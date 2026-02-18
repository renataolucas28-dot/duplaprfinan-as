import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

st.title("🧪 Teste Google Sheets API Direto")

SPREADSHEET_ID = "1_PmKlDUdZxp3UBlopyrPUlccJy_aP5aA_HvXa3FwqDo"

try:
    # Pega credenciais dos secrets
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    
    service = build('sheets', 'v4', credentials=credentials)
    
    # Lê planilha
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="Página1!A:Z"
    ).execute()
    
    values = result.get('values', [])
    
    if values:
        df = pd.DataFrame(values[1:], columns=values[0])
        st.success("✅ CONECTADO!")
        st.dataframe(df)
    else:
        st.success("✅ Conectado! Planilha vazia")
        
except Exception as e:
    st.error(f"❌ {e}")
