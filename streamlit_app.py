import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🧪 Teste Google Sheets")

st.info("Conectando na planilha...")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
    
    if df is not None:
        st.success("✅ GOOGLE SHEETS CONECTADO!")
        st.dataframe(df)
        st.metric("Linhas", len(df))
    else:
        st.warning("📭 Planilha vazia, mas conexão OK!")
        
except Exception as e:
    st.error(f"❌ Erro: {e}")
    st.info("Verifique secrets + permissões da service account")

st.success("Teste concluído!")
