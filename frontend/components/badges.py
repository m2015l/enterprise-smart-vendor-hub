# componentes/badges.py
import streamlit as st

TONS = {
    "bom":      "#1F5F5B",
    "atencao":  "#93641C",
    "ruim":     "#A8452E",
    "neutro":   "#6B7280",
    "destaque": "#2B4C7E",   # positivo, só para Prioritário/Apto
}

# grupo -> valor -> (texto exibido, tom)
GRUPOS = {
    "confianca": {
        "alto":  ("Confiança alta",  "bom"),
        "medio": ("Confiança média", "atencao"),
        "baixo": ("Confiança baixa", "ruim"),
    },
    "criticidade": {
        "Crítico": ("Crítico", "ruim"),
        "Médio":   ("Médio",   "atencao"),
        "Baixo":   ("Baixo",   "bom"),
    },
    "homologacao": {
        "Homologado":     ("Homologado",     "bom"),
        "Em homologação": ("Em homologação", "atencao"),
        "Vencido":        ("Vencido",        "ruim"),
        "Não homologado": ("Não homologado", "neutro"),
    },
    "validacao": {
        "nao_validado": ("Não validado", "neutro"),
    },
    "prioridade": {
        "prioritario": ("Prioritário", "destaque"),
    },
}


def badge_html(grupo, valor):
    texto, tom = GRUPOS.get(grupo, {}).get(valor, (str(valor), "neutro"))
    return (
        f'<span style="background:{TONS[tom]};color:#fff;padding:2px 10px;'
        f'border-radius:999px;font-size:0.8rem;font-weight:600;'
        f'white-space:nowrap">{texto}</span>'
    )


def badge(grupo, valor):
    st.markdown(badge_html(grupo, valor), unsafe_allow_html=True)