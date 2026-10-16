import streamlit as st
import pandas as pd
import os
from streamlit_chat import message

MOCK_DATA_DIR = os.getenv("MOCK_DATA_DIR", "dados_csv")
FILE_LOGIN = os.path.join(MOCK_DATA_DIR, "login.csv")
@st.dialog("Sign in:",width="medium",dismissible=True, icon= None, on_dismiss="ignore")
def email_form():
    name = st.text_input("Username:")
    email = st.text_input("Email:")
    password = st.text_input("Password:", type="password")
    type_of_user = st.selectbox("Type of user", ["Executivo", "Operacional", "Administrador"])
    st.write("")
    if st.button("Submit"):
        df_login_completo = pd.read_csv(FILE_LOGIN)
        if not (df_login_completo['username'] == name).any() and not(df_login_completo['email'] == email).any():
            st.session_state.email_form = {"username": name, "email": email, "password": password, "type_of_user": type_of_user}
            if os.path.exists(FILE_LOGIN):
                df_login_novo = pd.DataFrame({'username':[name],'email': [email], 'password': [password], 'type_of_user': [type_of_user]})
                df_login_completo = pd.concat([df_login_completo,df_login_novo], ignore_index=True)
                df_login_completo.to_csv(FILE_LOGIN, index=False)
                st.rerun()
        else:
            st.badge("This username/email is already registered", color="red")
@st.dialog("Login:",width="medium",dismissible=True, icon= None, on_dismiss="ignore")
def login_form():
    name = st.text_input("Username:")
    password = st.text_input("Password:", type="password")
    if st.button("Submit"):
        df_login_completo = pd.read_csv(FILE_LOGIN)
        if (df_login_completo['username'] == name).any():
            indice = df_login_completo.index[df_login_completo['username'] == name].item()
            if str(df_login_completo.at[indice, 'password']).strip() == str(password).strip():
                st.session_state.email_form = {"username": name, 'email': str(df_login_completo.at[indice, 'email']).strip(), 'password': password, 'type_of_user': str(df_login_completo.at[indice, 'type_of_user']).strip() }
                st.rerun()
            else:
                st.badge("Wrong password", color="red")
        else:
            st.badge("The user does not exist", color="red")

st.title("Enterprise Vendor Hub — Login")
st.header("Corporate Procurement & Vendor Intelligence Platform")

st.subheader("Create your account")
if st.button("Sign in"):
    email_form()
st.badge("Already have an account?", color="green")
if st.button("Login"):
    login_form()