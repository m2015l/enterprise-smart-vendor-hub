"Ranking page placeholder"
import streamlit as st
import pandas as pd
import os
from streamlit_chat import message

home_page = st.Page("pages/0_home.py", title="Home", icon="🏠")

st.page_link(home_page, label="Home")

st.title("Ranking")

MOCK_DATA_DIR = os.getenv("MOCK_DATA_DIR", "dados_csv")
MOCK_RANK = os.path.join(MOCK_DATA_DIR, "ranking.csv")
if os.path.exists(MOCK_RANK):
    df_ra = pd.read_csv(MOCK_RANK)
    st.dataframe(df_ra, hide_index=True)