"AI Enrichment Queue page placeholder"
import streamlit as st
import pandas as pd
import os
from streamlit_chat import message

home_page = st.Page("pages/0_home.py", title="Home", icon="🏠")

st.page_link(home_page, label="Home")

st.title("AI Enrichment Queue")

MOCK_DATA_DIR = os.getenv("MOCK_DATA_DIR", "dados_csv")
MOCK_RICH = os.path.join(MOCK_DATA_DIR, "enriquecimentos.csv")
if os.path.exists(MOCK_RICH):
    df_ri = pd.read_csv(MOCK_RICH)
    st.dataframe(df_ri, hide_index=True)