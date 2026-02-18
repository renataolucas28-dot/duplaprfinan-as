import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    "Investimentos", "Saúde", "Educação", "Outros"
]
CATEGORIAS_ENTRADA = ["Salário", "Freelance", "Investimento", "Outros"]
PESSOAS = ["Patrick", "Renata", "Nós dois"]

# Metas padrão por categoria (podem ser editadas na aba Metas)
METAS_PADRAO = {
    "Mercado": 800.0,
    "Contas Fixas": 1500.0,
    "Cartão de Crédito": 1000.0,
    "Lanche": 200.0,
    "Lazer": 300.0,
    "Gasolina": 400.0,
    "Reparos": 200.0,
    "Investimentos": 500.0,
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
            padding: 16px;
            text-align: center;
            color: white;
            margin-bottom: 12px;
        }
        .card h3 { margin: 0; font-size: 0.9rem; opacity: 0.85; }
        .card h1 { margin: 4px 0; font-size: 1.8rem; }

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

        .stTabs [data-baseweb="tab"] {
            font-size: 1rem;
            padding: 10px 20px;
            font-weight: bold;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Barra de progresso de meta */
        .meta-ok { color: #27ae60; font-weight: bold; }
        .meta-alerta { color: #f39c12; font-weight: bold; }
        .meta-estouro { color: #e74c3c; font-weight: bold; }
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

# Chamada na inicialização, fora do cache
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

def salvar_registro(data, descricao, categoria, tipo, valor, quem):
    novo = [[
        data.isoformat(),
        descricao,
        categoria,
        tipo,
        float(valor),
        quem
    ]]
    try:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{ABA_NOME}!A:F",
            valueInputOption="RAW",
            body={"values": novo}
        ).execute()
        st.cache_data.clear()
    except Exception as e:
        raise RuntimeError(f"Falha ao salvar no Sheets: {e}")

def excluir_registro(indice_real):
    """
    Exclui uma linha da planilha pelo índice real (1-based, contando o cabeçalho).
    indice_real = índice no DataFrame + 2 (1 do cabeçalho + 1 do offset 0-based)
    """
    linha = indice_real + 2  # +1 cabeçalho, +1 offset
    requests = [{
        "deleteDimension": {
            "range": {
                "sheetId": 0,  # ID da primeira aba
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
        raise RuntimeError(f"Falha ao excluir linha: {e}")

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("## 💑 Patrick & Renata")
st.markdown("##### 💰 Controle Financeiro do Casal")
st.markdown("---")

# ─────────────────────────────────────────
# ABAS PRINCIPAIS
# ─────────────────────────────────────────
aba1, aba2, aba3 = st.tabs(["📝 Lançamentos", "📊 Análises", "🎯 Metas"])

# ══════════════════════════════════════════
# ABA 1 - LANÇAMENTOS
# ══════════════════════════════════════════
with aba1:

    st.markdown("### ➕ Novo Lançamento")

    tipo = st.radio("Tipo:", ["📈 Entrada", "📉 Saída"], horizontal=True)
    tipo_limpo = "Entrada" if "Entrada" in tipo else "Saída"

    data = st.date_input("📅 Data", value=dt.date.today())
    descricao = st.text_input("📝 Descrição", placeholder="Ex: Compra no mercado")

    categorias = CATEGORIAS_ENTRADA if tipo_limpo == "Entrada" else CATEGORIAS_SAIDA
    categoria = st.selectbox("🏷️ Categoria", categorias)

    valor = st.number_input("💵 Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    quem = st.selectbox("👤 Quem?", PESSOAS)

    # Preview antes de salvar
    if valor > 0 and descricao:
        with st.expander("👁️ Pré-visualização do lançamento"):
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
                    st.balloons()
                    st.success(f"✅ {tipo_limpo} de R$ {valor:.2f} salva com sucesso!")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # ── ÚLTIMOS LANÇAMENTOS COM EXCLUSÃO ──
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

            # Exclusão de lançamento
            with st.expander("🗑️ Excluir um lançamento"):
                opcoes = [
                    f"{row['data_fmt']} | {row['descricao']} | R$ {row['valor']:.2f}"
                    for _, row in df_sorted.iterrows()
                ]
                selecao = st.selectbox("Selecione o lançamento para excluir:", opcoes)
                idx_selecionado = opcoes.index(selecao)
                indice_real = df_sorted.index[idx_selecionado]

                if st.button("🗑️ CONFIRMAR EXCLUSÃO", type="secondary"):
                    with st.spinner("Excluindo..."):
                        try:
                            excluir_registro(indice_real)
                            st.success("✅ Lançamento excluído com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")
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

            # GRÁFICO DE PIZZA - GASTOS POR CATEGORIA
            st.markdown("#### 🏷️ Gastos por Categoria")
            df_saidas = df_mes[df_mes["tipo"] == "Saída"]
            if not df_saidas.empty:
                cat_group = df_saidas.groupby("categoria")["valor"].sum().reset_index()
                cat_group.columns = ["Categoria", "Valor"]

                fig_pizza = px.pie(
                    cat_group,
                    values="Valor",
                    names="Categoria",
                    title=f"Distribuição de Gastos — {mes_selecionado}",
                    hole=0.4
                )
                fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
                fig_pizza.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_pizza, use_container_width=True)

                # Tabela complementar
                cat_group_fmt = cat_group.copy()
                cat_group_fmt["Valor"] = cat_group_fmt["Valor"].apply(lambda x: f"R$ {x:.2f}")
                cat_group_fmt = cat_group_fmt.sort_values("Valor", ascending=False)
                st.dataframe(cat_group_fmt, use_container_width=True, hide_index=True)
            else:
                st.info("Sem saídas neste mês.")

            st.markdown("---")

            # GRÁFICO DE EVOLUÇÃO HISTÓRICA
            st.markdown("#### 📈 Evolução dos Últimos Meses")
            df_evolucao = (
                df.groupby([df["data"].dt.to_period("M"), "tipo"])["valor"]
                .sum()
                .reset_index()
            )
            df_evolucao["data"] = df_evolucao["data"].astype(str)
            df_evolucao.columns = ["Mês", "Tipo", "Valor"]

            if not df_evolucao.empty:
                fig_linha = px.bar(
                    df_evolucao,
                    x="Mês",
                    y="Valor",
                    color="Tipo",
                    barmode="group",
                    title="Entradas vs Saídas por Mês",
                    color_discrete_map={"Entrada": "#27ae60", "Saída": "#e74c3c"}
                )
                fig_linha.update_layout(
                    xaxis_title="Mês",
                    yaxis_title="R$",
                    legend_title="Tipo",
                    margin=dict(t=40, b=0, l=0, r=0)
                )
                st.plotly_chart(fig_linha, use_container_width=True)

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

                # Gráfico de barras por pessoa
                fig_pessoa = px.bar(
                    x=df_pessoa.index.tolist(),
                    y=df_pessoa.values.tolist(),
                    labels={"x": "Pessoa", "y": "R$"},
                    title="Gastos por Pessoa",
                    color=df_pessoa.index.tolist(),
                    color_discrete_sequence=["#2e6da4", "#e84393", "#f39c12"]
                )
                fig_pessoa.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_pessoa, use_container_width=True)

            st.markdown("---")

            # TODOS OS LANÇAMENTOS DO MÊS
            st.markdown("#### 📋 Todos os lançamentos do mês")
            df_show2 = df_mes.sort_values("data", ascending=False).copy()
            df_show2["data"] = df_show2["data"].dt.strftime("%d/%m")
            df_show2["valor"] = df_show2["valor"].apply(lambda x: f"R$ {x:.2f}")
            df_show2 = df_show2.rename(columns={
                "data": "Data", "descricao": "Descrição",
                "categoria": "Categoria", "tipo": "Tipo",
                "valor": "Valor", "quem": "Quem"
            })
            st.dataframe(df_show2, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro análise: {e}")

# ══════════════════════════════════════════
# ABA 3 - METAS
# ══════════════════════════════════════════
with aba3:

    st.markdown("### 🎯 Metas de Gastos por Categoria")
    st.caption("Defina o limite mensal para cada categoria e acompanhe o progresso.")

    try:
        df = ler_dados()

        if df.empty:
            st.info("📭 Sem dados ainda. Adicione lançamentos para ver as metas!")
        else:
            # Filtro de mês para as metas
            meses_disponiveis = df["data"].dt.to_period("M").dropna().unique()
            meses_str = sorted([str(m) for m in meses_disponiveis], reverse=True)
            mes_meta = st.selectbox("📅 Mês de referência:", meses_str, key="mes_meta")

            df_mes_meta = df[df["data"].dt.to_period("M").astype(str) == mes_meta]

            st.markdown("---")
            st.markdown("#### 💰 Meta Global do Mês")
            meta_global = st.number_input(
                "🎯 Limite total de gastos (R$)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                format="%.2f",
                key="meta_global"
            )
            saidas_total = df_mes_meta[df_mes_meta["tipo"] == "Saída"]["valor"].sum()
            progresso_global = min(saidas_total / meta_global, 1.0) if meta_global > 0 else 0

            cor_global = "meta-ok" if progresso_global < 0.75 else ("meta-alerta" if progresso_global < 1.0 else "meta-estouro")
            emoji_global = "✅" if progresso_global < 0.75 else ("⚠️" if progresso_global < 1.0 else "🚨")

            st.progress(progresso_global, text=f"{emoji_global} R$ {saidas_total:,.2f} de R$ {meta_global:,.2f} gastos ({progresso_global*100:.1f}%)")

            st.markdown("---")
            st.markdown("#### 🏷️ Metas por Categoria")

            for cat in CATEGORIAS_SAIDA:
                gasto_cat = df_mes_meta[
                    (df_mes_meta["tipo"] == "Saída") & (df_mes_meta["categoria"] == cat)
                ]["valor"].sum()

                meta_cat = st.number_input(
                    f"Meta — {cat} (R$)",
                    min_value=0.0,
                    value=METAS_PADRAO.get(cat, 200.0),
                    step=50.0,
                    format="%.2f",
                    key=f"meta_{cat}"
                )

                if meta_cat > 0:
                    prog = min(gasto_cat / meta_cat, 1.0)
                    emoji = "✅" if prog < 0.75 else ("⚠️" if prog < 1.0 else "🚨")
                    st.progress(prog, text=f"{emoji} {cat}: R$ {gasto_cat:,.2f} / R$ {meta_cat:,.2f} ({prog*100:.1f}%)")
                else:
                    st.caption(f"📊 {cat}: R$ {gasto_cat:,.2f} gastos (sem meta definida)")

    except Exception as e:
        st.error(f"Erro ao carregar metas: {e}")
