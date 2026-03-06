# ─────────────────────────────────────────
# config.py (inline por praticidade)
# ─────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime as dt

# ─────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────
SPREADSHEET_ID = "1_PmKlDUdZxp3UBlopyrPUlccJy_aP5aA_HvXa3FwqDo"
ABA_NOME       = "Registro"
COLUNAS        = ["data", "descricao", "categoria", "tipo", "valor", "quem"]

TIPO_ENTRADA = "Entrada"
TIPO_SAIDA   = "Saída"

CATEGORIAS_SAIDA   = ["Mercado", "Contas Fixas", "Cartão de Crédito", "Lanche",
                      "Lazer", "Gasolina", "Reparos", "Saúde", "Educação", "Outros"]
CATEGORIAS_ENTRADA = ["Salário", "Freelance", "Outros"]

PESSOAS = ["Patrick só", "Renata só", "Patrick/Casal", "Renata/Casal", "Casal"]

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

            .card-verde   { background: linear-gradient(135deg, #1a5c38, #27ae60); }
            .card-vermelho { background: linear-gradient(135deg, #7b1a1a, #e74c3c); }
            .card-azul    { background: linear-gradient(135deg, #1e3a5f, #2e6da4); }
            .card-roxo    { background: linear-gradient(135deg, #4a1a7b, #8e44ad); }

            .mini-card { border-radius: 16px; padding: 14px 12px; color: white; margin-bottom: 10px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
            .mini-card .mc-label { font-size: 0.72rem; opacity: 0.75; letter-spacing: 0.07em; text-transform: uppercase; }
            .mini-card .mc-value { font-size: 1.25rem; font-weight: 800; margin-top: 2px; line-height: 1.1; }
            .mini-card .mc-icon  { font-size: 1.4rem; margin-bottom: 4px; }

            .mc-blue   { background: linear-gradient(135deg, #1a3a7b, #2e6da4); }
            .mc-purple { background: linear-gradient(135deg, #4a1a7b, #8e44ad); }
            .mc-orange { background: linear-gradient(135deg, #f39c12, #e67e22); }
            .mc-green  { background: linear-gradient(135deg, #11723e, #27ae60); }
            .mc-red    { background: linear-gradient(135deg, #7b1a1a, #e74c3c); }

            .hero-card { background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); border-radius: 20px; padding: 22px 18px 18px; color: white; margin-bottom: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.25); }
            .hero-card .label { font-size: 0.75rem; opacity: 0.65; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px; }
            .hero-card .value { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
            .hero-card .sub   { font-size: 0.78rem; opacity: 0.55; margin-top: 4px; }

            .section-title { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #7f8c9a; margin: 18px 0 8px 2px; }

            #MainMenu { visibility: hidden; } footer { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

inject_css()

# ─────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────
def fmt_brl(valor: float) -> str:
    """Formata valor no padrão brasileiro: R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def sinal_str(valor: float) -> str:
    return "+" if valor >= 0 else ""

def cor_saldo(valor: float) -> str:
    return "#2ecc71" if valor >= 0 else "#e74c3c"

def cor_card(valor: float) -> str:
    return "card-verde" if valor >= 0 else "card-vermelho"

# ─────────────────────────────────────────
# COMPONENTES HTML REUTILIZÁVEIS
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
    """Reutilizável nas abas Início e Análises."""
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
    ultimo = df_valido.sort_values("data", ascending=False).iloc[0]
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

# ─────────────────────────────────────────
# LÓGICA FINANCEIRA
# ─────────────────────────────────────────
def calcular_saldo_individual(df: pd.DataFrame) -> dict:
    """
    Patrick: entradas 'Patrick só' − saídas ('Patrick só' + 'Patrick/Casal')
    Renata:  entradas 'Renata só'  − saídas ('Renata só'  + 'Renata/Casal')
    """
    entrada_patrick = df[(df["tipo"] == TIPO_ENTRADA) & (df["quem"] == "Patrick só")]["valor"].sum()
    entrada_renata  = df[(df["tipo"] == TIPO_ENTRADA) & (df["quem"] == "Renata só")]["valor"].sum()
    saida_patrick   = df[(df["tipo"] == TIPO_SAIDA) & (df["quem"].isin(["Patrick só", "Patrick/Casal"]))]["valor"].sum()
    saida_renata    = df[(df["tipo"] == TIPO_SAIDA) & (df["quem"].isin(["Renata só",  "Renata/Casal"]))]["valor"].sum()
    saida_casal     = df[(df["tipo"] == TIPO_SAIDA) & (df["quem"] == "Casal")]["valor"].sum()

    return {
        "entrada_patrick": entrada_patrick,
        "entrada_renata":  entrada_renata,
        "saida_patrick":   saida_patrick,
        "saida_renata":    saida_renata,
        "saida_casal":     saida_casal,
        "saldo_patrick":   entrada_patrick - saida_patrick,
        "saldo_renata":    entrada_renata  - saida_renata,
    }

# ─────────────────────────────────────────
# DADOS GLOBAIS
# ─────────────────────────────────────────
with st.spinner("Carregando dados..."):
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
        "Tipo:",
        [TIPO_ENTRADA, TIPO_SAIDA],
        horizontal=True,
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
                selecao = st.selectbox("Selecione o lançamento:", opcoes)
                idx         = opcoes.index(selecao)
                indice_real = df_sorted.index[idx]

                st.warning("⚠️ Esta ação é irreversível. Confirme apenas se tiver certeza.")
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
                "📅 Período:",
                ["Mês específico", "Todo o histórico"],
                horizontal=True
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

            # ── Saldo do período ──
            render_hero_card(
                f"Saldo · {label_periodo}",
                saldo,
                f"Entradas: {fmt_brl(entradas)} · Saídas: {fmt_brl(saidas)}"
            )

            # ── Saldo individual ──
            render_saldo_individual(saldo_ind)

            # ── Detalhamento individual ──
            st.markdown('<div class="section-title">📊 Detalhamento Individual</div>', unsafe_allow_html=True)
            cols = st.columns(2)
            with cols[0]:
                render_mini_card_duplo("👨‍💼", "Patrick",
                                       saldo_ind["entrada_patrick"],
                                       saldo_ind["saida_patrick"], "mc-blue")
            with cols[1]:
                render_mini_card_duplo("👩‍💼", "Renata",
                                       saldo_ind["entrada_renata"],
                                       saldo_ind["saida_renata"], "mc-purple")

            # ── Gastos "Casal" sem dono ──
            if saldo_ind["saida_casal"] > 0:
                st.markdown('<div class="section-title">💑 Gastos Casal (sem dono de conta)</div>', unsafe_allow_html=True)
                render_mini_card("💑", 'Saídas marcadas como "Casal"',
                                 saldo_ind["saida_casal"], "mc-orange")

            # ── Gastos para manter a casa ──
            st.markdown('<div class="section-title">🏠 Gastos para Manter a Casa</div>', unsafe_allow_html=True)

            gasto_patrick_casal = df_periodo[(df_periodo["tipo"] == TIPO_SAIDA) & (df_periodo["quem"] == "Patrick/Casal")]["valor"].sum()
            gasto_renata_casal  = df_periodo[(df_periodo["tipo"] == TIPO_SAIDA) & (df_periodo["quem"] == "Renata/Casal")]["valor"].sum()
            total_casa          = gasto_patrick_casal + gasto_renata_casal

            if total_casa > 0:
                pct_patrick = (gasto_patrick_casal / total_casa) * 100
                pct_renata  = (gasto_renata_casal  / total_casa) * 100

                render_hero_card(
                    "💑 Total gasto para manter a casa",
                    total_casa,
                    "Patrick/Casal + Renata/Casal"
                )

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
                    <div style="width:{pct_patrick:.1f}%; background:linear-gradient(135deg,#1a3a7b,#2e6da4);
                                display:flex; align-items:center; justify-content:center;
                                font-size:0.72rem; color:white; font-weight:700;">
                        {pct_patrick:.1f}%
                    </div>
                    <div style="width:{pct_renata:.1f}%; background:linear-gradient(135deg,#4a1a7b,#8e44ad);
                                display:flex; align-items:center; justify-content:center;
                                font-size:0.72rem; color:white; font-weight:700;">
                        {pct_renata:.1f}%
                    </div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#7f8c9a; margin-bottom:8px;">
                    <span>👨‍💼 Patrick</span><span>👩‍💼 Renata</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Nenhum gasto do tipo Patrick/Casal ou Renata/Casal no período.")

            # ── Gráfico pizza por categoria ──
            df_saidas = df_periodo[df_periodo["tipo"] == TIPO_SAIDA]
            if not df_saidas.empty:
                st.markdown('<div class="section-title">Gastos por Categoria</div>', unsafe_allow_html=True)
                cat_group = df_saidas.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
                fig = px.pie(
                    cat_group, values="valor", names="categoria", hole=0.45,
                    custom_data=["valor"]
                )
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate="<b>%{label}</b><br>R$ %{customdata[0]:,.2f}<extra></extra>"
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # ── Tabela de lançamentos ──
            st.markdown('<div class="section-title">Lançamentos</div>', unsafe_allow_html=True)
            total_registros = len(df_periodo)
            df_exibicao = df_periodo.sort_values("data", ascending=False).head(50).copy()
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
