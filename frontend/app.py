"""Streamlit application entrypoint placeholder."""
import streamlit as st
import pandas as pd
import os
from streamlit_chat import message
home_page = st.Page("pages/0_home.py", title="Home", icon="🏠")
chat_page = st.Page("pages/1_chat.py", title="Chat-Bot", icon="👾")
suppliers_page = st.Page("pages/2_fornecedores.py", title="Suppliers", icon="🏭")
bodyshop_page = st.Page("pages/3_body_shop.py", title="Body Shop", icon="👨‍💼")
KPIS_page = st.Page("pages/4_kpis.py", title="KPIs", icon="📊")
rank_page = st.Page("pages/5_ranking.py", title="Rank", icon="🏅")
queue_page = st.Page("pages/6_fila_ai.py", title="AI queue", icon="✨")
login_page = st.Page("pages/7_login.py", title="Login", icon="🌐")

#if "email_form" not in st.session_state:
#    pages = [login_page]
#else:
    #user_type = st.session_state.email_form.get("type_of_user")
    #match user_type:
        #case "Administrador":
            #pages = [home_page,chat_page,suppliers_page,bodyshop_page,KPIS_page,rank_page,queue_page]
        #case "Executivo":
            #pages = [home_page,chat_page,KPIS_page,rank_page]
        #case "Operacional":
            #pages = [home_page,chat_page,suppliers_page,bodyshop_page,rank_page,queue_page]

pages = [home_page,chat_page,suppliers_page,bodyshop_page,KPIS_page,rank_page,queue_page]
pg = st.navigation(pages, position="hidden")
pg.run()



    
