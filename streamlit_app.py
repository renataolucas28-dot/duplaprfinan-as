import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🧪 Teste de Conexão Google Sheets")

st.info("Testando conexão com a planilha...")

try:
    # Conecta usando os secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lê a planilha
    df = conn.read()
    
    if df is not None and len(df) > 0:
        st.success("✅ CONEXÃO FUNCIONANDO!")
        st.write("**Dados da planilha:**")
        st.dataframe(df)
        
        # Mostra info básica
        st.metric("Total de linhas", len(df))
        
    else:
        st.warning("📭 Planilha vazia ou sem dados")
        st.success("✅ Mas a conexão está funcionando!")
        
except Exception as e:
    st.error(f"❌ Erro na conexão: {str(e)}")
    st.info("Verifique se:")
    st.info("- Secrets estão salvos e app reiniciado")
    st.info("- Service account tem permissão Editor na planilha")
    st.info("- private_key foi colada certinha")

