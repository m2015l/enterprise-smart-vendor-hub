"""Suppliers page."""
import streamlit as st
import pandas as pd
import os

from components.badges import badge_html

home_page = st.Page("pages/0_home.py", title="Home", icon="🏠")

MOCK_DATA_DIR = os.getenv("MOCK_DATA_DIR", "dados_csv")
MOCK_FORNECEDORES = os.path.join(MOCK_DATA_DIR, "fornecedores.csv")


def split_pipe(valor: str) -> list[str]:
    if not isinstance(valor, str) or not valor.strip():
        return []
    return [item.strip() for item in valor.split("|") if item.strip()]


st.page_link(home_page, label="Home")
st.title("Fornecedores")

if not os.path.exists(MOCK_FORNECEDORES):
    st.error(f"Arquivo não encontrado: {MOCK_FORNECEDORES}")
    st.stop()

df = pd.read_csv(MOCK_FORNECEDORES, sep=";")
df["lista_competencias"] = df["competencias"].apply(
    lambda v: [c.strip() for c in str(v).split(",")]
)

# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")

    todas_competencias = sorted({c for lista in df["lista_competencias"] for c in lista})
    filtro_competencias = st.multiselect("Competência", todas_competencias)

    filtro_status = st.multiselect(
        "Status de homologação", sorted(df["status_homologacao"].unique())
    )

    filtro_porte = st.multiselect("Porte", sorted(df["porte"].unique()))

df_filtrado = df.copy()

if filtro_competencias:
    df_filtrado = df_filtrado[
        df_filtrado["lista_competencias"].apply(
            lambda lista: any(c in lista for c in filtro_competencias)
        )
    ]
if filtro_status:
    df_filtrado = df_filtrado[df_filtrado["status_homologacao"].isin(filtro_status)]
if filtro_porte:
    df_filtrado = df_filtrado[df_filtrado["porte"].isin(filtro_porte)]

st.caption(f"{len(df_filtrado)} de {len(df)} fornecedores exibidos.")

# ---------------------------------------------------------------------------
# Tabela principal — clique numa linha para abrir o detalhe
# ---------------------------------------------------------------------------
colunas_tabela = [
    "nome", "cnpj", "lista_competencias", "porte",
    "status_homologacao", "gasto_anual_faixa", "ultima_interacao",
]

selecao = st.dataframe(
    df_filtrado[colunas_tabela],
    hide_index=True,
    use_container_width=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "nome": "Nome",
        "cnpj": "CNPJ",
        "lista_competencias": st.column_config.ListColumn("Competências"),
        "porte": "Porte",
        "status_homologacao": "Homologação",
        "gasto_anual_faixa": "Gasto anual",
        "ultima_interacao": st.column_config.DateColumn("Última interação"),
    },
)

# ---------------------------------------------------------------------------
# Detalhe do fornecedor selecionado
# ---------------------------------------------------------------------------
linhas_selecionadas = selecao.selection.rows if selecao and selecao.selection else []

if not linhas_selecionadas:
    st.info("Selecione um fornecedor na tabela para ver o detalhe completo.")
else:
    fornecedor = df_filtrado.iloc[linhas_selecionadas[0]]

    st.markdown("---")
    col_titulo, col_badges = st.columns([3, 2])
    with col_titulo:
        st.subheader(fornecedor["nome"])
        st.caption(f"CNPJ: {fornecedor['cnpj']} · Porte: {fornecedor['porte']}")
    with col_badges:
        st.markdown(
            badge_html("homologacao", fornecedor["status_homologacao"])
            + "&nbsp;&nbsp;"
            + badge_html("criticidade", fornecedor["criticidade"]),
            unsafe_allow_html=True,
        )

    col_a, col_b = st.columns(2)
    col_a.metric("Gasto anual", fornecedor["gasto_anual_faixa"])
    col_b.metric("Última interação", str(fornecedor["ultima_interacao"]))

    st.write(fornecedor["justificativa"])

    st.markdown("**Competências e evidências**")
    for item in split_pipe(fornecedor["evidencias"]):
        if ":" in item:
            competencia, evidencia = item.split(":", 1)
            st.markdown(f"- **{competencia.strip()}** — {evidencia.strip()}")
        else:
            st.markdown(f"- {item}")

    st.markdown("**Histórico de avaliações**")
    avaliacoes = split_pipe(fornecedor["historico_avaliacoes"])
    if avaliacoes:
        for item in avaliacoes:
            st.caption(f"🕘 {item}")
    else:
        st.caption("Sem avaliações registradas.")

    pontos_atencao = split_pipe(fornecedor["atencao"])
    if pontos_atencao:
        st.markdown("**Pontos de atenção**")
        for a in pontos_atencao:
            st.caption(f"⚠️ {a}")