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

# ── 5 TIPOS DE GASTOS: PESSOAIS + COMPARTILHADOS ──
PESSOAS = [
    "Patrick só", 
    "Renata só", 
    "Patrick/Casal", 
    "Renata/Casal", 
    "Casal"
]

METAS_PADRAO = {
    "Mercado": 800.0, "Contas Fixas": 1500.0, "Cartão de Crédito": 1000.0,
    "Lanche": 200.0, "Lazer": 300.0, "Gasolina": 400.0, "Reparos": 200.0,
    "Saúde": 300.0, "Educação": 200.0, "Outros": 200.0
}

# ─────────────────────────────────────────
# CSS MOBILE FIRST + NOVAS CORES
# ─────────────────────────────────────────
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <style>
        html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
        .stButton > button { width: 100%; padding: 0.8rem; font-size: 1.1rem; border-radius: 12px; font-weight: bold; }
        input, select, textarea { font-size: 1rem !important; }

        /* Cards principais */
        .card { background: linear-gradient(135deg, #1e3a5f, #2e6da4); border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }
        .card h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; } .card h1 { margin: 4px 0; font-size: 1.5rem; }

        .card-verde { background: linear-gradient(135deg, #1a5c38, #27ae60); border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }
        .card-verde h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; } .card-verde h1 { margin: 4px 0; font-size: 1.5rem; }

        .card-roxo { background: linear-gradient(135deg, #4a1a7b, #8e44ad); border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }
        .card-roxo h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; } .card-roxo h1 { margin: 4px 0; font-size: 1.5rem; }

        /* Mini cards 5 cores */
        .mini-card { border-radius: 16px; padding: 14px 12px; color: white; margin-bottom: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
        .mini-card .mc-label { font-size: 0.72rem; opacity: 0.75; letter-spacing: 0.07em; text-transform: uppercase; }
        .mini-card .mc-value { font-size: 1.25rem; font-weight: 800; margin-top: 2px; line-height: 1.1; }
        .mini-card .mc-icon { font-size: 1.4rem; margin-bottom: 4px; }

        .mc-blue   { background: linear-gradient(135deg, #1a3a7b, #2e6da4); }
        .mc-purple { background: linear-gradient(135deg, #4a1a7b, #8e44ad); }
        .mc-orange { background: linear-gradient(135deg, #f39c12, #e67e22); }
        .mc-pink   { background: linear-gradient(135deg, #e91e63, #ad1457); }
        .mc-green  { background: linear-gradient(135deg, #11723e, #27ae60); }
        .mc-gray   { background: linear-gradient(135deg, #6c757d, #adb5bd); opacity: 0.7; }

        /* Hero card */
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

# ── Garantir cabeçalhos ──
if "cabecalho_ok" not in st.session_state:
    def garantir_cabecalho():
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A1:F1"
        ).execute()
        if not result.get('values'):
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A1:F1",
                valueInputOption="RAW", body={"values": [COLUNAS]}
            ).execute()
    garantir_cabecalho()
    st.session_state["cabecalho_ok"] = True

# ─────────────────────────────────────────
# FUNÇÕES DE DADOS + ANÁLISE 5 TIPOS
# ─────────────────────────────────────────
@st.cache_data(ttl=60)
def ler_dados():
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A:F"
    ).execute()
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
    """Pega ID real da aba"""
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return 0

def excluir_registro(indice_real):
    """Delete corrigido com sheet ID real"""
    aba_id = get_sheet_id(ABA_NOME)
    linha = int(indice_real) + 2
    requests = [{
        "deleteDimension": {
            "range": {"sheetId": aba_id, "dimension": "ROWS", 
                     "startIndex": linha-1, "endIndex": linha}
        }
    }]
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body={"requests": requests}
    ).execute()
    st.cache_data.clear()

# ── FUNÇÃO ANÁLISE 5 TIPOS ──
def analisar_gastos_completos(df_mes):
    """Análise completa: 5 tipos de gastos"""
    patrick_so = df_mes[(df_mes["tipo"] == "Saída") & (df_mes["quem"] == "Patrick só")]["valor"].sum()
    renata_so = df_mes[(df_mes["tipo"] == "Saída") & (df_mes["quem"] == "Renata só")]["valor"].sum()
    patrick_casal = df_mes[(df_mes["tipo"] == "Saída") & (df_mes["quem"] == "Patrick/Casal")]["valor"].sum()
    renata_casal = df_mes[(df_mes["tipo"] == "Saída") & (df_mes["quem"] == "Renata/Casal")]["valor"].sum()
    casal_puro = df_mes[(df_mes["tipo"] == "Saída") & (df_mes["quem"] == "Casal")]["valor"].sum()
    
    patrick_total = patrick_so + (patrick_casal / 2)
    renata_total = renata_so + (renata_casal / 2)
    
    return {
        "patrick_so": patrick_so, "renata_so": renata_so,
        "patrick_casal": patrick_casal, "renata_casal": renata_casal,
        "casal_puro": casal_puro, "patrick_total": patrick_total,
        "renata_total": renata_total
    }

# ─────────────────────────────────────────
# DADOS GLOBAIS
# ─────────────────────────────────────────
df_global = ler_dados()

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("## 💑 Patrick & Renata")
st.markdown("##### 💰 Controle Financeiro do Casal")
st.markdown("---")

# ─────────────────────────────────────────
# 4 ABAS (SEM INVESTIMENTOS)
# ─────────────────────────────────────────
aba0, aba1, aba2, aba4 = st.tabs(["🏠 Início", "📝 Lançar", "📊 Análises", "🎯 Metas"])

# ══════════════════════════════════════════
# ABA 0 - INÍCIO
# ══════════════════════════════════════════
with aba0:
    st.markdown("### 👋 Olá, Patrick & Renata!")
    
    try:
        if df_global.empty:
            st.info("📭 Nenhum lançamento ainda. Vá para **Lançar**!")
        else:
            mes_atual_str = str(dt.date.today().strftime("%Y-%m"))
            df_mes_atual = df_global[df_global["data"].dt.to_period("M").astype(str) == mes_atual_str]
            
            entradas_atual = df_mes_atual[df_mes_atual["tipo"] == "Entrada"]["valor"].sum()
            saidas_atual = df_mes_atual[df_mes_atual["tipo"] == "Saída"]["valor"].sum()
            saldo_atual = entradas_atual - saidas_atual
            
            gastos_home = analisar_gastos_completos(df_mes_atual)
            
            # Hero card com totais
            sinal = "+" if saldo_atual >= 0 else ""
            cor_val = "#2ecc71" if saldo_atual >= 0 else "#e74c3c"
            st.markdown(f"""
            <div class="hero-card">
                <div class="label">Saldo {dt.date.today().strftime('%B/%Y')}</div>
                <div class="value" style="color:{cor_val};">{sinal}R$ {saldo_atual:,.2f}</div>
                <div class="sub">
                    Patrick: R${gastos_home['patrick_total']:,.0f} | 
                    Renata: R${gastos_home['renata_total']:,.0f}
                </div>
            </div>""", unsafe_allow_html=True)
            
            # Alertas metas
            alertas = []
            for cat, meta in METAS_PADRAO.items():
                gasto_cat = df_mes_atual[(df_mes_atual["tipo"] == "Saída") & (df_mes_atual["categoria"] == cat)]["valor"].sum()
                if meta > 0 and gasto_cat > meta:
                    alertas.append((cat, gasto_cat, meta))
            
            if alertas:
                st.markdown('<div class="section-title">⚠️ Metas Ultrapassadas</div>', unsafe_allow_html=True)
                for cat, gasto, meta in alertas:
                    st.markdown(f"""
                    <div class="alerta-meta">
                        🚨 <strong>{cat}</strong>: R${gasto:,.2f} de R${meta:,.2f}
                    </div>""", unsafe_allow_html=True)
            
            # Último lançamento
            ultimo = df_global.sort_values("data", ascending=False).iloc[0]
            emoji_tipo = "📈" if ultimo["tipo"] == "Entrada" else "📉"
            st.markdown(f"""
            <div style="background:var(--background-color,#f7f9fc); border:1px solid rgba(127,140,154,0.2);
                        border-radius:12px; padding:12px 16px; margin-bottom:8px;">
                <div style="font-size:0.75rem; color:#7f8c9a;">{pd.to_datetime(ultimo['data']).strftime('%d/%m/%Y')} · {ultimo['quem']}</div>
                <div style="font-weight:700; font-size:1rem;">{emoji_tipo} {ultimo['descricao']}</div>
                <div style="font-weight:800; font-size:1.1rem; color:{'#27ae60' if ultimo['tipo'] == 'Entrada' else '#e74c3c'};">
                    {'+ ' if ultimo['tipo'] == 'Entrada' else '- '}R$ {float(ultimo['valor']):,.2f}
                </div>
            </div>""", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Erro: {e}")

# ══════════════════════════════════════════
# ABA 1 - LANÇAR (COM 5 TIPOS)
# ══════════════════════════════════════════
with aba1:
    st.markdown("### ➕ Novo Lançamento")
    
    with st.form("form_lancamento", clear_on_submit=True):
        tipo = st.radio("Tipo:", ["📈 Entrada", "📉 Saída"], horizontal=True)
        tipo_limpo = "Entrada" if "Entrada" in tipo else "Saída"
        
        data = st.date_input("📅 Data", value=dt.date.today())
        descricao = st.text_input("📝 Descrição", placeholder="Ex: Gasolina semanal")
        
        col_cat, col_quem = st.columns(2)
        with col_cat:
            categoria = st.selectbox(
                "🏷️ Categoria", 
                CATEGORIAS_ENTRADA if tipo_limpo == "Entrada" else CATEGORIAS_SAIDA
            )
        with col_quem:
            quem = st.selectbox("👥 Quem?", PESSOAS)
            
        valor = st.number_input("💵 Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        submitted = st.form_submit_button("💾 SALVAR", type="primary", use_container_width=True)
    
    if submitted:
        if valor == 0 or not descricao:
            st.warning("⚠️ Valor e descrição obrigatórios!")
        else:
            with st.spinner("Salvando..."):
                try:
                    salvar_registro(data, descricao, categoria, tipo_limpo, valor, quem)
                    st.toast(f"✅ {tipo_limpo} R$ {valor:.2f} salvo!", icon="💾")
                except Exception as e:
                    st.error(f"Erro: {e}")
    
    # Últimos lançamentos
    st.markdown("---")
    st.markdown("### 📋 Últimos 10")
    try:
        df = ler_dados()
        if not df.empty:
            df_sorted = df.sort_values("data", ascending=False).head(10).copy()
            df_sorted["data_fmt"] = df_sorted["data"].dt.strftime("%d/%m")
            df_sorted["valor_fmt"] = df_sorted["valor"].apply(lambda x: f"R$ {x:.2f}")
            df_show = df_sorted[["data_fmt", "descricao", "categoria", "tipo", "valor_fmt", "quem"]].rename(columns={
                "data_fmt": "Data", "descricao": "Descrição", "categoria": "Categoria",
                "tipo": "Tipo", "valor_fmt": "Valor", "quem": "Quem"
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            
            with st.expander("🗑️ Excluir"):
                opcoes = [f"{row['data_fmt']} | {row['descricao'][:30]} | {row['quem']}"
                         for _, row in df_sorted.iterrows()]
                selecao = st.selectbox(":", opcoes)
                idx = opcoes.index(selecao)
                indice_real = df_sorted.index[idx]
                if st.button("🗑️ CONFIRMAR EXCLUSÃO", type="secondary"):
                    with st.spinner("Excluindo..."):
                        excluir_registro(indice_real)
                        st.success("✅ Excluído!")
                        st.rerun()
    except Exception as e:
        st.error(f"Erro: {e}")

# ══════════════════════════════════════════
# ABA 2 - ANÁLISES (5 TIPOS + GRÁFICOS)
# ══════════════════════════════════════════
with aba2:
    try:
        df = ler_dados()
        if df.empty:
            st.info("📭 Sem dados.")
        else:
            meses = sorted(df["data"].dt.to_period("M").dropna().unique(), reverse=True)
            meses_str = [str(m) for m in meses]
            mes_selecionado = st.selectbox("📅 Mês:", meses_str)
            df_mes = df[df["data"].dt.to_period("M").astype(str) == mes_selecionado]
            
            entradas = df_mes[df_mes["tipo"] == "Entrada"]["valor"].sum()
            saidas = df_mes[df_mes["tipo"] == "Saída"]["valor"].sum()
            saldo = entradas - saidas
            
            # Hero saldo
            st.markdown(f"""
            <div class="hero-card">
                <div class="label">Saldo {mes_selecionado}</div>
                <div class="value" style="color:{'#2ecc71' if saldo >= 0 else '#e74c3c'}">
                    {'+' if saldo >= 0 else ''}R$ {saldo:,.2f}
                </div>
            </div>""", unsafe_allow_html=True)
            
            # ── 5 TIPOS DE GASTOS ──
            gastos = analisar_gastos_completos(df_mes)
            
            st.markdown('<div class="section-title">Gastos por Tipo (5 categorias)</div>', unsafe_allow_html=True)
            cols1 = st.columns(3)
            cols2 = st.columns(2)
            
            with cols1[0]:
                st.markdown(f"""
                <div class="mini-card mc-blue">
                    <div class="mc-icon">👨‍💼</div><div class="mc-label">Patrick só</div>
                    <div class="mc-value">R${gastos['patrick_so']:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                
            with cols1[1]:
                st.markdown(f"""
                <div class="mini-card mc-purple">
                    <div class="mc-icon">👩‍💼</div><div class="mc-label">Renata só</div>
                    <div class="mc-value">R${gastos['renata_so']:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                
            with cols1[2]:
                st.markdown(f"""
                <div class="mini-card mc-orange">
                    <div class="mc-icon">👨💑</div><div class="mc-label">Patrick/Casal</div>
                    <div class="mc-value">R${gastos['patrick_casal']:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                
            with cols2[0]:
                st.markdown(f"""
                <div class="mini-card mc-pink">
                    <div class="mc-icon">👩💑</div><div class="mc-label">Renata/Casal</div>
                    <div class="mc-value">R${gastos['renata_casal']:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                
            with cols2[1]:
                st.markdown(f"""
                <div class="mini-card mc-green">
                    <div class="mc-icon">💑</div><div class="mc-label">Casal puro</div>
                    <div class="mc-value">R${gastos['casal_puro']:,.0f}</div>
                </div>""", unsafe_allow_html=True)
            
            # TOTAIS
            st.markdown('<div class="section-title">Totais Individuais (50% compartilhados)</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div class="card-verde">
                    <h3>Patrick TOTAL</h3><h1>R${gastos['patrick_total']:,.0f}</h1>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="card-roxo">
                    <h3>Renata TOTAL</h3><h1>R${gastos['renata_total']:,.0f}</h1>
                </div>""", unsafe_allow_html=True)
            
            # Pizza gastos categorias
            df_saidas = df_mes[df_mes["tipo"] == "Saída"]
            if not df_saidas.empty:
                st.markdown('<div class="section-title">Gastos por Categoria</div>', unsafe_allow_html=True)
                cat_group = df_saidas.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
                fig = px.pie(cat_group, values="valor", names="categoria", hole=0.45)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=280, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabela mês
            st.markdown('<div class="section-title">Lançamentos</div>', unsafe_allow_html=True)
            df_show = df_mes.sort_values("data", ascending=False).copy()
            df_show["data"] = df_show["data"].dt.strftime("%d/%m")
            df_show["valor"] = df_show["valor"].apply(lambda x: f"R${x:.2f}")
            df_show = df_show[["data", "descricao", "quem", "categoria", "tipo", "valor"]]
            st.dataframe(df_show.rename(columns={"data": "Data", "descricao": "Descrição", 
                                                "quem": "Quem", "categoria": "Categoria", 
                                                "tipo": "Tipo", "valor": "Valor"}), 
                        use_container_width=True, hide_index=True)
                        
    except Exception as e:
        st.error(f"Erro: {e}")

# ══════════════════════════════════════════
# ABA 4 - METAS
# ══════════════════════════════════════════
with aba4:
    st.markdown("### 🎯 Metas de Gastos")
    try:
        df = ler_dados()
        if df.empty:
            st.info("📭 Sem dados.")
        else:
            meses = sorted(df["data"].dt.to_period("M").dropna().unique(), reverse=True)
            mes_meta = st.selectbox("📅 Mês:", [str(m) for m in meses])
            df_mes_meta = df[df["data"].dt.to_period("M").astype(str) == mes_meta]
            
            # Meta global
            meta_global = st.number_input("🎯 Limite Total Mensal", value=5000.0, step=100.0)
            saidas_total = df_mes_meta[df_mes_meta["tipo"] == "Saída"]["valor"].sum()
            prog_global = min(saidas_total / meta_global, 1.0)
            st.progress(prog_global, text=f"R$ {saidas_total:,.2f} / R$ {meta_global:,.2f}")
            
            st.markdown("---")
            st.markdown("#### 🏷️ Por Categoria")
            for cat in CATEGORIAS_SAIDA:
                gasto_cat = df_mes_meta[(df_mes_meta["tipo"] == "Saída") & 
                                       (df_mes_meta["categoria"] == cat)]["valor"].sum()
                meta_cat = st.number_input(f"{cat}", value=METAS_PADRAO.get(cat, 200.0), 
                                         key=f"meta_{cat}", step=50.0)
                if meta_cat > 0:
                    prog = min(gasto_cat / meta_cat, 1.0)
                    st.progress(prog, text=f"{cat}: R${gasto_cat:,.0f}/{meta_cat:,.0f}")
                    
    except Exception as e:
        st.error(f"Erro: {e}")
