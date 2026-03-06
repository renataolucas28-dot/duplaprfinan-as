# ─────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime as dt
import calendar

SPREADSHEET_ID = "1_PmKlDUdZxp3UBlopyrPUlccJy_aP5aA_HvXa3FwqDo"
ABA_NOME       = "Registro"
ABA_METAS      = "Metas"
COLUNAS        = ["data", "descricao", "categoria", "tipo", "valor", "quem"]
COLUNAS_METAS  = ["categoria", "teto"]

TIPO_ENTRADA = "Entrada"
TIPO_SAIDA   = "Saída"

CATEGORIAS_SAIDA   = ["Mercado", "Contas Fixas", "Cartão de Crédito", "Lanche",
                      "Lazer", "Gasolina", "Reparos", "Saúde", "Educação", "Outros"]
CATEGORIAS_ENTRADA = ["Salário", "Freelance", "Outros"]
PESSOAS            = ["Patrick só", "Renata só", "Patrick/Casal", "Renata/Casal", "Casal"]

# ─────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────
st.set_page_config(
    page_title="💑 Finanças Patrick & Renata",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────
# LOGIN SIMPLES
# ─────────────────────────────────────────
def check_login():
    if st.session_state.get("autenticado"):
        return True

    st.markdown("## 🔐 Acesso Restrito")
    st.markdown("##### 💑 Finanças Patrick & Renata")
    st.markdown("---")

    with st.form("login_form"):
        senha = st.text_input("🔑 Senha", type="password", placeholder="Digite a senha")
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if entrar:
        if senha == st.secrets.get("app_password", "PR"):
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta.")

    return False

if not check_login():
    st.stop()

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
def inject_css():
    st.markdown("""
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
        <style>
            html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
            .stButton > button { width: 100%; padding: 0.8rem; font-size: 1.1rem; border-radius: 12px; font-weight: bold; }
            input, select, textarea { font-size: 1rem !important; }

            .card-base { border-radius: 16px; padding: 14px; text-align: center; color: white; margin-bottom: 10px; }
            .card-base h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; }
            .card-base h1 { margin: 4px 0; font-size: 1.5rem; }
            .card-verde    { background: linear-gradient(135deg, #1a5c38, #27ae60); }
            .card-vermelho { background: linear-gradient(135deg, #7b1a1a, #e74c3c); }

            .mini-card { border-radius: 16px; padding: 14px 12px; color: white; margin-bottom: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
            .mini-card .mc-label { font-size: 0.72rem; opacity: 0.75; letter-spacing: 0.07em; text-transform: uppercase; }
            .mini-card .mc-value { font-size: 1.25rem; font-weight: 800; margin-top: 2px; line-height: 1.1; }
            .mini-card .mc-icon  { font-size: 1.4rem; margin-bottom: 4px; }

            .mc-blue   { background: linear-gradient(135deg, #1a3a7b, #2e6da4); }
            .mc-purple { background: linear-gradient(135deg, #4a1a7b, #8e44ad); }
            .mc-orange { background: linear-gradient(135deg, #f39c12, #e67e22); }
            .mc-green  { background: linear-gradient(135deg, #11723e, #27ae60); }
            .mc-red    { background: linear-gradient(135deg, #7b1a1a, #e74c3c); }
            .mc-teal   { background: linear-gradient(135deg, #0f6674, #17a2b8); }

            .hero-card { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); border-radius: 20px; padding: 22px 18px 18px; color: white; margin-bottom: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
            .hero-card .label { font-size: 0.75rem; opacity: 0.65; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px; }
            .hero-card .value { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
            .hero-card .sub   { font-size: 0.78rem; opacity: 0.55; margin-top: 4px; }

            .section-title { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #7f8c9a; margin: 18px 0 8px 2px; }

            .ranking-item { border-radius: 12px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; color: white; }
            .ranking-label { font-size: 0.85rem; font-weight: 600; }
            .ranking-value { font-size: 1rem; font-weight: 800; }
            .ranking-delta-up   { font-size: 0.72rem; color: #ff6b6b; margin-top: 2px; }
            .ranking-delta-down { font-size: 0.72rem; color: #6bffb8; margin-top: 2px; }

            .progress-bar-bg { background: rgba(255,255,255,0.1); border-radius: 8px; height: 14px; overflow: hidden; margin-top: 6px; }
            .progress-bar-fill { height: 100%; border-radius: 8px; transition: width 0.3s ease; }

            #MainMenu { visibility: hidden; } footer { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

inject_css()

# ─────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────
def fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def sinal_str(valor: float) -> str:
    return "+" if valor >= 0 else ""

def cor_saldo(valor: float) -> str:
    return "#2ecc71" if valor >= 0 else "#e74c3c"

def cor_card(valor: float) -> str:
    return "card-verde" if valor >= 0 else "card-vermelho"

def dias_no_mes(ano: int, mes: int) -> int:
    return calendar.monthrange(ano, mes)[1]

# ─────────────────────────────────────────
# COMPONENTES HTML
# ─────────────────────────────────────────
def render_hero_card(label: str, valor: float, sub: str = "") -> None:
    st.markdown(f"""
    <div class="hero-card">
        <div class="label">{label}</div>
        <div class="value" style="color:{cor_saldo(valor)};">
            {sinal_str(valor)}{fmt_brl(valor)}
        </div>
        <div class="sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def render_card(titulo: str, valor: float, icone: str = "") -> None:
    classe = cor_card(valor)
    st.markdown(f"""
    <div class="card-base {classe}">
        <h3>{icone} {titulo}</h3>
        <h1>{sinal_str(valor)}{fmt_brl(valor)}</h1>
    </div>""", unsafe_allow_html=True)

def render_mini_card(icone: str, label: str, valor: float, cor: str) -> None:
    st.markdown(f"""
    <div class="mini-card {cor}">
        <div class="mc-icon">{icone}</div>
        <div class="mc-label">{label}</div>
        <div class="mc-value">{fmt_brl(valor)}</div>
    </div>""", unsafe_allow_html=True)

def render_mini_card_duplo(icone: str, label: str,
                            entrada: float, saida: float, cor: str) -> None:
    st.markdown(f"""
    <div class="mini-card {cor}">
        <div class="mc-label">{icone} {label}</div>
        <div style="font-size:0.72rem; opacity:0.75; margin-top:6px;">📈 Entradas</div>
        <div class="mc-value">{fmt_brl(entrada)}</div>
        <div style="font-size:0.72rem; opacity:0.75; margin-top:6px;">📉 Saídas</div>
        <div class="mc-value">{fmt_brl(saida)}</div>
    </div>""", unsafe_allow_html=True)

def render_saldo_individual(saldo_ind: dict) -> None:
    st.markdown('<div class="section-title">💳 Saldo Individual</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        render_card("Patrick", saldo_ind["saldo_patrick"], "👨‍💼")
    with c2:
        render_card("Renata", saldo_ind["saldo_renata"], "👩‍💼")

def render_ultimo_lancamento(df_raw: pd.DataFrame) -> None:
    df_valido = df_raw.dropna(subset=["data"])
    if df_valido.empty:
        return
    ultimo    = df_valido.sort_values("data", ascending=False).iloc[0]
    emoji_tipo = "📈" if ultimo["tipo"] == TIPO_ENTRADA else "📉"
    cor_valor  = "#27ae60" if ultimo["tipo"] == TIPO_ENTRADA else "#e74c3c"
    prefixo    = "+ " if ultimo["tipo"] == TIPO_ENTRADA else "- "
    st.markdown(f"""
    <div style="background:var(--background-color,#f7f9fc); border:1px solid rgba(127,140,154,0.2);
                border-radius:12px; padding:12px 16px; margin-bottom:8px;">
        <div style="font-size:0.75rem; color:#7f8c9a;">
            {pd.to_datetime(ultimo['data']).strftime('%d/%m/%Y')} · {ultimo['quem']}
        </div>
        <div style="font-weight:700; font-size:1rem;">{emoji_tipo} {ultimo['descricao']}</div>
        <div style="font-weight:800; font-size:1.1rem; color:{cor_valor};">
            {prefixo}{fmt_brl(float(ultimo['valor']))}
        </div>
    </div>""", unsafe_allow_html=True)

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
        # Aba Registro
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A1:F1"
        ).execute()
        if not result.get('values'):
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A1:F1",
                valueInputOption="RAW", body={"values": [COLUNAS]}
            ).execute()
        # Aba Metas
        result_m = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=f"{ABA_METAS}!A1:B1"
        ).execute()
        if not result_m.get('values'):
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID, range=f"{ABA_METAS}!A1:B1",
                valueInputOption="RAW", body={"values": [COLUNAS_METAS]}
            ).execute()
    garantir_cabecalho()
    st.session_state["cabecalho_ok"] = True

# ─────────────────────────────────────────
# FUNÇÕES DE DADOS
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def ler_dados() -> pd.DataFrame:
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A:F"
    ).execute()
    values = result.get('values', [])
    if len(values) > 1:
        df = pd.DataFrame(values[1:], columns=values[0])
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        df["data"]  = pd.to_datetime(df["data"], errors="coerce")
        return df
    return pd.DataFrame(columns=COLUNAS)

@st.cache_data(ttl=300)
def ler_metas() -> pd.DataFrame:
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_METAS}!A:B"
    ).execute()
    values = result.get('values', [])
    if len(values) > 1:
        df = pd.DataFrame(values[1:], columns=values[0])
        df["teto"] = pd.to_numeric(df["teto"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame(columns=COLUNAS_METAS)

def salvar_registro(data: dt.date, descricao: str, categoria: str,
                    tipo: str, valor: float, quem: str) -> None:
    novo = [[data.isoformat(), descricao.strip(), categoria, tipo, float(valor), quem]]
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_NOME}!A:F",
        valueInputOption="RAW", body={"values": novo}
    ).execute()
    ler_dados.clear()

@st.cache_data(ttl=300)
def get_sheet_id(sheet_name: str) -> int:
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    raise ValueError(f"Aba '{sheet_name}' não encontrada.")

def excluir_registro(indice_real: int) -> None:
    aba_id = get_sheet_id(ABA_NOME)
    linha  = int(indice_real) + 2
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

def salvar_meta(categoria: str, teto: float) -> None:
    """Atualiza meta existente ou insere nova."""
    df_metas = ler_metas()
    result   = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_METAS}!A:B"
    ).execute()
    values = result.get('values', [["categoria", "teto"]])

    # Procura linha existente para atualizar
    for i, row in enumerate(values[1:], start=2):
        if row and row[0] == categoria:
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{ABA_METAS}!A{i}:B{i}",
                valueInputOption="RAW",
                body={"values": [[categoria, float(teto)]]}
            ).execute()
            ler_metas.clear()
            return

    # Insere nova linha
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range=f"{ABA_METAS}!A:B",
        valueInputOption="RAW", body={"values": [[categoria, float(teto)]]}
    ).execute()
    ler_metas.clear()

# ─────────────────────────────────────────
# LÓGICA FINANCEIRA
# ─────────────────────────────────────────
def calcular_saldo_individual(df: pd.DataFrame) -> dict:
    entrada_patrick = df[(df["tipo"] == TIPO_ENTRADA) & (df["quem"] == "Patrick só")]["valor"].sum()
    entrada_renata  = df[(df["tipo"] == TIPO_ENTRADA) & (df["quem"] == "Renata só")]["valor"].sum()
    saida_patrick   = df[(df["tipo"] == TIPO_SAIDA) & (df["quem"].isin(["Patrick só", "Patrick/Casal"]))]["valor"].sum()
    saida_renata    = df[(df["tipo"] == TIPO_SAIDA) & (df["quem"].isin(["Renata só",  "Renata/Casal"]))]["valor"].sum()
    saida_casal     = df[(df["tipo"] == TIPO_SAIDA) & (df["quem"] == "Casal")]["valor"].sum()
    return {
        "entrada_patrick": entrada_patrick, "entrada_renata":  entrada_renata,
        "saida_patrick":   saida_patrick,   "saida_renata":    saida_renata,
        "saida_casal":     saida_casal,
        "saldo_patrick":   entrada_patrick - saida_patrick,
        "saldo_renata":    entrada_renata  - saida_renata,
    }

def projecao_mes(df_mes: pd.DataFrame) -> dict:
    """Calcula projeção de gastos até o fim do mês."""
    hoje         = dt.date.today()
    dias_passados = hoje.day
    total_dias   = dias_no_mes(hoje.year, hoje.month)
    dias_restantes = total_dias - dias_passados

    saidas_ate_hoje = df_mes[df_mes["tipo"] == TIPO_SAIDA]["valor"].sum()
    media_diaria    = saidas_ate_hoje / dias_passados if dias_passados > 0 else 0
    projecao        = saidas_ate_hoje + (media_diaria * dias_restantes)

    return {
        "saidas_ate_hoje":  saidas_ate_hoje,
        "media_diaria":     media_diaria,
        "projecao":         projecao,
        "dias_passados":    dias_passados,
        "dias_restantes":   dias_restantes,
        "total_dias":       total_dias,
    }

def ranking_categorias(df_mes: pd.DataFrame, df_mes_ant: pd.DataFrame,
                        excluir: list = None) -> pd.DataFrame:
    """Ranking de gastos por categoria, comparando com mês anterior."""
    excluir = excluir or []
    df_s    = df_mes[df_mes["tipo"] == TIPO_SAIDA]
    df_a    = df_mes_ant[df_mes_ant["tipo"] == TIPO_SAIDA]

    if excluir:
        df_s = df_s[~df_s["categoria"].isin(excluir)]
        df_a = df_a[~df_a["categoria"].isin(excluir)]

    atual     = df_s.groupby("categoria")["valor"].sum().rename("atual")
    anterior  = df_a.groupby("categoria")["valor"].sum().rename("anterior")
    ranking   = pd.concat([atual, anterior], axis=1).fillna(0).reset_index()
    ranking["delta"]  = ranking["atual"] - ranking["anterior"]
    ranking["delta_pct"] = ranking.apply(
        lambda r: (r["delta"] / r["anterior"] * 100) if r["anterior"] > 0 else 0, axis=1
    )
    return ranking.sort_values("atual", ascending=False)

# ─────────────────────────────────────────
# DADOS GLOBAIS
# ─────────────────────────────────────────
with st.spinner("Carregando dados..."):
    df_global  = ler_dados()
    df_metas   = ler_metas()

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
col_titulo, col_sair = st.columns([5, 1])
with col_titulo:
    st.markdown("## 💑 Patrick & Renata")
    st.markdown("##### 💰 Controle Financeiro do Casal")
with col_sair:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪", help="Sair"):
        st.session_state["autenticado"] = False
        st.rerun()
st.markdown("---")

# ─────────────────────────────────────────
# 5 ABAS
# ─────────────────────────────────────────
aba0, aba1, aba2, aba3, aba4 = st.tabs([
    "🏠 Início", "📝 Lançar", "📊 Análises", "🎯 Metas", "📈 Evolução"
])

# ══════════════════════════════════════════
# ABA 0 — INÍCIO
# ══════════════════════════════════════════
with aba0:
    st.markdown("### 👋 Olá, Patrick & Renata!")
    try:
        if df_global.empty:
            st.info("📭 Nenhum lançamento ainda. Vá para **Lançar**!")
        else:
            total_entradas = df_global[df_global["tipo"] == TIPO_ENTRADA]["valor"].sum()
            total_saidas   = df_global[df_global["tipo"] == TIPO_SAIDA]["valor"].sum()
            saldo_geral    = total_entradas - total_saidas
            saldo_ind      = calcular_saldo_individual(df_global)

            render_hero_card(
                "💰 Saldo Geral (todo o histórico)",
                saldo_geral,
                f"Entradas: {fmt_brl(total_entradas)} · Saídas: {fmt_brl(total_saidas)}"
            )
            render_saldo_individual(saldo_ind)

            # Projeção do mês atual
            hoje_periodo = str(dt.date.today())[:7]
            df_valido    = df_global.dropna(subset=["data"])
            df_mes_atual = df_valido[df_valido["data"].dt.to_period("M").astype(str) == hoje_periodo]

            

            st.markdown('<div class="section-title">📌 Último Lançamento</div>', unsafe_allow_html=True)
            render_ultimo_lancamento(df_global)

    except Exception as e:
        st.error(f"Erro ao carregar início: {e}")

# ══════════════════════════════════════════
# ABA 1 — LANÇAR
# ══════════════════════════════════════════
with aba1:
    st.markdown("### ➕ Novo Lançamento")

    tipo_limpo = st.radio(
        "Tipo:", [TIPO_ENTRADA, TIPO_SAIDA], horizontal=True,
        format_func=lambda x: "📈 Entrada" if x == TIPO_ENTRADA else "📉 Saída",
        key="tipo_lancamento"
    )

    with st.form("form_lancamento", clear_on_submit=True):
        data      = st.date_input("📅 Data", value=dt.date.today())
        descricao = st.text_input("📝 Descrição", placeholder="Ex: Gasolina semanal")
        col_cat, col_quem = st.columns(2)
        with col_cat:
            categoria = st.selectbox(
                "🏷️ Categoria",
                CATEGORIAS_ENTRADA if tipo_limpo == TIPO_ENTRADA else CATEGORIAS_SAIDA
            )
        with col_quem:
            quem = st.selectbox("👥 Quem?", PESSOAS)
        valor     = st.number_input("💵 Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        submitted = st.form_submit_button("💾 SALVAR", type="primary", use_container_width=True)

    if submitted:
        descricao_limpa = descricao.strip()
        if valor == 0:
            st.warning("⚠️ O valor não pode ser zero.")
        elif len(descricao_limpa) < 3:
            st.warning("⚠️ Descrição muito curta (mínimo 3 caracteres).")
        elif valor > 1_000_000:
            st.warning("⚠️ Valor muito alto — verifique antes de salvar.")
        else:
            with st.spinner("Salvando..."):
                try:
                    salvar_registro(data, descricao_limpa, categoria, tipo_limpo, valor, quem)
                    st.toast(f"✅ {tipo_limpo} {fmt_brl(valor)} salvo!", icon="💾")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    st.markdown("### 📋 Últimos 10")
    try:
        if not df_global.empty:
            df_sorted = df_global.dropna(subset=["data"]).sort_values("data", ascending=False).head(10).copy()
            df_sorted["data_fmt"]  = df_sorted["data"].dt.strftime("%d/%m")
            df_sorted["valor_fmt"] = df_sorted["valor"].apply(fmt_brl)
            st.dataframe(
                df_sorted[["data_fmt", "descricao", "categoria", "tipo", "valor_fmt", "quem"]].rename(columns={
                    "data_fmt": "Data", "descricao": "Descrição", "categoria": "Categoria",
                    "tipo": "Tipo", "valor_fmt": "Valor", "quem": "Quem"
                }),
                use_container_width=True, hide_index=True
            )

            with st.expander("🗑️ Excluir lançamento"):
                opcoes = [
                    f"{row['data_fmt']} | {str(row['descricao'])[:30]} | {row['quem']}"
                    for _, row in df_sorted.iterrows()
                ]
                selecao     = st.selectbox("Selecione o lançamento:", opcoes)
                idx         = opcoes.index(selecao)
                indice_real = df_sorted.index[idx]
                st.warning("⚠️ Esta ação é irreversível.")
                col_sim, col_nao = st.columns(2)
                with col_sim:
                    if st.button("🗑️ Confirmar exclusão", type="secondary", use_container_width=True):
                        with st.spinner("Excluindo..."):
                            excluir_registro(indice_real)
                            st.success("✅ Registro excluído!")
                            st.rerun()
                with col_nao:
                    st.button("↩️ Cancelar", use_container_width=True)
        else:
            st.info("📭 Nenhum lançamento ainda.")
    except Exception as e:
        st.error(f"Erro ao listar lançamentos: {e}")

# ══════════════════════════════════════════
# ABA 2 — ANÁLISES
# ══════════════════════════════════════════
with aba2:
    try:
        if df_global.empty:
            st.info("📭 Sem dados para analisar.")
        else:
            df_valido = df_global.dropna(subset=["data"])
            meses     = sorted(df_valido["data"].dt.to_period("M").unique(), reverse=True)
            meses_str = [str(m) for m in meses]

            opcao_periodo = st.radio(
                "📅 Período:", ["Mês específico", "Todo o histórico"], horizontal=True
            )

            if opcao_periodo == "Mês específico":
                mes_selecionado = st.selectbox("Mês:", meses_str)
                df_periodo      = df_valido[df_valido["data"].dt.to_period("M").astype(str) == mes_selecionado]
                label_periodo   = mes_selecionado
            else:
                df_periodo    = df_valido.copy()
                label_periodo = "Histórico completo"

            entradas  = df_periodo[df_periodo["tipo"] == TIPO_ENTRADA]["valor"].sum()
            saidas    = df_periodo[df_periodo["tipo"] == TIPO_SAIDA]["valor"].sum()
            saldo     = entradas - saidas
            saldo_ind = calcular_saldo_individual(df_periodo)

            render_hero_card(
                f"Saldo · {label_periodo}", saldo,
                f"Entradas: {fmt_brl(entradas)} · Saídas: {fmt_brl(saidas)}"
            )
            render_saldo_individual(saldo_ind)

            # ── Detalhamento individual ──
            st.markdown('<div class="section-title">📊 Detalhamento Individual</div>', unsafe_allow_html=True)
            cols = st.columns(2)
            with cols[0]:
                render_mini_card_duplo("👨‍💼", "Patrick", saldo_ind["entrada_patrick"], saldo_ind["saida_patrick"], "mc-blue")
            with cols[1]:
                render_mini_card_duplo("👩‍💼", "Renata", saldo_ind["entrada_renata"], saldo_ind["saida_renata"], "mc-purple")

            # ── Gastos Casal sem dono ──
            if saldo_ind["saida_casal"] > 0:
                st.markdown('<div class="section-title">💑 Gastos Casal (sem dono de conta)</div>', unsafe_allow_html=True)
                render_mini_card("💑", 'Saídas marcadas como "Casal"', saldo_ind["saida_casal"], "mc-orange")

            # ── Gastos para manter a casa ──
            st.markdown('<div class="section-title">🏠 Gastos para Manter a Casa</div>', unsafe_allow_html=True)
            gasto_patrick_casal = df_periodo[(df_periodo["tipo"] == TIPO_SAIDA) & (df_periodo["quem"] == "Patrick/Casal")]["valor"].sum()
            gasto_renata_casal  = df_periodo[(df_periodo["tipo"] == TIPO_SAIDA) & (df_periodo["quem"] == "Renata/Casal")]["valor"].sum()
            total_casa          = gasto_patrick_casal + gasto_renata_casal

            if total_casa > 0:
                pct_patrick = (gasto_patrick_casal / total_casa) * 100
                pct_renata  = (gasto_renata_casal  / total_casa) * 100
                render_hero_card("💑 Total gasto para manter a casa", total_casa, "Patrick/Casal + Renata/Casal")
                cols_casa = st.columns(2)
                with cols_casa[0]:
                    st.markdown(f"""
                    <div class="mini-card mc-blue">
                        <div class="mc-icon">👨‍💼</div>
                        <div class="mc-label">Patrick contribuiu</div>
                        <div class="mc-value">{fmt_brl(gasto_patrick_casal)}</div>
                        <div style="font-size:1rem; font-weight:700; margin-top:4px; opacity:0.9;">{pct_patrick:.1f}% do total</div>
                    </div>""", unsafe_allow_html=True)
                with cols_casa[1]:
                    st.markdown(f"""
                    <div class="mini-card mc-purple">
                        <div class="mc-icon">👩‍💼</div>
                        <div class="mc-label">Renata contribuiu</div>
                        <div class="mc-value">{fmt_brl(gasto_renata_casal)}</div>
                        <div style="font-size:1rem; font-weight:700; margin-top:4px; opacity:0.9;">{pct_renata:.1f}% do total</div>
                    </div>""", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="border-radius:12px; overflow:hidden; height:22px; display:flex; margin-bottom:6px;">
                    <div style="width:{pct_patrick:.1f}%; background:linear-gradient(135deg,#1a3a7b,#2e6da4); display:flex; align-items:center; justify-content:center; font-size:0.72rem; color:white; font-weight:700;">{pct_patrick:.1f}%</div>
                    <div style="width:{pct_renata:.1f}%; background:linear-gradient(135deg,#4a1a7b,#8e44ad); display:flex; align-items:center; justify-content:center; font-size:0.72rem; color:white; font-weight:700;">{pct_renata:.1f}%</div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#7f8c9a; margin-bottom:8px;">
                    <span>👨‍💼 Patrick</span><span>👩‍💼 Renata</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.info("Nenhum gasto do tipo Patrick/Casal ou Renata/Casal no período.")

            # ── Ranking de categorias ──
            if opcao_periodo == "Mês específico" and len(meses_str) > 1:
                st.markdown('<div class="section-title">🏆 Ranking de Categorias (excl. Contas Fixas)</div>', unsafe_allow_html=True)
                idx_mes_ant = meses_str.index(mes_selecionado) + 1
                if idx_mes_ant < len(meses_str):
                    mes_anterior = meses_str[idx_mes_ant]
                    df_mes_ant   = df_valido[df_valido["data"].dt.to_period("M").astype(str) == mes_anterior]
                    ranking = ranking_categorias(df_periodo, df_mes_ant, excluir=["Contas Fixas"])

                    # Categoria que mais cresceu
                    cresceu = ranking[ranking["delta"] > 0].sort_values("delta_pct", ascending=False)
                    if not cresceu.empty:
                        top = cresceu.iloc[0]
                        st.markdown(f"""
                        <div class="mini-card mc-red">
                            <div class="mc-icon">📈</div>
                            <div class="mc-label">Categoria que mais cresceu vs mês anterior</div>
                            <div class="mc-value">{top['categoria']}</div>
                            <div style="font-size:0.85rem; margin-top:4px; opacity:0.9;">
                                +{top['delta_pct']:.1f}% · {fmt_brl(top['anterior'])} → {fmt_brl(top['atual'])}
                            </div>
                        </div>""", unsafe_allow_html=True)

                    # Ranking visual
                    cores = ["mc-blue", "mc-purple", "mc-teal", "mc-orange", "mc-green"]
                    for i, row in ranking.head(5).iterrows():
                        cor   = cores[list(ranking.index).index(i) % len(cores)]
                        delta = row["delta"]
                        seta  = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
                        cor_delta = "#ff6b6b" if delta > 0 else ("#6bffb8" if delta < 0 else "white")
                        pct_delta = f"{abs(row['delta_pct']):.1f}%"
                        st.markdown(f"""
                        <div class="mini-card {cor}" style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <div class="mc-label">{row['categoria']}</div>
                                <div class="mc-value">{fmt_brl(row['atual'])}</div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:1.3rem; color:{cor_delta};">{seta}</div>
                                <div style="font-size:0.72rem; color:{cor_delta};">{pct_delta} vs mês ant.</div>
                                <div style="font-size:0.68rem; opacity:0.65;">{fmt_brl(row['anterior'])}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("Sem mês anterior disponível para comparação.")

          

                    # Projeção vs metas
                    if not df_metas.empty:
                        st.markdown('<div class="section-title">🎯 Projeção vs Teto por Categoria</div>', unsafe_allow_html=True)
                        df_saidas_mes = df_periodo[df_periodo["tipo"] == TIPO_SAIDA]
                        cat_atual = df_saidas_mes.groupby("categoria")["valor"].sum()
                        for _, meta_row in df_metas.iterrows():
                            cat  = meta_row["categoria"]
                            teto = meta_row["teto"]
                            gasto_atual = cat_atual.get(cat, 0)
                            media_cat   = gasto_atual / proj["dias_passados"] if proj["dias_passados"] > 0 else 0
                            proj_cat    = media_cat * proj["total_dias"]
                            pct         = min((proj_cat / teto) * 100, 100) if teto > 0 else 0
                            cor_barra   = "#27ae60" if pct < 70 else ("#f39c12" if pct < 90 else "#e74c3c")
                            st.markdown(f"""
                            <div style="margin-bottom:12px;">
                                <div style="display:flex; justify-content:space-between; font-size:0.78rem; margin-bottom:4px;">
                                    <span style="font-weight:700;">{cat}</span>
                                    <span style="opacity:0.7;">{fmt_brl(proj_cat)} proj. / {fmt_brl(teto)} teto</span>
                                </div>
                                <div class="progress-bar-bg">
                                    <div class="progress-bar-fill" style="width:{pct:.1f}%; background:{cor_barra};"></div>
                                </div>
                            </div>""", unsafe_allow_html=True)

            # ── Gráfico pizza ──
            df_saidas = df_periodo[df_periodo["tipo"] == TIPO_SAIDA]
            if not df_saidas.empty:
                st.markdown('<div class="section-title">Gastos por Categoria</div>', unsafe_allow_html=True)
                cat_group = df_saidas.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
                fig = px.pie(cat_group, values="valor", names="categoria", hole=0.45, custom_data=["valor"])
                fig.update_traces(
                    textposition='inside', textinfo='percent+label',
                    hovertemplate="<b>%{label}</b><br>R$ %{customdata[0]:,.2f}<extra></extra>"
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # ── Tabela de lançamentos ──
            st.markdown('<div class="section-title">Lançamentos</div>', unsafe_allow_html=True)
            total_registros = len(df_periodo)
            df_exibicao     = df_periodo.sort_values("data", ascending=False).head(50).copy()
            if total_registros > 50:
                st.caption(f"Exibindo 50 de {total_registros} registros.")
            df_exibicao["data"]  = df_exibicao["data"].dt.strftime("%d/%m/%Y")
            df_exibicao["valor"] = df_exibicao["valor"].apply(fmt_brl)
            st.dataframe(
                df_exibicao[["data", "descricao", "quem", "categoria", "tipo", "valor"]].rename(columns={
                    "data": "Data", "descricao": "Descrição", "quem": "Quem",
                    "categoria": "Categoria", "tipo": "Tipo", "valor": "Valor"
                }),
                use_container_width=True, hide_index=True
            )

    except Exception as e:
        st.error(f"Erro na aba de análises: {e}")

# ══════════════════════════════════════════
# ABA 3 — METAS
# ══════════════════════════════════════════
with aba3:
    st.markdown("### 🎯 Teto de Gastos por Categoria")
    st.caption("Defina o limite mensal para cada categoria. A projeção na aba Análises usará esses valores.")

    try:
        df_metas_atual = ler_metas()

        with st.form("form_meta"):
            col_cat, col_val = st.columns(2)
            with col_cat:
                cat_meta = st.selectbox("🏷️ Categoria", CATEGORIAS_SAIDA)
            with col_val:
                # Pré-preenche com valor atual se existir
                valor_atual = 0.0
                if not df_metas_atual.empty:
                    linha = df_metas_atual[df_metas_atual["categoria"] == cat_meta]
                    if not linha.empty:
                        valor_atual = float(linha.iloc[0]["teto"])
                teto_val = st.number_input("💵 Teto mensal (R$)", min_value=0.0,
                                           value=valor_atual, step=10.0, format="%.2f")
            salvar_meta_btn = st.form_submit_button("💾 Salvar Meta", type="primary", use_container_width=True)

        if salvar_meta_btn:
            if teto_val == 0:
                st.warning("⚠️ Defina um valor maior que zero.")
            else:
                with st.spinner("Salvando meta..."):
                    salvar_meta(cat_meta, teto_val)
                    st.toast(f"✅ Meta de {cat_meta}: {fmt_brl(teto_val)}/mês salva!", icon="🎯")
                    st.rerun()

        # ── Tabela de metas salvas ──
        st.markdown("---")
        st.markdown("### 📋 Metas Definidas")
        df_metas_atual = ler_metas()

        if df_metas_atual.empty:
            st.info("Nenhuma meta definida ainda.")
        else:
            # Cruza com gastos do mês atual
            hoje_periodo_str = str(dt.date.today())[:7]
            df_valido_g      = df_global.dropna(subset=["data"])
            df_mes_atual_g   = df_valido_g[df_valido_g["data"].dt.to_period("M").astype(str) == hoje_periodo_str]
            cat_atual        = df_mes_atual_g[df_mes_atual_g["tipo"] == TIPO_SAIDA].groupby("categoria")["valor"].sum()

            for _, row in df_metas_atual.iterrows():
                cat         = row["categoria"]
                teto        = row["teto"]
                gasto       = cat_atual.get(cat, 0)
                pct         = min((gasto / teto) * 100, 100) if teto > 0 else 0
                cor_barra   = "#27ae60" if pct < 70 else ("#f39c12" if pct < 90 else "#e74c3c")
                emoji_status = "✅" if pct < 70 else ("⚠️" if pct < 100 else "🚨")

                st.markdown(f"""
                <div style="background:rgba(127,140,154,0.08); border-radius:12px; padding:12px 14px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                        <span style="font-weight:700; font-size:0.9rem;">{emoji_status} {cat}</span>
                        <span style="font-size:0.85rem; opacity:0.8;">{fmt_brl(gasto)} / {fmt_brl(teto)}</span>
                    </div>
                    <div class="progress-bar-bg" style="background:rgba(127,140,154,0.2);">
                        <div class="progress-bar-fill" style="width:{pct:.1f}%; background:{cor_barra};"></div>
                    </div>
                    <div style="font-size:0.72rem; opacity:0.6; margin-top:4px;">{pct:.1f}% do teto mensal usado</div>
                </div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro na aba de metas: {e}")

# ══════════════════════════════════════════
# ABA 4 — EVOLUÇÃO
# ══════════════════════════════════════════
with aba4:
    st.markdown("### 📈 Evolução Mensal")
    try:
        if df_global.empty:
            st.info("📭 Sem dados suficientes.")
        else:
            df_valido = df_global.dropna(subset=["data"])
            df_valido = df_valido.copy()
            df_valido["mes"] = df_valido["data"].dt.to_period("M").astype(str)

            # ── Gráfico de barras empilhadas: Entradas vs Saídas por mês ──
            st.markdown('<div class="section-title">📊 Entradas vs Saídas por Mês</div>', unsafe_allow_html=True)

            resumo_mes = df_valido.groupby(["mes", "tipo"])["valor"].sum().reset_index()
            resumo_pivot = resumo_mes.pivot(index="mes", columns="tipo", values="valor").fillna(0).reset_index()
            resumo_pivot = resumo_pivot.sort_values("mes")

            fig_bar = go.Figure()
            if TIPO_ENTRADA in resumo_pivot.columns:
                fig_bar.add_trace(go.Bar(
                    name="📈 Entradas", x=resumo_pivot["mes"],
                    y=resumo_pivot[TIPO_ENTRADA],
                    marker_color="#27ae60",
                    hovertemplate="<b>%{x}</b><br>Entradas: R$ %{y:,.2f}<extra></extra>"
                ))
            if TIPO_SAIDA in resumo_pivot.columns:
                fig_bar.add_trace(go.Bar(
                    name="📉 Saídas", x=resumo_pivot["mes"],
                    y=resumo_pivot[TIPO_SAIDA],
                    marker_color="#e74c3c",
                    hovertemplate="<b>%{x}</b><br>Saídas: R$ %{y:,.2f}<extra></extra>"
                ))
            fig_bar.update_layout(
                barmode="group", height=380,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                xaxis=dict(title=""),
                yaxis=dict(title="R$", gridcolor="rgba(127,140,154,0.15)")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # ── Saldo acumulado mês a mês ──
            st.markdown('<div class="section-title">💰 Saldo Mês a Mês</div>', unsafe_allow_html=True)
            if TIPO_ENTRADA in resumo_pivot.columns and TIPO_SAIDA in resumo_pivot.columns:
                resumo_pivot["saldo"] = resumo_pivot[TIPO_ENTRADA] - resumo_pivot[TIPO_SAIDA]
            else:
                col = TIPO_ENTRADA if TIPO_ENTRADA in resumo_pivot.columns else TIPO_SAIDA
                resumo_pivot["saldo"] = resumo_pivot[col] * (1 if col == TIPO_ENTRADA else -1)

            cores_saldo = ["#27ae60" if s >= 0 else "#e74c3c" for s in resumo_pivot["saldo"]]
            fig_saldo = go.Figure(go.Bar(
                x=resumo_pivot["mes"], y=resumo_pivot["saldo"],
                marker_color=cores_saldo,
                hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>"
            ))
            fig_saldo.add_hline(y=0, line_dash="dash", line_color="rgba(127,140,154,0.5)")
            fig_saldo.update_layout(
                height=320,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title=""),
                yaxis=dict(title="R$", gridcolor="rgba(127,140,154,0.15)")
            )
            st.plotly_chart(fig_saldo, use_container_width=True)

            # ── Evolução por categoria ao longo dos meses ──
            st.markdown('<div class="section-title">📂 Gastos por Categoria ao Longo dos Meses</div>', unsafe_allow_html=True)
            df_saidas_hist = df_valido[df_valido["tipo"] == TIPO_SAIDA]
            if not df_saidas_hist.empty:
                cat_mes = df_saidas_hist.groupby(["mes", "categoria"])["valor"].sum().reset_index()
                fig_line = px.line(
                    cat_mes, x="mes", y="valor", color="categoria",
                    markers=True,
                    labels={"mes": "", "valor": "R$", "categoria": "Categoria"},
                    custom_data=["categoria", "valor"]
                )
                fig_line.update_traces(
                    hovertemplate="<b>%{customdata[0]}</b><br>%{x}<br>R$ %{customdata[1]:,.2f}<extra></extra>"
                )
                fig_line.update_layout(
                    height=420,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="top", y=-0.2),
                    yaxis=dict(gridcolor="rgba(127,140,154,0.15)")
                )
                st.plotly_chart(fig_line, use_container_width=True)

    except Exception as e:
        st.error(f"Erro na aba de evolução: {e}")
