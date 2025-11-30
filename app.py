# app.py
import io
import re
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st

# --------------------------------------------------
# CONFIG GERAL / TEMA PRICETAX
# --------------------------------------------------
st.set_page_config(
    page_title="PRICETAX • IBS/CBS & Ranking SPED 2026",
    page_icon="💡",
    layout="wide",
)

PRIMARY_YELLOW = "#FFC300"
PRIMARY_BLACK = "#050608"
PRIMARY_CYAN = "#0EB8B3"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {PRIMARY_BLACK};
        color: #F5F5F5;
        font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Título principal */
    .pricetax-title {{
        font-size: 2.2rem;
        font-weight: 700;
        color: {PRIMARY_YELLOW};
    }}
    .pricetax-subtitle {{
        font-size: 0.98rem;
        color: #E0E0E0;
    }}

    /* Cards */
    .pricetax-card {{
        border-radius: 0.9rem;
        padding: 1.1rem 1.3rem;
        background: linear-gradient(135deg, #1C1C1C 0%, #101010 60%, #060608 100%);
        border: 1px solid #333333;
    }}
    .pricetax-card-soft {{
        border-radius: 0.9rem;
        padding: 1.1rem 1.3rem;
        background: #111318;
        border: 1px solid #2B2F3A;
    }}
    .pricetax-card-erro {{
        border-radius: 0.9rem;
        padding: 1.1rem 1.3rem;
        background: #2b1a1a;
        border: 1px solid #ff5656;
    }}

    /* Badges / chips */
    .pricetax-badge {{
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        background: {PRIMARY_YELLOW};
        color: {PRIMARY_BLACK};
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.18rem 0.7rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 500;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(15,15,18,0.9);
        color: #EDEDED;
    }}
    .pill-regime {{
        border-color: {PRIMARY_CYAN};
        background: rgba(14,184,179,0.08);
        color: #E5FEFC;
    }}
    .pill-tag {{
        background: rgba(0,0,0,0.4);
    }}

    /* Métricas */
    .pricetax-metric-label {{
        font-size: 0.78rem;
        color: #BBBBBB;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        border-bottom: 1px solid #333333;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: #EEEEEE;
    }}
    .stTabs [aria-selected="true"] p {{
        color: {PRIMARY_YELLOW} !important;
        font-weight: 600;
    }}

    /* Inputs */
    .stTextInput > div > div > input {{
        background-color: #111318;
        color: #FFFFFF;
        border-radius: 0.6rem;
        border: 1px solid #333333;
    }}
    .stFileUploader > label div {{
        color: #DDDDDD;
    }}

    /* Botão primário */
    .stButton>button[kind="primary"] {{
        background-color: #ff4d4d;
        color: #ffffff;
        border-radius: 0.6rem;
        border: 1px solid #ff8080;
        font-weight: 600;
    }}
    .stButton>button[kind="primary"]:hover {{
        background-color: #ff6666;
        border-color: #ff9999;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# FUNÇÕES UTILITÁRIAS
# --------------------------------------------------
def only_digits(s: Optional[str]) -> str:
    return re.sub(r"\D+", "", s or "")

def to_float_br(s) -> float:
    if not s:
        return 0.0
    s = str(s)
    # Remove separadores de milhar e troca vírgula por ponto
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return 0.0

def normalize_cols_upper(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

def pct_str(v: float) -> str:
    return f"{v:.2f}".replace(".", ",") + "%"

emoji_sim = "🔵"
emoji_nao = "🔴"

def badge_flag(v):
    v = str(v or "").strip().upper()
    return f"{emoji_sim} SIM" if v == "SIM" else f"{emoji_nao} NÃO"

def regime_label(regime: str) -> str:
    r = (regime or "").upper()
    mapping = {
        "ALIQ_ZERO_CESTA_BASICA_NACIONAL": "Alíquota zero • Cesta Básica Nacional",
        "ALIQ_ZERO_HORTIFRUTI_OVOS": "Alíquota zero • Hortifrúti e Ovos",
        "RED_60_ALIMENTOS": "Redução de 60% • Alimentos",
        "RED_60_ESSENCIALIDADE": "Redução de 60% • Essencialidade",
        "TRIBUTACAO_PADRAO": "Tributação padrão (sem benefício)",
    }
    return mapping.get(r, regime or "Regime não mapeado")

# --------------------------------------------------
# BASE TIPI → IBS/CBS (2026)
# --------------------------------------------------
TIPI_DEFAULT_NAME = "PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx"
ALT_TIPI_NAME = "TIPI_IBS_CBS_CLASSIFICADA_MIND7.xlsx"

@st.cache_data(show_spinner=False)
def load_tipi_base() -> pd.DataFrame:
    """
    Carrega a base PRICETAX refinada de classificação IBS/CBS por NCM.
    Procura primeiro PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx,
    depois TIPI_IBS_CBS_CLASSIFICADA_MIND7.xlsx.
    """
    paths = [
        Path(TIPI_DEFAULT_NAME),
        Path.cwd() / TIPI_DEFAULT_NAME,
        Path(ALT_TIPI_NAME),
        Path.cwd() / ALT_TIPI_NAME,
    ]
    try:
        paths.append(Path(__file__).parent / TIPI_DEFAULT_NAME)
        paths.append(Path(__file__).parent / ALT_TIPI_NAME)
    except:
        pass

    df = None
    for p in paths:
        if p.exists():
            df = pd.read_excel(p)
            break

    if df is None:
        return pd.DataFrame()

    df = normalize_cols_upper(df)
    if "NCM" not in df.columns:
        return pd.DataFrame()

    if "NCM_DIG" not in df.columns:
        df["NCM_DIG"] = df["NCM"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)

    # Preenche campos necessários com vazio caso não existam
    required = [
        "NCM_DESCRICAO", "REGIME_IVA_2026_FINAL", "FONTE_LEGAL_FINAL",
        "FLAG_ALIMENTO","FLAG_CESTA_BASICA","FLAG_HORTIFRUTI_OVOS","FLAG_RED_60",
        "FLAG_DEPENDE_DESTINACAO","IBS_UF_TESTE_2026_FINAL","IBS_MUN_TESTE_2026_FINAL",
        "CBS_TESTE_2026_FINAL","CST_IBSCBS"
    ]
    for c in required:
        if c not in df.columns:
            df[c] = ""
    return df

def buscar_ncm(df: pd.DataFrame, ncm_raw: str):
    n = only_digits(ncm_raw)
    if len(n) != 8 or df.empty:
        return None
    row = df.loc[df["NCM_DIG"] == n]
    return None if row.empty else row.iloc[0]

# --------------------------------------------------
# PARSER SPED – SOMENTE NOTAS DE SAÍDA (C100/C170)
# --------------------------------------------------
def parse_sped_saida(nome_arquivo: str, conteudo: str):
    notas = []
    itens = []

    current_nf = None

    for raw in conteudo.splitlines():
        if not raw or raw == "|":
            continue

        campos = raw.split("|")
        if len(campos) < 3:
            continue

        reg = campos[1].upper()

        # C100 – Cabeçalho
        if reg == "C100":
            # Campos: IND_OPER (2), COD_MOD(6), SER (7), NUM_DOC (8), DT_DOC (9), VL_DOC (12), CFOP (11)
            ind_oper = campos[2].strip()
            cod_mod  = campos[6].strip()
            serie    = campos[7].strip()
            numero   = campos[8].strip()
            dt_doc   = campos[9].strip()
            cfop_tot = campos[11].strip() if len(campos) > 11 else ""
            vl_doc   = campos[12].strip() if len(campos) > 12 else ""

            # Só processa saídas
            if ind_oper != "1":
                current_nf = None
                continue

            current_nf = {
                "ID_NF": f"{nome_arquivo}__{numero}_{serie}",
                "ARQUIVO": nome_arquivo,
                "COD_MOD": cod_mod,
                "SERIE": serie,
                "NUMERO": numero,
                "DT_DOC": dt_doc,
                "CFOP_DOC": cfop_tot,
                "VL_DOC": to_float_br(vl_doc),
            }
            notas.append(current_nf)

        # C170 – Itens da NF
        elif reg == "C170" and current_nf:
            # Campos: NUM_ITEM(2), COD_ITEM(3), DESCR_COMPL(4), QTD(5), VL_ITEM(7), CFOP(11), NCM(8)
            qtd = to_float_br(campos[5]) if len(campos) > 5 else 0.0
            vl_item = to_float_br(campos[7]) if len(campos) > 7 else 0.0
            cfop   = campos[11].strip() if len(campos) > 11 else ""
            ncm    = campos[8].strip() if len(campos) > 8 else ""
            descr  = campos[4].strip() if len(campos) > 4 else ""

            itens.append({
                "ID_NF": current_nf["ID_NF"],
                "CFOP": cfop,
                "DT_DOC": current_nf["DT_DOC"],
                "NCM": only_digits(ncm),
                "DESCR_ITEM": descr,
                "QTD": qtd,
                "VL_ITEM": vl_item,
                "VL_TOTAL_ITEM": qtd * vl_item,
            })

    return itens

# --------------------------------------------------
# PROCESSAMENTO SPED – CONSOLIDAÇÃO E RANKING
# --------------------------------------------------
def processar_speds_vendas(files, df_tipi):
    """
    Lê múltiplos arquivos SPED Contribuições (.txt ou .zip),
    extrai notas de saída (C100) e itens (C170),
    cruza com a base TIPI para IBS/CBS 2026 e retorna:
       - df_itens_detalhado
       - df_ranking_produtos
       - df_erros (NCM sem correspondência)
    """
    itens_all = []

    for up in files:
        nome = up.name
        if nome.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(up.read()), "r") as z:
                for info in z.infolist():
                    if info.filename.lower().endswith(".txt"):
                        conteudo = z.open(info).read().decode("utf-8", errors="replace")
                        itens = parse_sped_saida(info.filename, conteudo)
                        itens_all.extend(itens)
        else:
            conteudo = up.read().decode("utf-8", errors="replace")
            itens = parse_sped_saida(nome, conteudo)
            itens_all.extend(itens)

    if not itens_all:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_itens = pd.DataFrame(itens_all)

    # Normaliza NCM
    df_itens["NCM_DIG"] = (
        df_itens["NCM"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)
    )

    # Cruza com TIPI
    df_merged = df_itens.merge(
        df_tipi,
        how="left",
        left_on="NCM_DIG",
        right_on="NCM_DIG",
    )

    # Erros: NCM não encontrado
    df_erros = df_merged[df_merged["NCM_DESCRICAO"].isna()][
        ["NCM_DIG", "DESCR_ITEM", "CFOP", "VL_TOTAL_ITEM"]
    ]

    df_validos = df_merged[df_merged["NCM_DESCRICAO"].notna()].copy()

    # Calcula alíquotas efetivas
    df_validos["IBS_UF"]  = pd.to_numeric(df_validos["IBS_UF_TESTE_2026_FINAL"], errors="coerce").fillna(0)
    df_validos["IBS_MUN"] = pd.to_numeric(df_validos["IBS_MUN_TESTE_2026_FINAL"], errors="coerce").fillna(0)
    df_validos["CBS"]     = pd.to_numeric(df_validos["CBS_TESTE_2026_FINAL"], errors="coerce").fillna(0)

    df_validos["IBS_EFETIVO"] = df_validos["IBS_UF"] + df_validos["IBS_MUN"]
    df_validos["TOTAL_IVA_2026"] = df_validos["IBS_EFETIVO"] + df_validos["CBS"]

    # Ranking por produto
    df_ranking = (
        df_validos.groupby([
            "NCM_DIG", "NCM_DESCRICAO", "CFOP", "REGIME_IVA_2026_FINAL",
            "FLAG_CESTA_BASICA", "FLAG_HORTIFRUTI_OVOS", "FLAG_RED_60"
        ])
        .agg(
            FATURAMENTO_TOTAL=("VL_TOTAL_ITEM", "sum"),
            QTD_TOTAL=("QTD", "sum"),
            NOTAS_QTD=("ID_NF", "nunique"),
        )
        .reset_index()
        .sort_values("FATURAMENTO_TOTAL", ascending=False)
    )

    # Ordena detalhados
    df_validos = df_validos.sort_values(["DT_DOC", "ID_NF"])
    return df_validos, df_ranking, df_erros

# --------------------------------------------------
# CABEÇALHO E TABS
# --------------------------------------------------
st.markdown(
    """
    <div class="pricetax-title">PRICETAX • IBS/CBS 2026 & Ranking SPED</div>
    <div class="pricetax-subtitle">
        Consulte o NCM do seu produto e analise suas vendas pelo SPED já com a tributação IBS/CBS 2026 simulada.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")
tabs = st.tabs([
    "🔍 Consulta NCM → IBS/CBS 2026",
    "📊 Ranking de Produtos (via SPED) – IBS/CBS 2026",
])

# ==================================================
# TABELA TIPI CARREGADA
# ==================================================
df_tipi = load_tipi_base()

# ==================================================
# TAB 1 – CONSULTA NCM
# ==================================================
with tabs[0]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Consulta de produtos</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Informe o código NCM do seu produto e veja a tributação de IBS e CBS simulada para 2026,
                conforme a EC 132/2023 e a LC 214/2025.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    col1, col2 = st.columns([3, 1])
    with col1:
        ncm_input = st.text_input("Informe o NCM (com ou sem pontos)", placeholder="Ex.: 16023220 ou 16.02.32.20")
    with col2:
        st.write("")
        consultar = st.button("Consultar", type="primary")

    if consultar and ncm_input.strip():
        row = buscar_ncm(df_tipi, ncm_input)

        if row is None:
            st.markdown(
                f"""
                <div class="pricetax-card-erro" style="margin-top:0.8rem;">
                    NCM: <b>{ncm_input}</b><br>
                    Não encontramos esse NCM na base PRICETAX. Verifique o código informado.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            ncm_fmt = row["NCM_DIG"]
            desc    = row["NCM_DESCRICAO"]

            regime   = row["REGIME_IVA_2026_FINAL"]
            fonte    = row["FONTE_LEGAL_FINAL"]

            flag_cesta = row["FLAG_CESTA_BASICA"]
            flag_hf    = row["FLAG_HORTIFRUTI_OVOS"]
            flag_red   = row["FLAG_RED_60"]
            flag_alim  = row["FLAG_ALIMENTO"]
            flag_dep   = row["FLAG_DEPENDE_DESTINACAO"]

            ibs_uf  = to_float_br(row["IBS_UF_TESTE_2026_FINAL"])
            ibs_mun = to_float_br(row["IBS_MUN_TESTE_2026_FINAL"])
            cbs     = to_float_br(row["CBS_TESTE_2026_FINAL"])

            total_iva = ibs_uf + ibs_mun + cbs

            cst_ibscbs = row.get("CST_IBSCBS", "")

            # CARD PRINCIPAL
            st.markdown(
                f"""
                <div class="pricetax-card" style="margin-top:1rem;">
                    <div style="font-size:1.1rem;font-weight:600;color:{PRIMARY_YELLOW};">
                        NCM {ncm_fmt} – {desc}
                    </div>
                    <div style="margin-top:0.5rem;">
                        <span class="pill pill-regime">{regime_label(regime)}</span>
                        &nbsp; <span class="pill pill-tag">Cesta Básica: {badge_flag(flag_cesta)}</span>
                        &nbsp; <span class="pill pill-tag">Hortifrúti/Ovos: {badge_flag(flag_hf)}</span>
                        &nbsp; <span class="pill pill-tag">Redução 60%: {badge_flag(flag_red)}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # MÉTRICAS
            st.markdown(
                f"""
                <div class="pricetax-card" style="margin-top:1rem;display:flex;gap:2rem;">
                    <div>
                        <div class="pricetax-metric-label">IBS 2026 (UF+Mun)</div>
                        <div style="font-size:2.4rem;color:{PRIMARY_YELLOW};">{pct_str(ibs_uf + ibs_mun)}</div>
                    </div>
                    <div>
                        <div class="pricetax-metric-label">CBS 2026</div>
                        <div style="font-size:2.4rem;color:{PRIMARY_YELLOW};">{pct_str(cbs)}</div>
                    </div>
                    <div>
                        <div class="pricetax-metric-label">TOTAL IVA 2026</div>
                        <div style="font-size:2.4rem;color:{PRIMARY_YELLOW};">{pct_str(total_iva)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Parametrizações
            st.subheader("Parâmetros de classificação", divider="gray")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown("**Produto é alimento?**")
                st.markdown(f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_alim)}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown("**Cesta Básica Nacional (CeNA)?**")
                st.markdown(f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_cesta)}</span>", unsafe_allow_html=True)
            with c3:
                st.markdown("**Hortifrúti / Ovos?**")
                st.markdown(f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_hf)}</span>", unsafe_allow_html=True)
            with c4:
                st.markdown("**Depende de destinação?**")
                st.markdown(f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_dep)}</span>", unsafe_allow_html=True)

            c5, c6 = st.columns(2)
            with c5:
                st.markdown("**CST IBS/CBS (venda)**")
                st.markdown(f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{cst_ibscbs or '—'}</span>", unsafe_allow_html=True)
            with c6:
                st.markdown("**Imposto Seletivo (IS)**")
                flag_is = row.get("FLAG_IMPOSTO_SELETIVO", "")
                st.markdown(f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_is)}</span>", unsafe_allow_html=True)

            # Observações e base legal
            st.markdown("---")
            # Ajusta alertas e observações
            def clean_txt(v):
                s = str(v or "").strip()
                return "" if s.lower() == "nan" else s

            alerta_fmt = clean_txt(row.get("ALERTA_APP"))
            obs_alim   = clean_txt(row.get("OBS_ALIMENTO"))
            obs_dest   = clean_txt(row.get("OBS_DESTINACAO"))
            reg_extra  = clean_txt(row.get("OBS_REGIME_ESPECIAL"))

            # Se regime tem redução 60% e não há textos, define padrão
            if "RED_60" in (regime or "").upper():
                if not alerta_fmt:
                    alerta_fmt = "Redução de 60% aplicada; conferir aderência ao segmento e às condições legais."
                if not reg_extra:
                    reg_extra = (
                        "Ano teste 2026 – IBS 0,1% (UF) e CBS 0,9%. "
                        "Carga reduzida em 60% conforme regras de essencialidade/alimentos."
                    )

            st.markdown(f"**Base legal aplicada:** {fonte or '—'}")
            st.markdown(f"**Alerta PRICETAX:** {alerta_fmt or '—'}")
            st.markdown(f"**Observação sobre alimentos:** {obs_alim or '—'}")
            st.markdown(f"**Observação sobre destinação:** {obs_dest or '—'}")
            st.markdown(f"**Regime especial / motivo adicional:** {reg_extra or '—'}")

# ==================================================
# TAB 2 – RANKING DE PRODUTOS (SAÍDAS SPED)
# ==================================================
with tabs[1]:

    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Análise de Vendas (Saídas SPED)</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Faça upload de arquivos SPED Contribuições (<b>.txt</b> ou <b>.zip</b>). O sistema irá:
                <br><br>
                • Ler todas as notas de <b>saída</b> (C100/C170)<br>
                • Consolidar produtos por CFOP + NCM + Descrição<br>
                • Gerar ranking de faturamento<br>
                • Cruzar cada item com a base PRICETAX IBS/CBS 2026<br>
                • Exibir alíquotas IBS/CBS simuladas para 2026
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Selecione arquivos SPED Contribuições (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
        key="sped_upload_rank",
    )

    if uploaded:
        if st.button("Processar SPED e Gerar Ranking", type="primary"):
            with st.spinner("Processando SPED, extraindo notas de saída e cruzando com tabelas PRICETAX..."):
                df_itens, df_ranking, df_erros = processar_speds_vendas(uploaded, df_tipi)

            if df_itens.empty:
                st.error("Nenhuma nota de saída foi encontrada nos arquivos fornecidos.")
            else:
                st.success("Processamento concluído!")
                st.markdown("---")

                # Função para gerar Excel em memória
                def to_excel(df):
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        df.to_excel(w, index=False)
                    buf.seek(0)
                    return buf

                # Botões de download
                colA, colB, colC = st.columns(3)
                with colA:
                    st.download_button(
                        "📥 Baixar Itens Detalhados (C170 + IVA 2026)",
                        data=to_excel(df_itens),
                        file_name="PRICETAX_Itens_Detalhados_2026.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                with colB:
                    st.download_button(
                        "📥 Baixar Ranking de Produtos",
                        data=to_excel(df_ranking),
                        file_name="PRICETAX_Ranking_Produtos_2026.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                with colC:
                    st.download_button(
                        "📥 Baixar Erros de NCM",
                        data=to_excel(df_erros),
                        file_name="PRICETAX_Erros_NCM.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                st.markdown("---")

                # Mostra ranking no app (Top 20)
                st.subheader("Ranking de Produtos – Top 20", divider="gray")
                st.dataframe(
                    df_ranking.head(20)[[
                        "NCM_DIG", "NCM_DESCRICAO", "CFOP",
                        "FATURAMENTO_TOTAL", "QTD_TOTAL", "NOTAS_QTD",
                        "REGIME_IVA_2026_FINAL",
                        "FLAG_CESTA_BASICA", "FLAG_HORTIFRUTI_OVOS", "FLAG_RED_60"
                    ]],
                    use_container_width=True,
                )

                # Insight rápido
                total_fat = df_itens["VL_TOTAL_ITEM"].sum()
                total_notas = df_itens["ID_NF"].nunique()

                st.markdown(
                    f"""
                    <div class="pricetax-card-soft" style="margin-top:1rem;">
                        <div style="font-size:1rem;color:{PRIMARY_YELLOW};font-weight:600;">📊 Insight PRICETAX</div>
                        <div style="margin-top:0.4rem;font-size:0.9rem;color:#E0E0E0;">
                            • Faturamento total analisado: <b>R$ {total_fat:,.2f}</b><br>
                            • Total de notas fiscais na análise: <b>{total_notas}</b><br>
                            • Ranking baseado em CFOP + NCM + Descrição, cruzado com IVA 2026<br>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Nenhum arquivo enviado ainda. Selecione um ou mais SPEDs para iniciar a análise.")
