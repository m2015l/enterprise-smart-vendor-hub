"""Body shop page placeholder."""
import streamlit as st
import pandas as pd
import os
from streamlit_chat import message

home_page = st.Page("pages/0_home.py", title="Home", icon="🏠")

st.page_link(home_page, label="Home")

st.title("Body Shop")

MOCK_DATA_DIR = os.getenv("MOCK_DATA_DIR", "dados_csv")
MOCK_BODY_SHOP = os.path.join(MOCK_DATA_DIR, "candidatos.csv")
if os.path.exists(MOCK_BODY_SHOP):
    df_bs = pd.read_csv(MOCK_BODY_SHOP)
    st.dataframe(df_bs, hide_index=True)