import streamlit as st
import pandas as pd
import plotly.express as px
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

CATEGORIAS_SAIDA = [
    "Mercado", "Contas Fixas", "Cartão de Crédito",
    "Lanche", "Lazer", "Gasolina", "Reparos",
    "Saúde", "Educação", "Outros"
]
CATEGORIAS_ENTRADA = ["Salário", "Freelance", "Outros"]

# ── 5 TIPOS DE GASTOS ──
PESSOAS = [
    "Patrick só", 
    "Renata só", 
    "Patrick/Casal", 
    "Renata/Casal", 
    "Casal"
]

METAS_PADRAO = {
    "Mercado": 800.0, "Contas Fixas": 1500.0, "Cartão de Crédito": 1000.0,
    "Lanche": 200.0, "Lazer": 300.0, "Gasolina": 400.0, 
    "Reparos": 200.0, "Saúde": 300.0, "Educação": 200.0, "Outros": 200.0
}

# ─────────────────────────────────────────
# CSS + CORES 5 TIPOS
# ─────────────────────────────────────────
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <style>
        html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
        .stButton > button { width: 100%; padding: 0.8rem; font-size: 1.1rem; border-radius: 12px; font-weight: bold; }
        input, select, textarea { font-size: 1rem !important; }

        .card { background: linear-gradient(135deg, #1e3a5f, #2e6da4); border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }
        .card h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; } .card h1 { margin: 4px 0; font-size: 1.5rem; }

        .card-verde { background: linear-gradient(135deg, #1a5c38, #27ae60); border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }
        .card-roxo { background: linear-gradient(135deg, #4a1a7b, #8e44ad); border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }

        .mini-card { border-radius: 16px; padding: 14px 12px; color: white; margin-bottom: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
        .mini-card .mc-label { font-size: 0.72rem; opacity: 0.75; letter-spacing: 0.07em; text-transform: uppercase; }
        .mini-card .mc-value { font-size: 1.25rem; font-weight: 800; margin-top: 2px; line-height: 1.1; }
        .mini-card .mc-icon { font-size: 1.4rem; margin-bottom: 4px; }

        .mc-blue   { background: linear-gradient(135deg, #1a3a7b, #2e6da4); }
        .mc-purple { background: linear-gradient(135deg, #4a1a7b, #8e44ad); }
        .mc-orange { background: linear-gradient(135deg, #f39c12, #e67e22); }
        .mc-pink   { background: linear-gradient(135deg, #e91e63, #ad1457); }
        .mc-green  { background: linear-gradient(135deg, #11723e, #27ae60); }

        .hero-card { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); border-radius: 20px; padding: 22px 18px 18px; color: white; margin-bottom: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
        .hero-card .label { font-size: 0.75rem; opacity: 0.65; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px; }
        .hero-card .value { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
        .hero-card .sub { font-size: 0.78rem; opacity: 0.55; margin-top: 4px; }

        .section-title { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #7f8c9a; margin: 18px 0 8px 2px; }
        .alerta-meta { background: linear-gradient(135deg, #7b1a1a, #e74c3c); border-radius: 12px; padding: 10px 14px; color: white; font-size: 0.85rem; margin-bottom: 6px; }

        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────
@st.cache_resource
def get_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build('sheets', 'v4', credentials=creds)

service = get_service()

if "cabecalho_ok" not in st.session_state:
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A1:F1").execute()
    if not result.get('values'):
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A1:F1",
            valueInputOption="RAW", body={"values": [COLUNAS]}
        ).execute()
    st.session_state["cabecalho_ok"] = True

# ─────────────────────────────────────────
# FUNÇÕES
# ─────────────────────────────────────────
@st.cache_data(ttl=60)
def ler_dados():
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A:F").execute()
    values = result.get('values', [])
    if len(values) > 1:
        df = pd.DataFrame(values[1:], columns=values[0])
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df
    return pd.DataFrame(columns=COLUNAS)

def salvar_registro(data, descricao, categoria, tipo, valor, quem):
    novo = [[data.isoformat(), descricao, categoria, tipo, float(valor), quem]]
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A:F",
        valueInputOption="RAW", body={"values": novo}
    ).execute()
    st.cache_data.clear()

def get_sheet_id(sheet_name):
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return 0

def excluir_registro(indice_real):
    aba_id = get_sheet_id(ABA_NOME)
    linha = int(indice_real) + 2
    requests = [{"deleteDimension": {"range": {"sheetId": aba_id, "dimension": "ROWS", 
                                             "startIndex": linha-1, "endIndex": linha}}}]
    service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
    st.cache_data.clear()

def analisar_gastos_completos(df_mes):
    patrick_so = df_mes[(df_mes["tipo"] == "Saída") & (df_mes["quem"] == "Patrick só")]["valor"].sum()
    renata_so = df_mes[(df_mes["tipo"]
