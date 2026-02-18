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
ABA_INVESTIMENTOS = "Investimentos"
COLUNAS = ["data", "descricao", "categoria", "tipo", "valor", "quem"]
COLUNAS_INV = ["data", "categoria", "motivo", "tipo", "valor"]

CATEGORIAS_SAIDA = [
    "Mercado", "Contas Fixas", "Cartão de Crédito",
    "Lanche", "Lazer", "Gasolina", "Reparos",
    "Saúde", "Educação", "Outros"
]
CATEGORIAS_ENTRADA = ["Salário", "Freelance", "Outros"]
CATEGORIAS_INV = [
    "Renda Fixa", "Tesouro Direto", "Ações", "FIIs",
    "Criptomoedas", "CDB", "LCI/LCA", "Poupança", "Outros"
]
PESSOAS = ["Patrick", "Renata", "Nós dois"]

METAS_PADRAO = {
    "Mercado": 800.0,
    "Contas Fixas": 1500.0,
    "Cartão de Crédito": 1000.0,
    "Lanche": 200.0,
    "Lazer": 300.0,
    "Gasolina": 400.0,
    "Reparos": 200.0,
    "Saúde": 300.0,
    "Educação": 200.0,
    "Outros": 200.0
}

# ─────────────────────────────────────────
# CSS MOBILE FIRST
# ─────────────────────────────────────────
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
        }
        .stButton > button {
            width: 100%;
            padding: 0.8rem;
            font-size: 1.1rem;
            border-radius: 12px;
            font-weight: bold;
        }
        input, select, textarea {
            font-size: 1rem !important;
        }
        .card {
            background: linear-gradient(135deg, #1e3a5f, #2e6da4);
            border-radius: 16px;
            padding: 14px;
            text-align: center;
            color: white;
            margin-bottom: 10px;
        }
        .card h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; }
        .card h1 { margin: 4px 0; font-size: 1.5rem; }

        .card-verde {
            background: linear-gradient(135deg, #1a5c38, #27ae60);
            border-radius: 16px;
            padding: 14px;
            text-align: center;
            color: white;
            margin-bottom: 10px;
        }
        .card-verde h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; }
        .card-verde h1 { margin: 4px 0; font-size: 1.5rem; }

        .card-vermelho {
            background: linear-gradient(135deg, #7b1a1a, #e74c3c);
            border-radius: 16px;
            padding: 14px;
            text-align: center;
            color: white;
            margin-bottom: 10px;
        }
        .card-vermelho h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; }
        .card-vermelho h1 { margin: 4px 0; font-size: 1.5rem; }

        .card-roxo {
            background: linear-gradient(135deg, #4a1a7b, #8e44ad);
            border-radius: 16px;
            padding: 14px;
            text-align: center;
            color: white;
            margin-bottom: 10px;
        }
        .card-roxo h3 { margin: 0; font-size: 0.85rem; opacity: 0.85; }
        .card-roxo h1 { margin: 4px 0; font-size: 1.5rem; }

        /* Tabs menores no mobile */
        .stTabs [data-baseweb="tab"] {
            font-size: 0.85rem;
            padding: 8px 10px;
            font-weight: bold;
        }

        /* Gráficos menores no mobile */
        .js-plotly-plot {
            max-height: 280px;
        }

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
    # Aba Registro
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

    # Aba Investimentos
    result_inv = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{ABA_INVESTIMENTOS}!A1:E1"
    ).execute()
    if not result_inv.get('values'):
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_INVESTIMENTOS}!A1:E1",
            valueInputOption="RAW",
            body={"values": [COLUNAS_INV]}
        ).execute()

garantir_cabecalho()

@st.cache_data(ttl=60)
def ler_dados():
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

@st.cache_data(ttl=60)
def ler_investimentos():
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{ABA_INVESTIMENTOS}!A:E"
    ).execute()
    values = result.get('values', [])
    if len(values) > 1:
        df = pd.DataFrame(values[1:], columns=values[0])
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df
    return pd.DataFrame(columns=COLUNAS_INV)

def salvar_registro(data, descricao, categoria, tipo, valor, quem):
    novo = [[data.isoformat(), descricao, categoria, tipo, float(valor), quem]]
    try:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_NOME}!A:F",
            valueInputOption="RAW",
            body={"values": novo}
        ).execute()
        st.cache_data.clear()
    except Exception as e:
        raise RuntimeError(f"Falha ao salvar: {e}")

def salvar_investimento(data, categoria, motivo, tipo, valor):
    novo = [[data.isoformat(), categoria, motivo, tipo, float(valor)]]
    try:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_INVESTIMENTOS}!A:E",
            valueInputOption="RAW",
            body={"values": novo}
        ).execute()
        st.cache_data.clear()
    except Exception as e:
        raise RuntimeError(f"Falha ao salvar investimento: {e}")

def excluir_registro(indice_real, aba_id=0):
    linha = indice_real + 2
    requests = [{
        "deleteDimension": {
            "range": {
                "sheetId": aba_id,
                "dimension": "ROWS",
                "startIndex": linha - 1,
                "endIndex": linha
            }
        }
    }]
    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": requests}
        ).execute()
        st.cache_data.clear()
    except Exception as e:
        raise RuntimeError(f"Falha ao excluir: {e}")

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("## 💑 Patrick & Renata")
st.markdown("##### 💰 Controle Financeiro do Casal")
st.markdown("---")

# ─────────────────────────────────────────
# ABAS PRINCIPAIS
# ─────────────────────────────────────────
aba1, aba2, aba3, aba4 = st.tabs(["📝 Lançar", "📊 Análises", "📈 Investimentos", "🎯 Metas"])

# ══════════════════════════════════════════
# ABA 1 - LANÇAMENTOS
# ══════════════════════════════════════════
with aba1:

    st.markdown("### ➕ Novo Lançamento")

    tipo = st.radio("Tipo:", ["📈 Entrada", "📉 Saída"], horizontal=True)
    tipo_limpo = "Entrada" if "Entrada" in tipo else "Saída"

    data = st.date_input("📅 Data", value=dt.date.today())

    # Descrição com chave dinâmica para limpar após salvar
    if "desc_key" not in st.session_state:
        st.session_state["desc_key"] = 0

    descricao = st.text_input(
        "📝 Descrição",
        placeholder="Ex: Compra no mercado",
        key=f"descricao_{st.session_state['desc_key']}"
    )

    categorias = CATEGORIAS_ENTRADA if tipo_limpo == "Entrada" else CATEGORIAS_SAIDA
    categoria = st.selectbox("🏷️ Categoria", categorias)
    valor = st.number_input("💵 Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    quem = st.selectbox("👤 Quem?", PESSOAS)

    if valor > 0 and descricao:
        with st.expander("👁️ Pré-visualização"):
            st.markdown(f"""
            - 📅 **Data:** {data.strftime('%d/%m/%Y')}
            - 📝 **Descrição:** {descricao}
            - 🏷️ **Categoria:** {categoria}
            - 🔄 **Tipo:** {tipo_limpo}
            - 💵 **Valor:** R$ {valor:,.2f}
            - 👤 **Quem:** {quem}
            """)

    if st.button("💾 SALVAR LANÇAMENTO", type="primary"):
        if valor == 0:
            st.warning("⚠️ Coloque um valor maior que zero!")
        elif not descricao:
            st.warning("⚠️ Adicione uma descrição!")
        else:
            with st.spinner("Salvando..."):
                try:
                    salvar_registro(data, descricao, categoria, tipo_limpo, valor, quem)
                    st.session_state["desc_key"] += 1  # ← Limpa a descrição
                    st.balloons()
                    st.success(f"✅ {tipo_limpo} de R$ {valor:.2f} salva com sucesso!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.markdown("---")
    st.markdown("### 📋 Últimos Lançamentos")

    try:
        df = ler_dados()
        if not df.empty:
            df_sorted = df.sort_values("data", ascending=False).head(10).copy()
            df_sorted["data_fmt"] = df_sorted["data"].dt.strftime("%d/%m/%Y")
            df_sorted["valor_fmt"] = df_sorted["valor"].apply(lambda x: f"R$ {x:.2f}")
            df_show = df_sorted[["data_fmt", "descricao", "categoria", "tipo", "valor_fmt", "quem"]].rename(columns={
                "data_fmt": "Data", "descricao": "Descrição",
                "categoria": "Categoria", "tipo": "Tipo",
                "valor_fmt": "Valor", "quem": "Quem"
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            with st.expander("🗑️ Excluir um lançamento"):
                opcoes = [
                    f"{row['data_fmt']} | {row['descricao']} | R$ {row['valor']:.2f}"
                    for _, row in df_sorted.iterrows()
                ]
                selecao = st.selectbox("Selecione:", opcoes)
                idx_selecionado = opcoes.index(selecao)
                indice_real = df_sorted.index[idx_selecionado]
                if st.button("🗑️ CONFIRMAR EXCLUSÃO", type="secondary"):
                    with st.spinner("Excluindo..."):
                        try:
                            excluir_registro(indice_real, aba_id=0)
                            st.success("✅ Lançamento excluído!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
        else:
            st.info("📭 Nenhum lançamento ainda!")
    except Exception as e:
        st.error(f"Erro: {e}")

# ══════════════════════════════════════════
# ABA 2 - ANÁLISES (visual mobile premium)
# ══════════════════════════════════════════
with aba2:

    try:
        df = ler_dados()
        df_inv = ler_investimentos()

        if df.empty:
            st.info("📭 Sem dados ainda.")
        else:
            # ── FILTRO DE MÊS ──
            meses_disponiveis = df["data"].dt.to_period("M").dropna().unique()
            meses_str = sorted([str(m) for m in meses_disponiveis], reverse=True)
            mes_selecionado = st.selectbox("📅 Mês:", meses_str, key="mes_analise")
            df_mes = df[df["data"].dt.to_period("M").astype(str) == mes_selecionado]

            entradas = df_mes[df_mes["tipo"] == "Entrada"]["valor"].sum()
            saidas  = df_mes[df_mes["tipo"] == "Saída"]["valor"].sum()
            saldo   = entradas - saidas

            aportes_inv  = df_inv[df_inv["tipo"] == "Aporte"]["valor"].sum()  if not df_inv.empty else 0
            resgates_inv = df_inv[df_inv["tipo"] == "Resgate"]["valor"].sum() if not df_inv.empty else 0
            saldo_inv    = aportes_inv - resgates_inv

            # ── CSS EXTRA PARA ESTA ABA ──
            st.markdown("""
            <style>
                /* Seção título */
                .section-title {
                    font-size: 0.78rem;
                    font-weight: 700;
                    letter-spacing: 0.12em;
                    text-transform: uppercase;
                    color: #7f8c9a;
                    margin: 18px 0 8px 2px;
                }

                /* Card principal de saldo */
                .hero-card {
                    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
                    border-radius: 20px;
                    padding: 22px 18px 18px;
                    color: white;
                    margin-bottom: 14px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
                }
                .hero-card .label {
                    font-size: 0.75rem;
                    opacity: 0.65;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                    margin-bottom: 2px;
                }
                .hero-card .value {
                    font-size: 2.2rem;
                    font-weight: 800;
                    letter-spacing: -0.02em;
                    line-height: 1.1;
                }
                .hero-card .sub {
                    font-size: 0.78rem;
                    opacity: 0.55;
                    margin-top: 4px;
                }

                /* Mini cards (entrada / saída / investimento) */
                .mini-card {
                    border-radius: 16px;
                    padding: 14px 12px;
                    color: white;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
                }
                .mini-card .mc-label {
                    font-size: 0.72rem;
                    opacity: 0.75;
                    letter-spacing: 0.07em;
                    text-transform: uppercase;
                }
                .mini-card .mc-value {
                    font-size: 1.25rem;
                    font-weight: 800;
                    margin-top: 2px;
                    line-height: 1.1;
                }
                .mini-card .mc-icon {
                    font-size: 1.4rem;
                    margin-bottom: 4px;
                }
                .mc-green  { background: linear-gradient(135deg, #11723e, #27ae60); }
                .mc-red    { background: linear-gradient(135deg, #7b1a1a, #e74c3c); }
                .mc-purple { background: linear-gradient(135deg, #4a1a7b, #8e44ad); }
                .mc-blue   { background: linear-gradient(135deg, #1a3a7b, #2e6da4); }

                /* Divider com label */
                .divider-label {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin: 16px 0 10px;
                }
                .divider-label span {
                    font-size: 0.78rem;
                    font-weight: 700;
                    letter-spacing: 0.1em;
                    text-transform: uppercase;
                    color: #7f8c9a;
                    white-space: nowrap;
                }
                .divider-label hr {
                    flex: 1;
                    border: none;
                    border-top: 1px solid #e0e0e0;
                    margin: 0;
                }
            </style>
            """, unsafe_allow_html=True)

            # ── HERO CARD: SALDO DO MÊS ──
            sinal   = "+" if saldo >= 0 else ""
            cor_val = "#2ecc71" if saldo >= 0 else "#e74c3c"
            emoji_s = "😊" if saldo >= 0 else "😰"
            st.markdown(f"""
            <div class="hero-card">
                <div class="label">Saldo de {mes_selecionado}</div>
                <div class="value" style="color:{cor_val};">{sinal}R$ {saldo:,.2f}</div>
                <div class="sub">{emoji_s} {"Você está no positivo!" if saldo >= 0 else "Atenção: saldo negativo!"}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── MINI CARDS: ENTRADAS / SAÍDAS / INVEST ──
            st.markdown('<div class="section-title">Resumo do mês</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="mini-card mc-green">
                    <div class="mc-icon">💚</div>
                    <div class="mc-label">Entradas</div>
                    <div class="mc-value">R${entradas:,.0f}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="mini-card mc-red">
                    <div class="mc-icon">❤️</div>
                    <div class="mc-label">Saídas</div>
                    <div class="mc-value">R${saidas:,.0f}</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="mini-card mc-purple">
                    <div class="mc-icon">📈</div>
                    <div class="mc-label">Investido</div>
                    <div class="mc-value">R${saldo_inv:,.0f}</div>
                </div>""", unsafe_allow_html=True)

            # ── CARD INVESTIMENTOS DETALHADO ──
            st.markdown('<div class="section-title">Carteira de Investimentos</div>', unsafe_allow_html=True)
            ci1, ci2, ci3 = st.columns(3)
            with ci1:
                st.markdown(f"""
                <div class="mini-card mc-green">
                    <div class="mc-icon">💰</div>
                    <div class="mc-label">Aportes</div>
                    <div class="mc-value">R${aportes_inv:,.0f}</div>
                </div>""", unsafe_allow_html=True)
            with ci2:
                st.markdown(f"""
                <div class="mini-card mc-red">
                    <div class="mc-icon">💸</div>
                    <div class="mc-label">Resgates</div>
                    <div class="mc-value">R${resgates_inv:,.0f}</div>
                </div>""", unsafe_allow_html=True)
            with ci3:
                st.markdown(f"""
                <div class="mini-card mc-blue">
                    <div class="mc-icon">🏦</div>
                    <div class="mc-label">Saldo</div>
                    <div class="mc-value">R${saldo_inv:,.0f}</div>
                </div>""", unsafe_allow_html=True)

            # Distribuição por categoria de investimento
            if not df_inv.empty:
                df_ap = df_inv[df_inv["tipo"] == "Aporte"]
                if not df_ap.empty:
                    cat_inv = df_ap.groupby("categoria")["valor"].sum().reset_index()
                    fig_inv = px.pie(
                        cat_inv, values="valor", names="categoria",
                        hole=0.5
                    )
                    fig_inv.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        textfont_size=10
                    )
                    fig_inv.update_layout(
                        showlegend=False,
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=220
                    )
                    st.plotly_chart(fig_inv, use_container_width=True)

            # ── GRÁFICO PIZZA CATEGORIAS ──
            df_saidas_mes = df_mes[df_mes["tipo"] == "Saída"]
            if not df_saidas_mes.empty:
                st.markdown('<div class="section-title">Gastos por categoria</div>', unsafe_allow_html=True)
                cat_group = df_saidas_mes.groupby("categoria")["valor"].sum().reset_index()
                cat_group.columns = ["Categoria", "Valor"]
                cat_group = cat_group.sort_values("Valor", ascending=False)

                fig_pizza = px.pie(
                    cat_group, values="Valor", names="Categoria",
                    hole=0.45
                )
                fig_pizza.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    textfont_size=10
                )
                fig_pizza.update_layout(
                    showlegend=False,
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=240
                )
                st.plotly_chart(fig_pizza, use_container_width=True)

                # Top 3 categorias
                st.markdown('<div class="section-title">Top gastos</div>', unsafe_allow_html=True)
                top3 = cat_group.head(3)
                for i, row in top3.iterrows():
                    pct = row["Valor"] / saidas * 100 if saidas > 0 else 0
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center;
                                background:#f7f9fc; border-radius:12px; padding:10px 14px; margin-bottom:6px;">
                        <span style="font-weight:600; font-size:0.9rem;">🏷️ {row['Categoria']}</span>
                        <span style="font-weight:800; font-size:0.9rem; color:#2c5364;">R$ {row['Valor']:,.2f}
                            <span style="font-size:0.75rem; color:#7f8c9a; font-weight:400;">({pct:.0f}%)</span>
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

            # ── GRÁFICO HISTÓRICO ──
            st.markdown('<div class="section-title">Histórico mensal</div>', unsafe_allow_html=True)
            df_evolucao = (
                df.groupby([df["data"].dt.to_period("M"), "tipo"])["valor"]
                .sum().reset_index()
            )
            df_evolucao["data"] = df_evolucao["data"].astype(str)
            df_evolucao.columns = ["Mês", "Tipo", "Valor"]
            fig_hist = px.bar(
                df_evolucao, x="Mês", y="Valor", color="Tipo",
                barmode="group",
                color_discrete_map={"Entrada": "#27ae60", "Saída": "#e74c3c"}
            )
            fig_hist.update_layout(
                xaxis_title="", yaxis_title="R$",
                legend=dict(orientation="h", y=-0.3, title=""),
                margin=dict(t=10, b=10, l=10, r=10),
                height=230,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            fig_hist.update_xaxes(showgrid=False)
            fig_hist.update_yaxes(gridcolor="#f0f0f0")
            st.plotly_chart(fig_hist, use_container_width=True)

            # ── DIVISÃO POR PESSOA ──
            df_pessoa = df_mes[df_mes["tipo"] == "Saída"].groupby("quem")["valor"].sum()
            if not df_pessoa.empty:
                st.markdown('<div class="section-title">Gastos por pessoa</div>', unsafe_allow_html=True)
                p1, p2 = st.columns(2)
                with p1:
                    st.markdown(f"""
                    <div class="mini-card mc-blue">
                        <div class="mc-icon">👨</div>
                        <div class="mc-label">Patrick</div>
                        <div class="mc-value">R${df_pessoa.get('Patrick', 0):,.0f}</div>
                    </div>""", unsafe_allow_html=True)
                with p2:
                    st.markdown(f"""
                    <div class="mini-card mc-purple">
                        <div class="mc-icon">👩</div>
                        <div class="mc-label">Renata</div>
                        <div class="mc-value">R${df_pessoa.get('Renata', 0):,.0f}</div>
                    </div>""", unsafe_allow_html=True)
                nos = df_pessoa.get("Nós dois", 0)
                if nos > 0:
                    st.markdown(f"""
                    <div class="mini-card mc-blue">
                        <div class="mc-icon">💑</div>
                        <div class="mc-label">Nós dois</div>
                        <div class="mc-value">R${nos:,.0f}</div>
                    </div>""", unsafe_allow_html=True)

            # ── TABELA COMPACTA ──
            st.markdown('<div class="section-title">Lançamentos do mês</div>', unsafe_allow_html=True)
            df_show2 = df_mes.sort_values("data", ascending=False).copy()
            df_show2["data"] = df_show2["data"].dt.strftime("%d/%m")
            df_show2["valor"] = df_show2["valor"].apply(lambda x: f"R${x:.2f}")
            df_show2 = df_show2[["data", "descricao", "tipo", "valor"]].rename(columns={
                "data": "Data", "descricao": "Descrição",
                "tipo": "Tipo", "valor": "Valor"
            })
            st.dataframe(df_show2, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro: {e}")

# ══════════════════════════════════════════
# ABA 3 - INVESTIMENTOS
# ══════════════════════════════════════════
with aba3:

    st.markdown("### 📈 Investimentos")

    # Formulário de novo investimento
    st.markdown("#### ➕ Novo Registro")

    tipo_inv = st.radio("Tipo:", ["💰 Aporte", "💸 Resgate"], horizontal=True, key="tipo_inv")
    tipo_inv_limpo = "Aporte" if "Aporte" in tipo_inv else "Resgate"

    data_inv = st.date_input("📅 Data", value=dt.date.today(), key="data_inv")
    categoria_inv = st.selectbox("🏦 Categoria", CATEGORIAS_INV, key="cat_inv")

    if "motivo_key" not in st.session_state:
        st.session_state["motivo_key"] = 0

    motivo_inv = st.text_input(
        "📝 Motivo / Descrição",
        placeholder="Ex: Aporte mensal Tesouro Selic",
        key=f"motivo_{st.session_state['motivo_key']}"
    )
    valor_inv = st.number_input("💵 Valor (R$)", min_value=0.0, step=0.01, format="%.2f", key="valor_inv")

    if st.button("💾 SALVAR INVESTIMENTO", type="primary"):
        if valor_inv == 0:
            st.warning("⚠️ Coloque um valor maior que zero!")
        elif not motivo_inv:
            st.warning("⚠️ Adicione uma descrição!")
        else:
            with st.spinner("Salvando..."):
                try:
                    salvar_investimento(data_inv, categoria_inv, motivo_inv, tipo_inv_limpo, valor_inv)
                    st.session_state["motivo_key"] += 1  # ← Limpa o motivo
                    st.balloons()
                    st.success(f"✅ {tipo_inv_limpo} de R$ {valor_inv:.2f} salvo!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.markdown("---")

    # Resumo dos investimentos
    try:
        df_inv = ler_investimentos()

        if not df_inv.empty:
            aportes = df_inv[df_inv["tipo"] == "Aporte"]["valor"].sum()
            resgates = df_inv[df_inv["tipo"] == "Resgate"]["valor"].sum()
            saldo_inv = aportes - resgates

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='card-verde'><h3>💰 Aportes</h3><h1>R${aportes:,.0f}</h1></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='card-vermelho'><h3>💸 Resgates</h3><h1>R${resgates:,.0f}</h1></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='card-roxo'><h3>📊 Saldo</h3><h1>R${saldo_inv:,.0f}</h1></div>", unsafe_allow_html=True)

            st.markdown("---")

            # Gráfico por categoria de investimento
            st.markdown("#### 🏦 Aportes por Categoria")
            df_aportes = df_inv[df_inv["tipo"] == "Aporte"]
            if not df_aportes.empty:
                cat_inv_group = df_aportes.groupby("categoria")["valor"].sum().reset_index()
                fig_inv = px.pie(
                    cat_inv_group, values="valor", names="categoria",
                    hole=0.4
                )
                fig_inv.update_traces(textposition='inside', textinfo='percent+label', textfont_size=11)
                fig_inv.update_layout(
                    showlegend=False,
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=260
                )
                st.plotly_chart(fig_inv, use_container_width=True)

            st.markdown("---")

            # Histórico de investimentos
            st.markdown("#### 📋 Histórico")
            df_inv_show = df_inv.sort_values("data", ascending=False).copy()
            df_inv_show["data"] = df_inv_show["data"].dt.strftime("%d/%m/%Y")
            df_inv_show["valor"] = df_inv_show["valor"].apply(lambda x: f"R$ {x:.2f}")
            df_inv_show = df_inv_show.rename(columns={
                "data": "Data", "categoria": "Categoria",
                "motivo": "Motivo", "tipo": "Tipo", "valor": "Valor"
            })
            st.dataframe(df_inv_show, use_container_width=True, hide_index=True)

            # Exclusão
            with st.expander("🗑️ Excluir registro"):
                df_inv_sorted = df_inv.sort_values("data", ascending=False).copy()
                df_inv_sorted["data_fmt"] = df_inv_sorted["data"].dt.strftime("%d/%m/%Y")
                opcoes_inv = [
                    f"{row['data_fmt']} | {row['motivo']} | R$ {row['valor']:.2f}"
                    for _, row in df_inv_sorted.iterrows()
                ]
                sel_inv = st.selectbox("Selecione:", opcoes_inv, key="del_inv")
                idx_inv = opcoes_inv.index(sel_inv)
                indice_inv_real = df_inv_sorted.index[idx_inv]
                if st.button("🗑️ CONFIRMAR EXCLUSÃO", type="secondary", key="btn_del_inv"):
                    with st.spinner("Excluindo..."):
                        try:
                            excluir_registro(indice_inv_real, aba_id=1)  # aba_id=1 = segunda aba
                            st.success("✅ Registro excluído!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
        else:
            st.info("📭 Nenhum investimento registrado ainda!")

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
            st.info("📭 Sem dados ainda!")
        else:
            meses_disponiveis = df["data"].dt.to_period("M").dropna().unique()
            meses_str = sorted([str(m) for m in meses_disponiveis], reverse=True)
            mes_meta = st.selectbox("📅 Mês:", meses_str, key="mes_meta")
            df_mes_meta = df[df["data"].dt.to_period("M").astype(str) == mes_meta]

            st.markdown("#### 💰 Meta Global")
            meta_global = st.number_input(
                "🎯 Limite total (R$)",
                min_value=0.0, value=5000.0, step=100.0, format="%.2f"
            )
            saidas_total = df_mes_meta[df_mes_meta["tipo"] == "Saída"]["valor"].sum()
            prog_global = min(saidas_total / meta_global, 1.0) if meta_global > 0 else 0
            emoji_g = "✅" if prog_global < 0.75 else ("⚠️" if prog_global < 1.0 else "🚨")
            st.progress(prog_global, text=f"{emoji_g} R$ {saidas_total:,.2f} de R$ {meta_global:,.2f} ({prog_global*100:.1f}%)")

            st.markdown("---")
            st.markdown("#### 🏷️ Por Categoria")

            for cat in CATEGORIAS_SAIDA:
                gasto_cat = df_mes_meta[
                    (df_mes_meta["tipo"] == "Saída") & (df_mes_meta["categoria"] == cat)
                ]["valor"].sum()
                meta_cat = st.number_input(
                    f"{cat} (R$)", min_value=0.0,
                    value=METAS_PADRAO.get(cat, 200.0),
                    step=50.0, format="%.2f", key=f"meta_{cat}"
                )
                if meta_cat > 0:
                    prog = min(gasto_cat / meta_cat, 1.0)
                    emoji = "✅" if prog < 0.75 else ("⚠️" if prog < 1.0 else "🚨")
                    st.progress(prog, text=f"{emoji} {cat}: R$ {gasto_cat:,.2f} / R$ {meta_cat:,.2f} ({prog*100:.1f}%)")
                else:
                    st.caption(f"📊 {cat}: R$ {gasto_cat:,.2f} gastos")

    except Exception as e:
        st.error(f"Erro: {e}")
