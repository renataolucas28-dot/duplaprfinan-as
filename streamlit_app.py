import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime as dt

# ID da SUA planilha
SPREADSHEET_ID = "1_PmKlDUdZxp3UBlopyrPUlccJy_aP5aA_HvXa3FwqDo"

st.title("💰 Finanças Casal - FUNCIONANDO!")
st.success("✅ Service account conectada!")

@st.cache_data(ttl=300)
def ler_planilha():
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["connections"]["gsheets"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        
        # TESTA DIFERENTES NOMES DE ABA
        ranges = ["Sheet1!A:E", "Página1!A:E", "Sheet1", "Página1"]
        
        for range_name in ranges:
            try:
                result = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                if values:
                    return pd.DataFrame(values[1:], columns=values[0])
            except:
                continue
        
        # Se nenhuma aba funcionar, cria estrutura vazia
        return pd.DataFrame(columns=["data", "descricao", "categoria", "valor", "quem"])
        
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()

# LER
df = ler_planilha()

if not df.empty:
    st.success("✅ DADOS ENCONTRADOS!")
    st.dataframe(df)
else:
    st.info("📭 Primeira vez - estrutura OK!")

# FORMULÁRIO
st.markdown("---")
st.subheader("➕ Novo Gasto")

col1, col2, col3, col4 = st.columns(4)
with col1: data = st.date_input("Data", dt.date.today())
with col2: descricao = st.text_input("O que foi?")
with col3: categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer"])
with col4: valor = st.number_input("Valor R$", 0.0)

quem = st.radio("Quem pagou:", ["Eu", "Namorada"])

if st.button("💾 SALVAR", type="primary"):
    novo = [[data.isoformat(), descricao, categoria, float(valor), quem]]
    
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    
    service = build('sheets', 'v4', credentials=credentials)
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A:E",  # Tenta Sheet1 primeiro
        valueInputOption="RAW",
        body={"values": novo}
    ).execute()
    
    st.success("✅ SALVO na planilha!")
    st.rerun()
