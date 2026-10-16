"""Página de KPIs da plataforma."""
import os

import pandas as pd
import streamlit as st

# set_page_config precisa ser o PRIMEIRO comando Streamlit da página
st.set_page_config(page_title="KPIs da Plataforma", layout="wide")

home_page = st.Page("pages/0_home.py", title="Home",icon="🏠")
st.page_link(home_page, label="Home")

MOCK_DATA_DIR = os.getenv("MOCK_DATA_DIR", "dados_csv")
MOCK_KPI = os.path.join(MOCK_DATA_DIR, "kpis.csv")

# Explicação curta de cada KPI (aparece no ícone "?" do card)
DESCRICOES = {
    "cobertura_idf": "Avaliações registradas no último ano ÷ fornecedores ativos de tecnologia.",
    "confianca_media": "Média do nível de confiança de todas as recomendações do sistema.",
    "recomendacoes_incompletas": "Percentual de recomendações que precisaram de redistribuição de peso por falta de dado.",
    "exclusoes_restricao": "Fornecedores excluídos do ranking por restrição ou código eliminado.",
    "sourcing_dias": "Tempo médio de sourcing, em dias.",
    "hit_rate_5": "Percentual de vezes em que o fornecedor escolhido estava entre as 5 primeiras recomendações.",
    "taxa_uso": "Percentual de uso da plataforma.",
}


# ---------- Funções auxiliares ----------
def br(numero, casas=1):
    """Formata número no padrão brasileiro (1.234,5)."""
    texto = f"{numero:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar(valor, unidade):
    if unidade == "%":
        return f"{br(valor)}%"
    if unidade == "dias":
        return f"{br(valor)} dias"
    if unidade == "qtd":
        return br(valor, 0)
    return f"{br(valor, 2)} / 5"  # nota (1-5)


def unidade_delta(unidade):
    return {"%": "pp", "dias": "dias"}.get(unidade, "")


@st.cache_data
def carregar(caminho):
    df = pd.read_csv(caminho)
    df["mes_ref"] = pd.to_datetime(df["mes_ref"])
    return df


def card_kpi(df, kpi_id):
    dados = df[df["kpi_id"] == kpi_id].sort_values("mes_ref")
    atual, anterior = dados.iloc[-1], dados.iloc[-2]

    delta = atual["valor"] - anterior["valor"]
    un = unidade_delta(atual["unidade"])
    casas = 0 if atual["unidade"] == "qtd" else 1
    sem_meta = pd.isna(atual["meta"])

    if atual["direcao_melhora"] == "menor":
        cor = "inverse"  # queda = verde
    elif atual["direcao_melhora"] == "neutra":
        cor = "off"      # sem juízo de valor
    else:
        cor = "normal"

    st.metric(
        label=f"{atual['kpi']} · {atual['mes']}",
        value=formatar(atual["valor"], atual["unidade"]),
        delta=f"{delta:+.{casas}f} {un} vs {anterior['mes']}".replace(".", ","),
        delta_color=cor,
        help=DESCRICOES.get(kpi_id),
        border=True,
    )

    if sem_meta:
        st.caption("Indicador informativo, sem meta definida.")
    else:
        meta_txt = formatar(atual["meta"], atual["unidade"])
        if atual["atingiu_meta"] == "sim":
            st.caption(f"Meta: {meta_txt} · Meta atingida")
        else:
            falta = abs(atual["meta"] - atual["valor"])
            st.caption(f"Meta: {meta_txt} · Faltam {br(falta)} {un}".strip())


def grafico_kpi(df, kpi_id, tipo="linha"):
    dados = df[df["kpi_id"] == kpi_id].sort_values("mes_ref")
    ref = dados.iloc[-1]

    titulo = ref["kpi"]
    if ref["direcao_melhora"] == "menor":
        titulo += " (quanto menor, melhor)"

    tabela = dados[["mes_ref", "valor", "meta"]].rename(
        columns={"mes_ref": "Mês", "valor": "Realizado", "meta": "Meta"}
    )
    tem_meta = tabela["Meta"].notna().any()
    series = ["Realizado", "Meta"] if tem_meta else ["Realizado"]

    # formato longo: uma linha por (mês, série)
    longo = tabela.melt(
        id_vars="Mês", value_vars=series,
        var_name="Série", value_name="Valor",
    )

    with st.container(border=True):
        st.markdown(f"**{titulo}**")
        if tipo == "barra":
            st.bar_chart(longo[longo["Série"] == "Realizado"], x="Mês", y="Valor")
        else:
            st.line_chart(longo, x="Mês", y="Valor", color="Série")

        legenda = f"{dados.iloc[0]['mes']} a {ref['mes']} · unidade: {ref['unidade']}"
        if tem_meta:
            legenda += f" · meta: {br(ref['meta'])}"
        st.caption(legenda)


# ---------- Página ----------
st.title("KPIs da Plataforma")

if not os.path.exists(MOCK_KPI):
    st.error(f"Arquivo não encontrado: {MOCK_KPI}")
    st.stop()

df_KPI = carregar(MOCK_KPI)
primeiro_mes = df_KPI.loc[df_KPI["mes_ref"].idxmin(), "mes"]
ultimo_mes = df_KPI.loc[df_KPI["mes_ref"].idxmax(), "mes"]
n_meses = df_KPI["mes_ref"].nunique()

st.caption(
    f"Dados de **{primeiro_mes}** a **{ultimo_mes}** ({n_meses} meses). "
    f"Os cards mostram o último mês ({ultimo_mes}) e a variação em relação ao mês anterior."
)

# 1) Destaque
st.header("Em destaque")
destaque, resumo = st.columns([1, 2])
with destaque:
    card_kpi(df_KPI, "cobertura_idf")
with resumo:
    idf = df_KPI[df_KPI["kpi_id"] == "cobertura_idf"].sort_values("mes_ref").iloc[-1]
    st.markdown("**Cobertura de fornecedores avaliados**")
    st.progress(min(idf["valor"] / 100, 1.0), text=f"{br(idf['valor'])}% dos fornecedores ativos de tecnologia")
    st.caption(DESCRICOES["cobertura_idf"])

# 2) Qualidade das recomendações
st.header("Qualidade das recomendações")
c1, c2, c3 = st.columns(3)
with c1:
    card_kpi(df_KPI, "confianca_media")
with c2:
    card_kpi(df_KPI, "recomendacoes_incompletas")
with c3:
    card_kpi(df_KPI, "exclusoes_restricao")

# 3) Desempenho e adoção
st.header("Desempenho e adoção")
c1, c2, c3 = st.columns(3)
with c1:
    card_kpi(df_KPI, "sourcing_dias")
with c2:
    card_kpi(df_KPI, "hit_rate_5")
with c3:
    card_kpi(df_KPI, "taxa_uso")

# 4) Evolução mensal
st.header("Evolução mensal")
st.caption("Linha tracejada de meta indisponível no gráfico nativo: a meta aparece como uma segunda linha.")

aba1, aba2, aba3 = st.tabs(["Base de fornecedores", "Adoção da plataforma", "Eficiência e satisfação"])

with aba1:
    g1, g2 = st.columns(2)
    with g1:
        grafico_kpi(df_KPI, "pct_classificados")
    with g2:
        grafico_kpi(df_KPI, "pct_enriquecidos")

with aba2:
    g1, g2 = st.columns(2)
    with g1:
        grafico_kpi(df_KPI, "pct_demandas_plataforma")
    with g2:
        grafico_kpi(df_KPI, "talentos_optin", "barra")

with aba3:
    g1, g2 = st.columns(2)
    with g1:
        grafico_kpi(df_KPI, "mobilizacao_dias")
    with g2:
        grafico_kpi(df_KPI, "csat")