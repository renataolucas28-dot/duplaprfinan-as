import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

SPREADSHEET_ID = "1_PmKlDUdZxp3UBlopyrPUlccJy_aP5aA_HvXa3FwqDo"
ABA_NOME = "Registro"

st.title("🔧 Atualizar colunas da planilha")

creds = service_account.Credentials.from_service_account_info(
    st.secrets["connections"]["gsheets"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
service = build('sheets', 'v4', credentials=creds)

# NOVO CABEÇALHO COM TODAS AS COLUNAS
NOVO_CABECALHO = [["data", "descricao", "categoria", "tipo", "valor", "quem"]]

if st.button("🔄 ATUALIZAR COLUNAS DA PLANILHA", type="primary"):
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_NOME}!A1:F1",
            valueInputOption="RAW",
            body={"values": NOVO_CABECALHO}
        ).execute()
        
        st.success("✅ Colunas atualizadas!")
        st.info("Colunas agora: data | descricao | categoria | tipo | valor | quem")
        st.warning("⚠️ Os dados antigos continuam, só a ordem mudou. Coluna 'tipo' foi adicionada na posição D.")
        
    except Exception as e:
        st.error(f"Erro: {e}")

# MOSTRA ESTADO ATUAL
st.markdown("---")
st.markdown("**Colunas atuais na planilha:**")
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=f"{ABA_NOME}!A1:F1"
).execute()
st.write(result.get('values', [["Sem cabeçalho"]]))
