import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime as dt

# ID da SUA planilha
SPREADSHEET_ID = "1_PmKlDUdZxp3UBlopyrPUlccJy_aP5aA_HvXa3FwqDo"

st.title("💰 Finanças Casal - Teste Completo")

@st.cache_data(ttl=300)
def ler_planilha():
    """Lê dados da planilha usando secrets"""
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["connections"]["gsheets"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Página1!A:E"
        ).execute()
        
        values = result.get('values', [])
        if values:
            return pd.DataFrame(values[1:], columns=values[0])
        return pd.DataFrame(columns=["data", "descricao", "categoria", "valor", "quem"])
        
    except Exception as e:
        st.error(f"Erro conexão: {e}")
        return pd.DataFrame()

# LER DADOS
df = ler_planilha()

if not df.empty:
    st.success("✅ PLANILHA CONECTADA!")
    st.dataframe(df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    col1.metric("Total lançamentos", len(df))
    col2.metric("Total gasto", df["valor"].sum() if "valor" in df.columns else 0)
else:
    st.info("📭 Planilha vazia - vamos criar estrutura!")

# FORMULÁRIO NOVO LANÇAMENTO
st.markdown("---")
st.subheader("➕ Novo Lançamento")

col1, col2, col3, col4 = st.columns(4)
with col1:
    data = st.date_input("Data", value=dt.date.today())
with col2:
    descricao = st.text_input("Descrição")
with col3:
    categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde"])
with col4:
    valor = st.number_input("Valor", min_value=0.0, step=0.01)

quem = st.selectbox("Quem pagou", ["Eu", "Namorada", "Nós"])

if st.button("💾 Salvar", type="primary"):
    novo_registro = [[
        data.isoformat(),
        descricao,
        categoria,
        valor,
        quem
    ]]
    
    try:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["connections"]["gsheets"],
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Página1!A:E",
            valueInputOption="RAW",
            body={"values": novo_registro}
        ).execute()
        
        st.success("✅ Salvo na planilha!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Erro salvando: {e}")

st.markdown("---")
st.caption("👩‍❤️‍👨 App de finanças para casal - pronto para usar!")
