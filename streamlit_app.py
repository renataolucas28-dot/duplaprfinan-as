import streamlit as st
import pandas as pd

st.title("✅ Pandas OK!")

# Testa pandas
dados = pd.DataFrame({
    "data": ["2026-02-18"],
    "descricao": ["Teste pandas"],
    "valor": [100.50]
})

st.success("Pandas instalado!")
st.dataframe(dados)
st.metric("Total", dados["valor"].sum())

st.info("✅ Pandas funcionando! Próximo: gsheets-connection")
