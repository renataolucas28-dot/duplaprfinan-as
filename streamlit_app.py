import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime as dt

# ─────────────────────────────────────────
# CONFIGURAÇÃO GERAL
# ─────────────────────────────────────────
st.set_page_config(
    page_title="💑 Finanças Patrick & Renata",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

SPREADSHEET_ID = "1_PmKlDUdZxp3UBlopyrPUlccJy_aP5aA_HvXa3FwqDo"
ABA_NOME = "Registro"
COLUNAS = ["data", "descricao", "categoria", "tipo", "valor", "quem"]
CATEGORIAS = [
    "Mercado", "Contas Fixas", "Cartão de Crédito",
    "Lanche", "Lazer", "Gasolina", "Reparos",
    "Investimentos", "Saúde", "Educação", "Outros"
]
PESSOAS = ["Patrick", "Renata", "Nós dois"]

# ─────────────────────────────────────────
# CSS MOBILE FIRST
# ─────────────────────────────────────────
st.markdown("""
    <style>
        /* Fonte e fundo geral */
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }

        /* Botão primário maior para dedo */
        .stButton > button {
            width: 100%;
            padding: 0.8rem;
            font-size: 1.1rem;
            border-radius: 12px;
            font-weight: bold;
        }

        /* Inputs maiores */
        input, select, textarea {
            font-size: 1rem !important;
        }

        /* Card de métrica */
        .card {
            background: linear-gradient(135deg, #1e3a5f, #2e6da4);
            border-radius: 16px;
            padding: 16px;
            text-align: center;
            color: white;
            margin-bottom: 12px;
        }
        .card h3 { margin: 0; font-size: 0.9rem; opacity: 0.85; }
        .card h1 { margin: 4px 0; font-size: 1.8rem; }

        /* Card verde entradas */
        .card-verde {
            background: linear-gradient(135deg, #1a5c38, #27ae60);
            border-radius: 16px;
            padding: 16px;
            text-align: center;
            color: white;
            margin-bottom: 12px;
        }
        .card-verde h3 { margin: 0; font-size: 0.9rem; opacity: 0.85; }
        .card-verde h1 { margin: 4px 0; font-size: 1.8rem; }

        /* Card vermelho saídas */
        .card-vermelho {
            background: linear-gradient(135deg, #7b1a1a, #e74c3c);
            border-radius: 16px;
            padding: 16px;
            text-align: center;
            color: white;
            margin-bottom: 12px;
        }
        .card-vermelho h3 { margin: 0; font-size: 0.9rem; opacity: 0.85; }
        .card-vermelho h1 { margin: 4px 0; font-size: 1.8rem; }

        /* Tabs mais grossas */
        .stTabs [data-baseweb="tab"] {
            font-size: 1rem;
            padding: 10px 20px;
            font-weight: bold;
        }
        
        /* Esconde menu hamburger desnecessário */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CONEXÃO GOOGLE SHEETS
# ─────────────────────────────────────────
@st.cache_resource
def get_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build('sheets', 'v4', credentials=creds)

service = get_service()

def garantir_cabecalho():
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{ABA_NOME}!A1:F1"
    ).execute()
    if not result.get('values'):
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_NOME}!A1:F1",
            valueInputOption="RAW",
            body={"values": [COLUNAS]}
        ).execute()

@st.cache_data(ttl=60)
def ler_dados():
    garantir_cabecalho()
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{ABA_NOME}!A:F"
    ).execute()
    values = result.get('values', [])
    if len(values) > 1:
        df = pd.DataFrame(values[1:], columns=values[0])
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df
    return pd.DataFrame(columns=COLUNAS)

def salvar_registro(data, descricao, categoria, tipo, valor, quem):
    novo = [[
        data.isoformat(),
        descricao,
        categoria,
        tipo,
        float(valor),
        quem
    ]]
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{ABA_NOME}!A:F",
        valueInputOption="RAW",
        body={"values": novo}
    ).execute()
    st.cache_data.clear()

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("## 💑 Patrick & Renata")
st.markdown("##### 💰 Controle Financeiro do Casal")
st.markdown("---")

# ─────────────────────────────────────────
# ABAS PRINCIPAIS
# ─────────────────────────────────────────
aba1, aba2 = st.tabs(["📝 Lançamentos", "📊 Análises"])

# ══════════════════════════════════════════
# ABA 1 - LANÇAMENTOS
# ══════════════════════════════════════════
with aba1:

    st.markdown("### ➕ Novo Lançamento")

    tipo = st.radio(
        "Tipo:",
        ["📈 Entrada", "📉 Saída"],
        horizontal=True
    )
    tipo_limpo = "Entrada" if "Entrada" in tipo else "Saída"

    data = st.date_input("📅 Data", value=dt.date.today())
    descricao = st.text_input("📝 Descrição", placeholder="Ex: Compra no mercado")

    if tipo_limpo == "Saída":
        categoria = st.selectbox("🏷️ Categoria", CATEGORIAS)
    else:
        categoria = st.selectbox("🏷️ Categoria", ["Salário", "Freelance", "Investimento", "Outros"])

    valor = st.number_input("💵 Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    quem = st.selectbox("👤 Quem?", PESSOAS)

    if st.button("💾 SALVAR LANÇAMENTO", type="primary"):
        if valor == 0:
            st.warning("⚠️ Coloque um valor maior que zero!")
        elif not descricao:
            st.warning("⚠️ Adicione uma descrição!")
        else:
            try:
                salvar_registro(data, descricao, categoria, tipo_limpo, valor, quem)
                st.balloons()
                st.success(f"✅ {tipo_limpo} de R$ {valor:.2f} salva!")
            except Exception as e:
                st.error(f"Erro: {e}")

    # ÚLTIMOS LANÇAMENTOS
    st.markdown("---")
    st.markdown("### 📋 Últimos Lançamentos")

    try:
        df = ler_dados()
        if not df.empty:
            df_show = df.sort_values("data", ascending=False).head(10).copy()
            df_show["data"] = df_show["data"].dt.strftime("%d/%m/%Y")
            df_show["valor"] = df_show["valor"].apply(lambda x: f"R$ {x:.2f}")
            df_show = df_show.rename(columns={
                "data": "Data",
                "descricao": "Descrição",
                "categoria": "Categoria",
                "tipo": "Tipo",
                "valor": "Valor",
                "quem": "Quem"
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else:
            st.info("📭 Nenhum lançamento ainda!")
    except Exception as e:
        st.error(f"Erro carregando dados: {e}")

# ══════════════════════════════════════════
# ABA 2 - ANÁLISES
# ══════════════════════════════════════════
with aba2:

    st.markdown("### 📊 Análise Financeira")

    try:
        df = ler_dados()

        if df.empty:
            st.info("📭 Sem dados para analisar ainda. Adicione lançamentos!")
        else:
            # FILTRO DE MÊS
            meses_disponiveis = df["data"].dt.to_period("M").dropna().unique()
            meses_str = sorted([str(m) for m in meses_disponiveis], reverse=True)
            mes_selecionado = st.selectbox("📅 Mês:", meses_str)

            df_mes = df[df["data"].dt.to_period("M").astype(str) == mes_selecionado]

            entradas = df_mes[df_mes["tipo"] == "Entrada"]["valor"].sum()
            saidas = df_mes[df_mes["tipo"] == "Saída"]["valor"].sum()
            saldo = entradas - saidas

            # CARDS RESUMO
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class='card-verde'>
                        <h3>💚 Entradas</h3>
                        <h1>R$ {entradas:,.2f}</h1>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class='card-vermelho'>
                        <h3>❤️ Saídas</h3>
                        <h1>R$ {saidas:,.2f}</h1>
                    </div>
                """, unsafe_allow_html=True)

            cor_saldo = "card-verde" if saldo >= 0 else "card-vermelho"
            emoji_saldo = "😊" if saldo >= 0 else "😰"
            st.markdown(f"""
                <div class='{cor_saldo}'>
                    <h3>{emoji_saldo} Saldo do Mês</h3>
                    <h1>R$ {saldo:,.2f}</h1>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            # GASTOS POR CATEGORIA
            st.markdown("#### 🏷️ Gastos por Categoria")
            df_saidas = df_mes[df_mes["tipo"] == "Saída"]
            if not df_saidas.empty:
                cat_group = df_saidas.groupby("categoria")["valor"].sum().sort_values(ascending=False)
                df_cat = pd.DataFrame({
                    "Categoria": cat_group.index,
                    "Total (R$)": cat_group.values
                })
                df_cat["Total (R$)"] = df_cat["Total (R$)"].apply(lambda x: f"R$ {x:.2f}")
                st.dataframe(df_cat, use_container_width=True, hide_index=True)
            else:
                st.info("Sem saídas neste mês")

            st.markdown("---")

            # GASTOS POR PESSOA
            st.markdown("#### 👤 Divisão por Pessoa")
            df_pessoa = df_mes[df_mes["tipo"] == "Saída"].groupby("quem")["valor"].sum()
            if not df_pessoa.empty:
                col1, col2 = st.columns(2)
                patrick_gasto = df_pessoa.get("Patrick", 0)
                renata_gasto = df_pessoa.get("Renata", 0)
                nos_gasto = df_pessoa.get("Nós dois", 0)

                with col1:
                    st.markdown(f"""
                        <div class='card'>
                            <h3>👨 Patrick</h3>
                            <h1>R$ {patrick_gasto:,.2f}</h1>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                        <div class='card'>
                            <h3>👩 Renata</h3>
                            <h1>R$ {renata_gasto:,.2f}</h1>
                        </div>
                    """, unsafe_allow_html=True)

                if nos_gasto > 0:
                    st.markdown(f"""
                        <div class='card'>
                            <h3>💑 Nós dois</h3>
                            <h1>R$ {nos_gasto:,.2f}</h1>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")

            # TODOS OS LANÇAMENTOS DO MÊS
            st.markdown("#### 📋 Todos os lançamentos do mês")
            df_show = df_mes.sort_values("data", ascending=False).copy()
            df_show["data"] = df_show["data"].dt.strftime("%d/%m")
            df_show["valor"] = df_show["valor"].apply(lambda x: f"R$ {x:.2f}")
            df_show = df_show.rename(columns={
                "data": "Data", "descricao": "Descrição",
                "categoria": "Categoria", "tipo": "Tipo",
                "valor": "Valor", "quem": "Quem"
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro análise: {e}")
