import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime as dt

SPREADSHEET_ID = "1_PmKlDUdZxp3UBlopyrPUlccJy_aP5aA_HvXa3FwqDo"
ABA_NOME = "Registro"

st.title("💰 Finanças Casal - PRONTO!")

# Credenciais
creds = service_account.Credentials.from_service_account_info(
    st.secrets["connections"]["gsheets"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
service = build('sheets', 'v4', credentials=creds)

# 1. CRIAR CABEÇALHO (se não existir)
try:
    # Verifica se tem dados
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A1:E1"
    ).execute()
    
    if not result.get('values'):
        # CRIA CABEÇALHO
        cabecalho = [["data", "descricao", "categoria", "valor", "quem"]]
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_NOME}!A1:E1",
            valueInputOption="RAW",
            body={"values": cabecalho}
        ).execute()
        st.success("✅ Cabeçalho criado!")
    
    # LÊ DADOS (pula linha 1)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A:E"
    ).execute()
    
    values = result.get('values', [])
    if len(values) > 1:  # Tem dados além do cabeçalho
        df = pd.DataFrame(values[1:], columns=values[0])
        st.success("✅ Dados carregados!")
        st.dataframe(df)
    else:
        st.info("📭 Sem lançamentos ainda")
        
except Exception as e:
    st.error(f"Erro: {e}")

# FORMULÁRIO
st.markdown("---")
st.subheader("➕ Novo Gasto")

col1, col2, col3, col4 = st.columns(4)
with col1: data = st.date_input("Data", dt.date.today())
with col2: descricao = st.text_input("O que foi?")
with col3: categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Conta fixa", "Lazer"])
with col4: valor = st.number_input("Valor R$", 0.0)

quem = st.radio("Quem pagou:", ["Eu", "Namorada"])

if st.button("💾 SALVAR NA PLANILHA", type="primary"):
    novo_registro = [[
        data.isoformat(),
        descricao or "Sem descrição",
        categoria,
        float(valor),
        quem
    ]]
    
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{ABA_NOME}!A:E",
        valueInputOption="RAW",
        body={"values": novo_registro}
    ).execute()
    
    st.balloons()
    st.success("✅ SALVO na aba 'Registro'!")
    st.rerun()

st.markdown("---")
st.caption("👩‍❤️‍👨 App pronto para vocês usarem!")
