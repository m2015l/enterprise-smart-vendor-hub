"""Página inicial do hub."""
import streamlit as st

# set_page_config precisa ser o PRIMEIRO comando Streamlit da página
st.set_page_config(page_title="Enterprise Vendor Hub", page_icon="🏠", layout="wide")

home_page = st.Page("pages/0_home.py", title="Página Inicial", icon="🏠")
chat_page = st.Page("pages/1_chat.py", title="Assistente de IA", icon="👾")
suppliers_page = st.Page("pages/2_fornecedores.py", title="Fornecedores", icon="🏭")
bodyshop_page = st.Page("pages/3_body_shop.py", title="Terceirizados", icon="👨‍💼")
KPIS_page = st.Page("pages/4_kpis.py", title="KPIs", icon="📊")
rank_page = st.Page("pages/5_ranking.py", title="Ranking do banco de talentos", icon="🏅")
queue_page = st.Page("pages/6_fila_ai.py", title="Fila de enriquecimento de IA", icon="✨")
login_page = st.Page("pages/7_login.py", title="Login", icon="🌐")

# Cada card: (página, título, descrição). Edite os textos à vontade.
SECOES = [
    (chat_page, "Assistente de IA", "Converse com o assistente para buscar e recomendar fornecedores."),
    (suppliers_page, "Fornecedores", "Consulte e filtre a base de fornecedores."),
    (bodyshop_page, "Terceirizados", "Acompanhe os talentos e as demandas de body shop."),
    (KPIS_page, "KPIs", "Veja os indicadores da plataforma, metas e evolução mensal."),
    (rank_page, "Ranking do Banco de Talentos", "Confira o ranking de fornecedores."),
    (queue_page, "Fila de Enriquecimento de IA", "Acompanhe a fila de enriquecimento de dados por IA."),
]

# ---------- Cabeçalho ----------
st.title("Bem-vindo ao Enterprise Vendor Hub")
st.subheader("Plataforma Corporativa de Inteligência e Gestão de Fornecedores")
st.caption("Escolha uma área abaixo para começar.")
st.page_link(home_page, label="Página Inicial")

st.divider()

# ---------- Grade de cards (3 por linha) ----------
POR_LINHA = 3
for i in range(0, len(SECOES), POR_LINHA):
    colunas = st.columns(POR_LINHA)
    for col, (pagina, titulo, descricao) in zip(colunas, SECOES[i:i + POR_LINHA]):
        with col:
            with st.container(border=True):
                st.markdown(f"#### {titulo}")
                st.write(descricao)
                st.page_link(pagina, label=f"Abrir {titulo}")