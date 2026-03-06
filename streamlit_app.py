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

PESSOAS = [
    "Patrick só",
    "Renata só",
    "Patrick/Casal",
    "Renata/Casal",
    "Casal"
]

# ─────────────────────────────────────────
# CSS MOBILE FIRST
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
        .card-verde h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; } .card-verde h1 { margin: 4px 0; font-size: 1.5rem; }

        .card-roxo { background: linear-gradient(135deg, #4a1a7b, #8e44ad); border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }
        .card-roxo h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; } .card-roxo h1 { margin: 4px 0; font-size: 1.5rem; }

        .card-vermelho { background: linear-gradient(135deg, #7b1a1a, #e74c3c); border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }
        .card-vermelho h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; } .card-vermelho h1 { margin: 4px 0; font-size: 1.5rem; }

        .mini-card { border-radius: 16px; padding: 14px 12px; color: white; margin-bottom: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
        .mini-card .mc-label { font-size: 0.72rem; opacity: 0.75; letter-spacing: 0.07em; text-transform: uppercase; }
        .mini-card .mc-value { font-size: 1.25rem; font-weight: 800; margin-top: 2px; line-height: 1.1; }
        .mini-card .mc-icon { font-size: 1.4rem; margin-bottom: 4px; }

        .mc-blue   { background: linear-gradient(135deg, #1a3a7b, #2e6da4); }
        .mc-purple { background: linear-gradient(135deg, #4a1a7b, #8e44ad); }
        .mc-orange { background: linear-gradient(135deg, #f39c12, #e67e22); }
        .mc-pink   { background: linear-gradient(135deg, #e91e63, #ad1457); }
        .mc-green  { background: linear-gradient(135deg, #11723e, #27ae60); }
        .mc-red    { background: linear-gradient(135deg, #7b1a1a, #e74c3c); }

        .hero-card { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); border-radius: 20px; padding: 22px 18px 18px; color: white; margin-bottom: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
        .hero-card .label { font-size: 0.75rem; opacity: 0.65; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px; }
        .hero-card .value { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
        .hero-card .sub { font-size: 0.78rem; opacity: 0.55; margin-top: 4px; }

        .section-title { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #7f8c9a; margin: 18px 0 8px 2px; }

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
# FUNÇÕES DE DADOS
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
    ler_dados.clear()

def get_sheet_id(sheet_name):
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    raise ValueError(f"Aba '{sheet_name}' não encontrada na planilha.")

def excluir_registro(indice_real):
    aba_id = get_sheet_id(ABA_NOME)
    linha = int(indice_real) + 2
    requests = [{
        "deleteDimension": {
            "range": {"sheetId": aba_id, "dimension": "ROWS",
                      "startIndex": linha - 1, "endIndex": linha}
        }
    }]
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID, body={"requests": requests}
    ).execute()
    ler_dados.clear()

# ─────────────────────────────────────────
# FUNÇÃO: SALDO INDIVIDUAL POR PESSOA
# ─────────────────────────────────────────
def calcular_saldo_individual(df):
    """
    Patrick: entradas 'Patrick só' − saídas 'Patrick só' + 'Patrick/Casal'
    Renata:  entradas 'Renata só'  − saídas 'Renata só'  + 'Renata/Casal'
    Casal puro: saídas marcadas como 'Casal' (sem dono de conta definido)
    Saldo casal: todas entradas − todas saídas
    """
    entrada_patrick = df[(df["tipo"] == "Entrada") & (df["quem"] == "Patrick só")]["valor"].sum()
    entrada_renata  = df[(df["tipo"] == "Entrada") & (df["quem"] == "Renata só")]["valor"].sum()

    saida_patrick = df[(df["tipo"] == "Saída") & (df["quem"].isin(["Patrick só", "Patrick/Casal"]))]["valor"].sum()
    saida_renata  = df[(df["tipo"] == "Saída") & (df["quem"].isin(["Renata só",  "Renata/Casal"]))]["valor"].sum()
    saida_casal   = df[(df["tipo"] == "Saída") & (df["quem"] == "Casal")]["valor"].sum()

    return {
        "entrada_patrick": entrada_patrick,
        "entrada_renata":  entrada_renata,
        "saida_patrick":   saida_patrick,
        "saida_renata":    saida_renata,
        "saida_casal":     saida_casal,
        "saldo_patrick":   entrada_patrick - saida_patrick,
        "saldo_renata":    entrada_renata  - saida_renata,
    }

    def soma(tipo_reg, quem_lista, fator=1.0):
        return df[(df["tipo"] == tipo_reg) & (df["quem"].isin(quem_lista))]["valor"].sum() * fator

    # Entradas
    entrada_patrick = (
        soma("Entrada", ["Patrick só", "Patrick/Casal"]) +
        soma("Entrada", ["Casal"], 0.5)
    )
    entrada_renata = (
        soma("Entrada", ["Renata só", "Renata/Casal"]) +
        soma("Entrada", ["Casal"], 0.5)
    )

    # Saídas
    saida_patrick = (
        soma("Saída", ["Patrick só", "Patrick/Casal"]) +
        soma("Saída", ["Casal"], 0.5)
    )
    saida_renata = (
        soma("Saída", ["Renata só", "Renata/Casal"]) +
        soma("Saída", ["Casal"], 0.5)
    )

    return {
        "entrada_patrick": entrada_patrick,
        "entrada_renata": entrada_renata,
        "saida_patrick": saida_patrick,
        "saida_renata": saida_renata,
        "saldo_patrick": entrada_patrick - saida_patrick,
        "saldo_renata": entrada_renata - saida_renata,
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
# 3 ABAS
# ─────────────────────────────────────────
aba0, aba1, aba2 = st.tabs(["🏠 Início", "📝 Lançar", "📊 Análises"])

# ══════════════════════════════════════════
# ABA 0 - INÍCIO
# ══════════════════════════════════════════
with aba0:
    st.markdown("### 👋 Olá, Patrick & Renata!")

    try:
        if df_global.empty:
            st.info("📭 Nenhum lançamento ainda. Vá para **Lançar**!")
        else:
            # Saldo geral = TODAS entradas − TODAS saídas (histórico completo)
            total_entradas = df_global[df_global["tipo"] == "Entrada"]["valor"].sum()
            total_saidas   = df_global[df_global["tipo"] == "Saída"]["valor"].sum()
            saldo_geral    = total_entradas - total_saidas

            saldo_ind = calcular_saldo_individual(df_global)

            sinal = "+" if saldo_geral >= 0 else ""
            cor_val = "#2ecc71" if saldo_geral >= 0 else "#e74c3c"

            st.markdown(f"""
            <div class="hero-card">
                <div class="label">💰 Saldo Geral (todo o histórico)</div>
                <div class="value" style="color:{cor_val};">{sinal}R$ {saldo_geral:,.2f}</div>
                <div class="sub">
                    Entradas: R${total_entradas:,.2f} · Saídas: R${total_saidas:,.2f}
                </div>
            </div>""", unsafe_allow_html=True)

            # Saldos individuais
            st.markdown('<div class="section-title">💳 Saldo Individual</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)

            def cor_card(saldo):
                return "card-verde" if saldo >= 0 else "card-vermelho"

            with c1:
                sinal_p = "+" if saldo_ind["saldo_patrick"] >= 0 else ""
                st.markdown(f"""
                <div class="{cor_card(saldo_ind['saldo_patrick'])}">
                    <h3>👨‍💼 Patrick</h3>
                    <h1>{sinal_p}R$ {saldo_ind['saldo_patrick']:,.2f}</h1>
                </div>""", unsafe_allow_html=True)

            with c2:
                sinal_r = "+" if saldo_ind["saldo_renata"] >= 0 else ""
                st.markdown(f"""
                <div class="{cor_card(saldo_ind['saldo_renata'])}">
                    <h3>👩‍💼 Renata</h3>
                    <h1>{sinal_r}R$ {saldo_ind['saldo_renata']:,.2f}</h1>
                </div>""", unsafe_allow_html=True)

            # Último lançamento
            st.markdown('<div class="section-title">📌 Último Lançamento</div>', unsafe_allow_html=True)
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
# ABA 1 - LANÇAR
# ══════════════════════════════════════════
with aba1:
    st.markdown("### ➕ Novo Lançamento")

    tipo_limpo = st.radio(
        "Tipo:",
        ["Entrada", "Saída"],
        horizontal=True,
        format_func=lambda x: "📈 Entrada" if x == "Entrada" else "📉 Saída",
        key="tipo_lancamento"
    )

    with st.form("form_lancamento", clear_on_submit=True):
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
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

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
# ABA 2 - ANÁLISES
# ══════════════════════════════════════════
with aba2:
    try:
        df = ler_dados()
        if df.empty:
            st.info("📭 Sem dados.")
        else:
            meses = sorted(df["data"].dt.to_period("M").dropna().unique(), reverse=True)
            meses_str = [str(m) for m in meses]

            opcao_periodo = st.radio(
                "📅 Período:",
                ["Mês específico", "Todo o histórico"],
                horizontal=True
            )

            if opcao_periodo == "Mês específico":
                mes_selecionado = st.selectbox("Mês:", meses_str)
                df_periodo = df[df["data"].dt.to_period("M").astype(str) == mes_selecionado]
                label_periodo = mes_selecionado
            else:
                df_periodo = df.copy()
                label_periodo = "Histórico completo"

            # ── Saldo geral do período ──
            entradas = df_periodo[df_periodo["tipo"] == "Entrada"]["valor"].sum()
            saidas   = df_periodo[df_periodo["tipo"] == "Saída"]["valor"].sum()
            saldo    = entradas - saidas

            st.markdown(f"""
            <div class="hero-card">
                <div class="label">Saldo · {label_periodo}</div>
                <div class="value" style="color:{'#2ecc71' if saldo >= 0 else '#e74c3c'}">
                    {'+' if saldo >= 0 else ''}R$ {saldo:,.2f}
                </div>
                <div class="sub">Entradas: R${entradas:,.2f} · Saídas: R${saidas:,.2f}</div>
            </div>""", unsafe_allow_html=True)

            # ── Saldo individual ──
            saldo_ind = calcular_saldo_individual(df_periodo)

            st.markdown('<div class="section-title">💳 Saldo Individual</div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                sinal_p = "+" if saldo_ind["saldo_patrick"] >= 0 else ""
                cor_p = "card-verde" if saldo_ind["saldo_patrick"] >= 0 else "card-vermelho"
                st.markdown(f"""
                <div class="{cor_p}">
                    <h3>👨‍💼 Patrick</h3>
                    <h1>{sinal_p}R$ {saldo_ind['saldo_patrick']:,.2f}</h1>
                </div>""", unsafe_allow_html=True)

            with c2:
                sinal_r = "+" if saldo_ind["saldo_renata"] >= 0 else ""
                cor_r = "card-verde" if saldo_ind["saldo_renata"] >= 0 else "card-vermelho"
                st.markdown(f"""
                <div class="{cor_r}">
                    <h3>👩‍💼 Renata</h3>
                    <h1>{sinal_r}R$ {saldo_ind['saldo_renata']:,.2f}</h1>
                </div>""", unsafe_allow_html=True)

            # ── Detalhamento individual ──
            st.markdown('<div class="section-title">📊 Detalhamento Individual</div>', unsafe_allow_html=True)
            cols = st.columns(2)
            dados_detalhe = [
                ("👨‍💼 Patrick", saldo_ind["entrada_patrick"], saldo_ind["saida_patrick"], "mc-blue"),
                ("👩‍💼 Renata",  saldo_ind["entrada_renata"],  saldo_ind["saida_renata"],  "mc-purple"),
            ]
            for i, (nome, entrada, saida, cor) in enumerate(dados_detalhe):
                with cols[i]:
                    st.markdown(f"""
                    <div class="mini-card {cor}">
                        <div class="mc-label">{nome}</div>
                        <div style="font-size:0.72rem; opacity:0.75; margin-top:6px;">📈 Entradas</div>
                        <div class="mc-value">R${entrada:,.2f}</div>
                        <div style="font-size:0.72rem; opacity:0.75; margin-top:6px;">📉 Saídas</div>
                        <div class="mc-value">R${saida:,.2f}</div>
                    </div>""", unsafe_allow_html=True)

            # ── Gráfico pizza por categoria (saídas) ──
            df_saidas = df_periodo[df_periodo["tipo"] == "Saída"]
            if not df_saidas.empty:
                st.markdown('<div class="section-title">Gastos por Categoria</div>', unsafe_allow_html=True)
                cat_group = df_saidas.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
                fig = px.pie(cat_group, values="valor", names="categoria", hole=0.45)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=280, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # ── Tabela de lançamentos ──
            st.markdown('<div class="section-title">Lançamentos</div>', unsafe_allow_html=True)
            df_show = df_periodo.sort_values("data", ascending=False).copy()
            df_show["data"] = df_show["data"].dt.strftime("%d/%m/%Y")
            df_show["valor"] = df_show["valor"].apply(lambda x: f"R${x:.2f}")
            df_show = df_show[["data", "descricao", "quem", "categoria", "tipo", "valor"]]
            st.dataframe(
                df_show.rename(columns={
                    "data": "Data", "descricao": "Descrição", "quem": "Quem",
                    "categoria": "Categoria", "tipo": "Tipo", "valor": "Valor"
                }),
                use_container_width=True, hide_index=True
            )

    except Exception as e:
        st.error(f"Erro: {e}")
