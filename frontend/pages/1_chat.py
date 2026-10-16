"""Chat page placeholder."""
import os
import streamlit as st
import string
import pandas as pd
import re

from components.badges import badge, GRUPOS, TONS

home_page = st.Page("pages/0_home.py", title="Home", icon="🏠")

MOCK_DATA_DIR = os.getenv("MOCK_DATA_DIR", "dados_csv")
MOCK_FORNECEDORES = os.path.join(MOCK_DATA_DIR, "fornecedores.csv")

df_fornecedores = pd.read_csv(MOCK_FORNECEDORES, sep=";")

st.page_link(home_page, label="Home")

st.title("Converse com nosso chat-bot, o x40!")


def limpar(texto: str) -> set[str]:
    sem_pontuacao = texto.lower().translate(str.maketrans("", "", string.punctuation))
    return set(sem_pontuacao.split())


def media_notas(texto):
    """Extrai as notas de 'Nota 9.0' etc. e devolve a média (0 se não houver avaliações)."""
    notas = [float(n.replace(",", ".")) for n in re.findall(r"Nota\s+(\d+(?:[.,]\d+)?)", str(texto))]
    return sum(notas) / len(notas) if notas else 0.0


def ranquear_fornecedores(prompt: str, df: pd.DataFrame, top_n: int = 3):
    palavras_input = limpar(prompt)

    # vocabulário de competências existentes na base
    vocabulario = set()
    for c in df["competencias"]:
        for comp in c.split(","):
            vocabulario |= limpar(comp.replace("/", " "))
    palavras_pedidas = palavras_input & vocabulario

    resultados = []

    for _, linha in df.iterrows():
        competencias = [c.strip() for c in linha["competencias"].split(",")]

        # bate por sobreposição de palavras, não por igualdade exata
        # ("Compliance/LGPD" -> {"compliance", "lgpd"})
        palavras_cobertas = set()
        competencias_batidas = []
        for comp in competencias:
            palavras_comp = limpar(comp.replace("/", " "))
            if palavras_comp & palavras_input:
                palavras_cobertas |= palavras_comp & palavras_pedidas
                competencias_batidas.append(comp)

        if not competencias_batidas:
            continue

        cobertura = len(palavras_cobertas) / len(palavras_pedidas) if palavras_pedidas else 0
        pontuacaocomp = cobertura * 10
        pontuacaohistorico = media_notas(linha["historico_avaliacoes"])
        pontuacaocusto = float(linha["nota_custos"])
        pontuacaodisp = float(linha["nota_disponibilidade"])
        pontuacaototal = (
            pontuacaocomp * 32.5
            + pontuacaohistorico * 27.5
            + pontuacaocusto * 17.5
            + pontuacaodisp * 22.5
        ) / 100  # resultado em 0–10
        
        if pontuacaototal >= 8:
            confianca = "alto"
        elif pontuacaototal >= 5:
            confianca = "medio"
        else:
            confianca = "baixo"

        atencao = [a for a in str(linha["atencao"]).split("|") if a and a != "nan"]

        resultados.append({
            "nome": linha["nome"],
            "competencias": competencias,
            "justificativa": linha["justificativa"],
            "historico": linha["historico"],
            "atencao": atencao,
            "confianca": confianca,
            "pontuacao": round(pontuacaototal, 2),
        })

    resultados.sort(key=lambda r: r["pontuacao"], reverse=True)
    return resultados[:top_n]


def renderizar_resposta(resultados: list[dict]):
    if not resultados:
        st.write("Não encontrei fornecedores aderentes a essa busca. Tenta descrever de outro jeito?")
        return

    n = len(resultados)
    st.markdown(
        f'<span style="font-size:16px;color:#6b7280;">'
        f"Verifiquei {n} fornecedor{'es' if n > 1 else ''} com aderência à sua busca!</span>",
        unsafe_allow_html=True,
    )

    for i, f in enumerate(resultados, start=1):
        cor = TONS[GRUPOS["confianca"][f["confianca"]][1]]

        st.markdown("---")
        col_rank, col_nome, col_pontuacao, col_badge = st.columns(
            [0.8, 4, 2.2, 2.6], vertical_alignment="center"
        )

        with col_rank:
            st.markdown(
                f'<span style="font-size:20px;font-weight:800;color:#9ca3af;">{i:02d}</span>',
                unsafe_allow_html=True,
            )

        with col_nome:
            st.markdown(
                f'<span style="font-size:17px;font-weight:700;">{f["nome"]}</span>',
                unsafe_allow_html=True,
            )

        with col_pontuacao:
            st.markdown(
                f'<span style="color:{cor};font-size:22px;font-weight:800;white-space:nowrap;">'
                f'{f["pontuacao"]:.1f}'
                f'<span style="color:#9ca3af;font-size:12px;font-weight:500;"> /10</span></span>',
                unsafe_allow_html=True,
            )

        with col_badge:
            badge("confianca", f["confianca"])

        # competências como etiquetas
        chips = "".join(
            f'<span style="background:#f3f4f6;color:#374151;border-radius:6px;'
            f'padding:2px 8px;margin:0 6px 4px 0;font-size:12px;display:inline-block;">{c}</span>'
            for c in f["competencias"]
        )
        st.markdown(chips, unsafe_allow_html=True)

        st.write(f["justificativa"])
        st.caption(f"🕘 {f['historico']}")

        for a in f["atencao"]:
            st.caption(f"⚠️ {a}")


if "mensagens_salvas" not in st.session_state:
    st.session_state.mensagens_salvas = []
    with st.chat_message("assistant"):
        st.write("Olá! O que você está procurando?")

for msg in st.session_state.mensagens_salvas:
    with st.chat_message(msg["perfil"]):
        if msg["perfil"] == "assistant" and isinstance(msg["texto"], list):
            renderizar_resposta(msg["texto"])
        else:
            st.write(msg["texto"])

if prompt := st.chat_input("Digite algo..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.mensagens_salvas.append({"perfil": "user", "texto": prompt})

    resultados = ranquear_fornecedores(prompt, df_fornecedores)

    with st.chat_message("assistant"):
        renderizar_resposta(resultados)
    st.session_state.mensagens_salvas.append({"perfil": "assistant", "texto": resultados})

    st.rerun()