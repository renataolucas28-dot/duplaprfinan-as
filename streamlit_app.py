import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime as dt

st.title("🧪 Teste Completo - Finanças Casal")
st.markdown("---")

st.info("🔄 Testando conexão com Google Sheets...")

try:
    # Conecta com a planilha
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lê dados existentes
    df = conn.read()
    
    if df is not None and len(df) > 0:
        st.success("✅ CONEXÃO FUNCIONANDO!")
        st.write("**Dados atuais da planilha:**")
        st.dataframe(df, use_container_width=True)
        
        # Métricas básicas
        col1, col2 = st.columns(2)
        col1.metric("Total linhas", len(df))
        col2.metric("Última data", df.iloc[-1].get("data", "N/A") if "data" in df.columns else "N/A")
        
    else:
        st.success("✅ Conexão OK! Planilha vazia ou sem dados")
        st.info("Vamos criar a estrutura agora...")
        df = pd.DataFrame(columns=["data", "descricao", "categoria", "valor", "quem"])
    
    st.markdown("---")
    
    # Teste de escrita: nova linha
    with st.expander("📝 Testar lançamento novo"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            data_teste = st.date_input("Data", value=dt.date.today())
        with col2:
            desc = st.text_input("Descrição", "Teste do app")
        with col3:
            cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Conta fixa"])
        with col4:
            valor = st.number_input("Valor", value=0.0, step=0.01)
        
        if st.button("💾 Salvar teste", type="primary"):
            nova_linha = pd.DataFrame([{
                "data": data_teste.isoformat(),
                "descricao": desc,
                "categoria": cat,
                "valor": valor,
                "quem": "Teste"
            }])
            
            conn.update(worksheet="Página1", data=nova_linha, append=True)
            st.success("✅ Lançamento salvo!")
            st.rerun()
    
    st.markdown("---")
    st.success("🎉 TESTE CONCLUÍDO - Tudo funcionando!")
    
except Exception as e:
    st.error(f"❌ Erro: {str(e)}")
    st.info("**Possíveis causas:**")
    st.info("• requirements.txt não tem streamlit-gsheets-connection")
    st.info("• Secrets não salvos ou app não reiniciado")
    st.info("• Service account sem permissão Editor na planilha")
    st.info("• private_key colada errada (falta \n)")
