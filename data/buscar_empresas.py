"""
==========================================================
Buscador de Empresas Semelhantes por CNPJ
==========================================================
Este programa:
1. Acessa automaticamente o site dados.gov.br
2. Clica em "Inscrições no CNPJ" para obter o link da Receita Federal
3. Usa a API WebDAV do Nextcloud para listar a pasta mais recente
4. Baixa todos os arquivos Estabelecimentos*.zip
5. Extrai os CSVs e busca os CNAEs das empresas fornecidas
6. Filtra todas as empresas com CNAEs semelhantes
7. Gera o arquivo saida.csv com os resultados
8. Limpa todos os arquivos temporários (zip e csv)

Requisitos:
    pip install pandas selenium requests
"""
import os
import re
import sys
import time
import zipfile
import urllib.parse
from xml.etree import ElementTree

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# ============================================================
# CONFIGURAÇÕES DE AMBIENTE
# ============================================================

DADOS_GOV_CNPJ_URL = os.getenv(
    "DADOS_GOV_CNPJ_URL",
    "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj",
)
RECEITA_WEBDAV_BASE_URL = os.getenv(
    "RECEITA_WEBDAV_BASE_URL",
    "https://arquivos.receitafederal.gov.br",
)
RECEITA_SHARE_TOKEN = os.getenv("RECEITA_SHARE_TOKEN", "")
CNPJ_DATA_DIR = os.getenv("CNPJ_DATA_DIR", "cnpj_dados")
CNPJ_OUTPUT_CSV = os.getenv("CNPJ_OUTPUT_CSV", "saida.csv")


# ============================================================
# UTILITÁRIOS
# ============================================================

def limpar_cnpj(cnpj: str) -> str:
    """Remove pontos, barras, traços de um CNPJ. Retorna apenas dígitos."""
    return re.sub(r'[^0-9]', '', cnpj)


def setup_driver():
    """Configura e retorna uma instância do Chrome via Selenium."""
    options = Options()
    if os.getenv("SELENIUM_HEADLESS", "false").lower() == "true":
        options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        print(f"[ERRO] Falha ao iniciar o Chrome: {e}")
        print("Certifique-se de que o Google Chrome está instalado e atualizado.")
        sys.exit(1)


# ============================================================
# ETAPA 1 — OBTER O TOKEN DE COMPARTILHAMENTO DA RECEITA
# ============================================================

def obter_token_receita() -> str:
    """
    Acessa dados.gov.br via Selenium, localiza o recurso
    "Inscrições no CNPJ" e extrai o token do share do Nextcloud.
    Se RECEITA_SHARE_TOKEN estiver definido no ambiente, retorna-o diretamente.
    """
    if RECEITA_SHARE_TOKEN:
        print("\n[1/6] Utilizando RECEITA_SHARE_TOKEN definido via variável de ambiente.")
        return RECEITA_SHARE_TOKEN

    print("\n[1/6] Acessando dados.gov.br para obter o link da Receita Federal...")
    driver = setup_driver()

    try:
        driver.get(DADOS_GOV_CNPJ_URL)
        time.sleep(10)  # Aguarda Vue.js renderizar completamente

        # Localiza todos os blocos de recurso
        blocos = driver.find_elements(By.CSS_SELECTOR, "div.row.flex.mb-5")

        for bloco in blocos:
            h4s = bloco.find_elements(By.TAG_NAME, "h4")
            if not h4s:
                continue
            titulo = h4s[0].get_attribute("innerText") or ""
            titulo = titulo.strip()

            if "Inscri" in titulo and "CNPJ" in titulo:
                print(f"    Recurso encontrado: '{titulo}'")
                btn = bloco.find_element(By.ID, "btnDownloadUrl")

                # Salva handles antes do clique
                handles_antes = set(driver.window_handles)
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(5)

                # Verifica se abriu nova aba
                handles_depois = set(driver.window_handles)
                novas = handles_depois - handles_antes
                if novas:
                    driver.switch_to.window(list(novas)[0])

                url_receita = driver.current_url
                print(f"    URL da Receita Federal: {url_receita}")

                # Extrair o token do share
                match = re.search(r'/s/([A-Za-z0-9]+)', url_receita)
                if match:
                    token = match.group(1)
                    print(f"    Token do compartilhamento obtido com sucesso.")
                    return token

                print("[ERRO] Não foi possível extrair o token da URL.")
                sys.exit(1)

        print("[ERRO] Recurso 'Inscrições no CNPJ' não encontrado na página.")
        sys.exit(1)

    finally:
        driver.quit()


# ============================================================
# ETAPA 2 — LISTAR PASTAS E ARQUIVOS VIA WEBDAV
# ============================================================

def listar_via_webdav(token: str, caminho: str = "/") -> list:
    """
    Usa a API WebDAV pública do Nextcloud para listar o conteúdo
    de um diretório. Retorna lista de dicts com 'nome' e 'tipo'.
    Inclui retentativas automáticas contra queda de conexão.
    """
    base = RECEITA_WEBDAV_BASE_URL
    url = f"{base}/public.php/webdav{caminho}"
    headers = {"Depth": "1"}
    auth = (token, "")

    tentativas = [15, 30, 60, 120, 240]
    resp = None
    for i in range(len(tentativas) + 1):
        try:
            resp = requests.request("PROPFIND", url, headers=headers,
                                    auth=auth, timeout=60)
            if resp.status_code != 207:
                print(f"[ERRO] WebDAV retornou status {resp.status_code}")
                return []
            break  # Sucesso
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                ConnectionResetError) as e:
            if i < len(tentativas):
                espera = tentativas[i]
                print(f"    [AVISO] Conexão WebDAV falhou: {type(e).__name__}")
                print(f"    Aguardando {espera}s antes de tentar novamente...")
                time.sleep(espera)
            else:
                print(f"[ERRO] WebDAV falhou após todas as tentativas: {e}")
                return []

    if resp is None:
        return []

    root = ElementTree.fromstring(resp.content)
    ns = {"d": "DAV:"}
    itens = []

    for r in root.findall(".//d:response", ns):
        href_elem = r.find("d:href", ns)
        if href_elem is None or href_elem.text is None:
            continue
        href = href_elem.text
        nome = urllib.parse.unquote(href.rstrip("/").split("/")[-1])
        eh_dir = r.find(".//d:resourcetype/d:collection", ns) is not None

        # Pula o item que é o próprio diretório atual
        if nome and href.rstrip("/") != f"/public.php/webdav{caminho}".rstrip("/"):
            itens.append({"nome": nome, "tipo": "dir" if eh_dir else "file"})

    return itens


def obter_links_download(token: str) -> tuple:
    """
    Lista as pastas de data no Nextcloud, entra na mais recente e
    retorna (links, token). links é uma lista de tuplas (nome, url).
    Retorna ([], token) em caso de erro.
    """
    print("\n[2/6] Consultando o servidor da Receita Federal via WebDAV...")
    itens_raiz = listar_via_webdav(token, "/")

    pastas_data = sorted(
        [i["nome"] for i in itens_raiz if i["tipo"] == "dir" and re.match(r'^\d{4}-\d{2}$', i["nome"])]
    )

    if not pastas_data:
        print("[ERRO] Nenhuma pasta de data encontrada no servidor.")
        return [], token

    pasta_recente = pastas_data[-1]
    print(f"    Pasta mais recente: {pasta_recente}")
    print(f"    Total de pastas de data: {len(pastas_data)}")

    # Listar arquivos dentro da pasta mais recente
    itens_pasta = listar_via_webdav(token, f"/{pasta_recente}/")
    arquivos_estab = sorted(
        [i["nome"] for i in itens_pasta if i["tipo"] == "file" and "estabelecimento" in i["nome"].lower()]
    )

    print(f"    Arquivos Estabelecimentos encontrados: {len(arquivos_estab)}")

    base = RECEITA_WEBDAV_BASE_URL
    links = []
    for arq in arquivos_estab:
        # Usar WebDAV direto (funciona; a URL de share retorna body vazio)
        url = f"{base}/public.php/webdav/{pasta_recente}/{arq}"
        links.append((arq, url))

    return links, token


# ============================================================
# ETAPA 3 — DOWNLOAD DOS ARQUIVOS
# ============================================================

MAX_TENTATIVAS = 5
PAUSA_ENTRE_ARQUIVOS = 10   # segundos de espera entre downloads
PAUSA_ENTRE_TENTATIVAS = [15, 30, 60, 120, 240]  # backoff progressivo


def _baixar_um_arquivo(nome: str, url: str, caminho: str, auth: tuple) -> bool:
    """
    Baixa um único arquivo com suporte a:
    - Retomada de download parcial (HTTP Range)
    - Retentativas automáticas com backoff progressivo
    Retorna True se o download foi concluído com sucesso.
    """
    caminho_parcial = caminho + ".part"

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            # Verificar se existe download parcial para retomar
            bytes_ja_baixados = 0
            if os.path.exists(caminho_parcial):
                bytes_ja_baixados = os.path.getsize(caminho_parcial)

            headers = {}
            if bytes_ja_baixados > 0:
                headers["Range"] = f"bytes={bytes_ja_baixados}-"
                print(f"        Retomando de {bytes_ja_baixados / (1024**2):.1f} MB...")

            with requests.get(url, stream=True, timeout=(30, 600),
                              headers=headers, auth=auth) as r:
                # Se o servidor aceita Range, retorna 206; senão, 200
                if r.status_code == 416:
                    # Range insatisfatório — arquivo já completo ou corrompido
                    if os.path.exists(caminho_parcial):
                        os.remove(caminho_parcial)
                    bytes_ja_baixados = 0
                    continue

                r.raise_for_status()

                # Se recebemos 200 (não 206), o servidor não suporta Range
                # e está enviando o arquivo inteiro do zero
                modo = 'ab' if r.status_code == 206 else 'wb'

                with open(caminho_parcial, modo) as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1 MB por vez
                        f.write(chunk)

            # Download completo — renomear .part para .zip
            if os.path.exists(caminho):
                os.remove(caminho)
            os.rename(caminho_parcial, caminho)
            return True

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError,
                ConnectionResetError) as e:

            espera = PAUSA_ENTRE_TENTATIVAS[min(tentativa - 1, len(PAUSA_ENTRE_TENTATIVAS) - 1)]
            print(f"        [AVISO] Tentativa {tentativa}/{MAX_TENTATIVAS} falhou: {type(e).__name__}")
            print(f"        Aguardando {espera}s antes de tentar novamente...")
            time.sleep(espera)

    print(f"    [ERRO] Falha ao baixar {nome} após {MAX_TENTATIVAS} tentativas.")
    return False


def baixar_arquivos(links: list, token: str) -> list:
    """Baixa os arquivos .zip para a pasta configurada em CNPJ_DATA_DIR. Retorna caminhos locais."""
    print(f"\n[3/6] Iniciando download de {len(links)} arquivos...")
    print(f"    (Pausa de {PAUSA_ENTRE_ARQUIVOS}s entre downloads para evitar bloqueio)")
    os.makedirs(CNPJ_DATA_DIR, exist_ok=True)

    auth = (token, "")  # Autenticação WebDAV: token como usuário, senha vazia
    caminhos = []
    for i, (nome, url) in enumerate(links, 1):
        caminho = os.path.join(CNPJ_DATA_DIR, nome)
        if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
            print(f"    [{i}/{len(links)}] {nome} já existe. Pulando.")
            caminhos.append(caminho)
        else:
            # Apagar arquivo vazio de tentativas anteriores
            if os.path.exists(caminho) and os.path.getsize(caminho) == 0:
                os.remove(caminho)
            print(f"    [{i}/{len(links)}] Baixando {nome}...")
            sucesso = _baixar_um_arquivo(nome, url, caminho, auth)
            if not sucesso:
                print(f"    [{i}/{len(links)}] {nome} não pôde ser baixado. Continuando...")
                continue  # NÃO adiciona ao caminhos — arquivo não existe
            print(f"    [{i}/{len(links)}] {nome} concluído!")
            caminhos.append(caminho)

            # Pausa entre downloads para não sobrecarregar o servidor
            if i < len(links):
                print(f"    Aguardando {PAUSA_ENTRE_ARQUIVOS}s antes do próximo download...")
                time.sleep(PAUSA_ENTRE_ARQUIVOS)

    return caminhos


# ============================================================
# ETAPA 4 — EXTRAIR OS ARQUIVOS ZIP
# ============================================================

def extrair_arquivos(arquivos_zip: list) -> list:
    """Extrai todos os ZIPs e apaga os originais. Retorna lista de CSVs."""
    print(f"\n[4/6] Extraindo {len(arquivos_zip)} arquivos ZIP...")
    csvs = []

    for zp in arquivos_zip:
        if not os.path.exists(zp):
            print(f"    [AVISO] Arquivo {os.path.basename(zp)} não encontrado. Pulando.")
            continue
        print(f"    Extraindo {os.path.basename(zp)}...")
        try:
            with zipfile.ZipFile(zp, 'r') as z:
                nomes = z.namelist()
                z.extractall(CNPJ_DATA_DIR)
                for n in nomes:
                    csvs.append(os.path.join(CNPJ_DATA_DIR, n))
            os.remove(zp)
            print(f"    ZIP {os.path.basename(zp)} removido para liberar espaço.")
        except Exception as e:
            print(f"    [AVISO] Erro ao extrair {zp}: {e}")

    return csvs


# ============================================================
# ETAPA 5 — BUSCAR CNAES DOS CNPJS FORNECIDOS
# ============================================================

def buscar_cnaes(cnpjs_alvo: list, arquivos_csv: list) -> set:
    """
    Lê os CSVs em chunks e encontra os CNAEs (principal + secundário)
    das empresas cujos CNPJs foram fornecidos.
    """
    print(f"\n[5/6] Buscando CNAEs dos {len(cnpjs_alvo)} CNPJs fornecidos...")
    colunas_usar = [0, 1, 2, 11, 12]
    cnaes = set()
    restantes = set(cnpjs_alvo)

    for arquivo in arquivos_csv:
        if not restantes:
            break
        if not os.path.exists(arquivo):
            continue
        print(f"    Lendo {os.path.basename(arquivo)}...")

        try:
            chunks = pd.read_csv(
                arquivo, sep=';', encoding='latin1', header=None,
                usecols=colunas_usar, chunksize=500_000, dtype=str,
                on_bad_lines='skip'
            )
        except Exception as e:
            print(f"    [AVISO] Erro ao ler {arquivo}: {e}")
            continue

        for chunk in chunks:
            # Preservar zeros à esquerda: preencher NaN com string vazia
            chunk[0] = chunk[0].fillna('')
            chunk[1] = chunk[1].fillna('')
            chunk[2] = chunk[2].fillna('')

            # Montar CNPJ: strip para remover espaços que possam existir
            chunk['CNPJ'] = chunk[0].str.strip() + chunk[1].str.strip() + chunk[2].str.strip()

            encontrados = chunk[chunk['CNPJ'].isin(restantes)]
            for _, row in encontrados.iterrows():
                if pd.notna(row[11]):
                    cnaes.add(str(row[11]).strip())
                if pd.notna(row[12]):
                    for s in str(row[12]).split(','):
                        s = s.strip()
                        if s:
                            cnaes.add(s)
                restantes.discard(row['CNPJ'])
                print(f"    ✔ CNPJ {row['CNPJ']} encontrado! CNAEs registrados.")

            if not restantes:
                break

    if restantes:
        print(f"    [AVISO] {len(restantes)} CNPJ(s) não encontrado(s) no dataset.")

    return cnaes


# ============================================================
# ETAPA 6 — BUSCAR EMPRESAS SEMELHANTES E GERAR saida.csv
# ============================================================

def buscar_similares(cnaes_alvo: set, arquivos_csv: list, saida: str = CNPJ_OUTPUT_CSV):
    """
    Lê todos os CSVs em chunks, filtra empresas com CNAEs compatíveis
    e salva em saida.csv. Apaga os CSVs originais ao terminar cada um.
    """
    # Apagar saida.csv anterior para não acumular resultados de execuções passadas
    if os.path.exists(saida):
        os.remove(saida)
        print(f"    Arquivo {saida} anterior removido.")

    print(f"\n[6/6] Buscando empresas semelhantes (CNAEs: {cnaes_alvo})...")

    nomes_colunas = [
        "CNPJ_BASE", "CNPJ_ORDEM", "CNPJ_DV",
        "IDENTIFICADOR_MATRIZ_FILIAL", "NOME_FANTASIA",
        "SITUACAO_CADASTRAL", "DATA_SITUACAO_CADASTRAL",
        "MOTIVO_SITUACAO_CADASTRAL", "NOME_CIDADE_EXTERIOR", "PAIS",
        "DATA_INICIO_ATIVIDADE", "CNAE_FISCAL_PRINCIPAL",
        "CNAE_FISCAL_SECUNDARIA", "TIPO_LOGRADOURO", "LOGRADOURO",
        "NUMERO", "COMPLEMENTO", "BAIRRO", "CEP", "UF", "MUNICIPIO",
        "DDD_1", "TELEFONE_1", "DDD_2", "TELEFONE_2",
        "DDD_FAX", "FAX", "CORREIO_ELETRONICO",
        "SITUACAO_ESPECIAL", "DATA_SITUACAO_ESPECIAL"
    ]

    # Colunas relevantes para análise de porte/tamanho da empresa
    colunas_saida = [
        "CNPJ_COMPLETO",
        "IDENTIFICADOR_MATRIZ_FILIAL",   # 1=Matriz, 2=Filial (indica porte)
        "NOME_FANTASIA",
        "SITUACAO_CADASTRAL",            # 02=Ativa, 08=Baixada, etc.
        "DATA_INICIO_ATIVIDADE",         # Idade da empresa
        "CNAE_FISCAL_PRINCIPAL",
        "CNAE_FISCAL_SECUNDARIA",
        "UF", "MUNICIPIO", "BAIRRO", "CEP",
        "CORREIO_ELETRONICO",
        "DDD_1", "TELEFONE_1",
    ]

    primeiro = True
    total = 0

    for arquivo in arquivos_csv:
        if not os.path.exists(arquivo):
            print(f"    [AVISO] Arquivo {os.path.basename(arquivo)} não encontrado. Pulando.")
            continue
        print(f"    Filtrando em {os.path.basename(arquivo)}...")

        try:
            chunks = pd.read_csv(
                arquivo, sep=';', encoding='latin1', header=None,
                names=nomes_colunas, chunksize=500_000, dtype=str,
                on_bad_lines='skip'
            )
        except Exception as e:
            print(f"    [AVISO] Erro ao ler {arquivo}: {e}")
            continue

        for chunk in chunks:
            # Strip para remover espaços que o CSV possa conter
            chunk['CNAE_FISCAL_PRINCIPAL'] = chunk['CNAE_FISCAL_PRINCIPAL'].fillna('').str.strip()
            chunk['CNAE_FISCAL_SECUNDARIA'] = chunk['CNAE_FISCAL_SECUNDARIA'].fillna('').str.strip()

            mask_p = chunk['CNAE_FISCAL_PRINCIPAL'].isin(cnaes_alvo)
            mask_s = chunk['CNAE_FISCAL_SECUNDARIA'].apply(
                lambda x: any(s.strip() in cnaes_alvo for s in str(x).split(',') if s.strip())
            )

            sim = chunk[mask_p | mask_s].copy()
            if sim.empty:
                continue

            sim['CNPJ_BASE'] = sim['CNPJ_BASE'].fillna('')
            sim['CNPJ_ORDEM'] = sim['CNPJ_ORDEM'].fillna('')
            sim['CNPJ_DV'] = sim['CNPJ_DV'].fillna('')
            sim['CNPJ_COMPLETO'] = (
                sim['CNPJ_BASE'].str.strip()
                + sim['CNPJ_ORDEM'].str.strip()
                + sim['CNPJ_DV'].str.strip()
            )

            total += len(sim)
            sim[colunas_saida].to_csv(
                saida, mode='a', index=False,
                header=primeiro, sep=';', encoding='utf-8-sig'
            )
            primeiro = False

        # Apagar CSV original para liberar espaço
        try:
            os.remove(arquivo)
            print(f"    Apagando {os.path.basename(arquivo)} para liberar espaço...")
        except OSError:
            pass

    print(f"\n{'='*50}")
    print(f"CONCLUÍDO! {total} empresas semelhantes encontradas.")
    print(f"Resultado salvo em: {os.path.abspath(saida)}")
    print(f"{'='*50}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 55)
    print("  BUSCADOR DE EMPRESAS SEMELHANTES POR CNPJ")
    print("  Fonte: Receita Federal (dados.gov.br)")
    print("=" * 55)

    # ---- Entrada do usuário ----
    try:
        n = int(input("\nQuantos CNPJs você deseja fornecer? "))
    except ValueError:
        print("Número inválido. Encerrando.")
        return

    cnpjs = []
    print("Digite os CNPJs (aceita pontuação, ex: 00.000.000/0001-00):\n")
    for i in range(n):
        raw = input(f"  CNPJ {i + 1}: ")
        limpo = limpar_cnpj(raw)
        if len(limpo) == 14:
            cnpjs.append(limpo)
        else:
            print(f"  [AVISO] CNPJ '{raw}' é inválido (não tem 14 dígitos). Ignorado.")

    if not cnpjs:
        print("\nNenhum CNPJ válido fornecido. Encerrando.")
        return

    print(f"\nCNPJs válidos: {cnpjs}")
    print("O processo agora é automático. Aguarde...\n")

    # ---- Pipeline automático ----
    token = obter_token_receita()
    links, token = obter_links_download(token)

    if not links:
        print("Nenhum arquivo Estabelecimentos encontrado. Encerrando.")
        return

    zips = baixar_arquivos(links, token)
    csvs = extrair_arquivos(zips)

    if not csvs:
        print("Nenhum CSV extraído. Encerrando.")
        return

    cnaes = buscar_cnaes(cnpjs, csvs)
    if not cnaes:
        print("Nenhum CNAE encontrado para os CNPJs informados.")
        for c in csvs:
            if os.path.exists(c):
                os.remove(c)
        return

    print(f"\nCNAEs mapeados: {cnaes}")
    buscar_similares(cnaes, csvs)


if __name__ == "__main__":
    main()
