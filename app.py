import io
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st
import altair as alt

# --------------------------------------------------
# CONFIG GERAL / TEMA PRICETAX
# --------------------------------------------------
st.set_page_config(
    page_title="PRICETAX • IBS/CBS 2026 & Ranking SPED",
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
    /* Títulos */
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
    /* Badges e chips */
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
    /* Botão primário - azul ciano */
    .stButton>button[kind="primary"] {{
        background-color: {PRIMARY_CYAN};
        color: #ffffff;
        border-radius: 0.6rem;
        border: 1px solid {PRIMARY_CYAN};
        font-weight: 600;
    }}
    .stButton>button[kind="primary"]:hover {{
        background-color: #15d0c9;
        border-color: #4fe0dc;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# UTILITÁRIOS
# --------------------------------------------------
def only_digits(s: Optional[str]) -> str:
    return re.sub(r"\D+", "", s or "")

def to_float_br(s) -> float:
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def competencia_from_dt(dt_ini: str, dt_fin: str) -> str:
    for raw in (dt_ini or "", dt_fin or ""):
        dig = only_digits(raw)
        if len(dig) == 8:
            return f"{dig[2:4]}/{dig[4:8]}"
    return ""

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

def normalize_cst_key(cst_val: Any) -> str:
    s = re.sub(r"\D+", "", str(cst_val or "").strip())
    if s == "":
        return ""
    # remove zeros à esquerda
    try:
        return str(int(s))
    except Exception:
        return s

# --------------------------------------------------
# CARREGAR BASE TIPI (PLANILHA PRICETAX / MIND7)
# --------------------------------------------------
TIPI_DEFAULT_NAME = "PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx"
ALT_TIPI_NAME = "TIPI_IBS_CBS_CLASSIFICADA_MIND7.xlsx"

@st.cache_data(show_spinner=False)
def load_tipi_base() -> pd.DataFrame:
    paths = [
        Path(TIPI_DEFAULT_NAME), Path.cwd() / TIPI_DEFAULT_NAME,
        Path(ALT_TIPI_NAME), Path.cwd() / ALT_TIPI_NAME,
    ]
    try:
        paths.append(Path(__file__).parent / TIPI_DEFAULT_NAME)
        paths.append(Path(__file__).parent / ALT_TIPI_NAME)
    except Exception:
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

    required = [
        "NCM_DESCRICAO", "REGIME_IVA_2026_FINAL", "FONTE_LEGAL_FINAL",
        "FLAG_ALIMENTO","FLAG_CESTA_BASICA","FLAG_HORTIFRUTI_OVOS","FLAG_RED_60",
        "FLAG_DEPENDE_DESTINACAO","IBS_UF_TESTE_2026_FINAL","IBS_MUN_TESTE_2026_FINAL",
        "CBS_TESTE_2026_FINAL","CST_IBSCBS","ALERTA_APP","OBS_ALIMENTO",
        "OBS_DESTINACAO","OBS_REGIME_ESPECIAL","FLAG_IMPOSTO_SELETIVO"
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
    return None if row.empty or row.isnull().all().all() else row.iloc[0]

df_tipi = load_tipi_base()

# --------------------------------------------------
# CARREGAR BASE CLASSIFICAÇÃO TRIBUTÁRIA (CST -> cClassTrib)
# --------------------------------------------------
CLASSIF_NAME = "classificacao_tributaria.xlsx"

@st.cache_data(show_spinner=False)
def load_classificacao_base() -> pd.DataFrame:
    paths = [
        Path(CLASSIF_NAME), Path.cwd() / CLASSIF_NAME,
    ]
    try:
        paths.append(Path(__file__).parent / CLASSIF_NAME)
    except Exception:
        pass

    df = None
    for p in paths:
        if p.exists():
            df = pd.read_excel(p, sheet_name="Classificação Tributária")
            break

    if df is None:
        return pd.DataFrame()

    # normaliza CST_KEY
    df = df.copy()
    df["CST_KEY"] = df["Código da Situação Tributária"].apply(normalize_cst_key)

    # Normaliza campos Sim/Não para evitar ruído
    for col in [
        "Tributação Regular",
        "Redução de Alíquota",
        "Transferência de Crédito",
        "Diferimento",
        "Monofásica",
        "NFe",
    ]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    return df

@st.cache_data(show_spinner=False)
def build_cclasstrib_index(df_class: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """
    Cria um índice: CST_KEY -> cenário padrão de cClassTrib para NFe,
    seguindo a regra que combinamos:
    - NFe == "Sim"
    - Tributação Regular == "Sim"
    - Redução de Alíquota == "Não"
    - Transferência de Crédito == "Não"
    - Diferimento == "Não"
    Se não achar com todos esses filtros, relaxa a regra (NFe Sim, depois sem filtro).
    """
    index: Dict[str, Dict[str, str]] = {}
    if df_class.empty:
        return index

    for cst_key, grp in df_class.groupby("CST_KEY"):
        if not cst_key:
            continue

        g = grp.copy()

        # 1) prioriza NFe = Sim
        if "NFe" in g.columns:
            g_pref = g[g["NFe"].str.lower() == "sim"]
            if not g_pref.empty:
                g = g_pref

        # 2) prioriza cenário regular sem redução, sem transferência, sem diferimento
        for col in [
            "Tributação Regular",
            "Redução de Alíquota",
            "Transferência de Crédito",
            "Diferimento",
        ]:
            if col not in g.columns:
                g[col] = ""

        mask_reg = (
            (g["Tributação Regular"].str.lower() == "sim")
            & (g["Redução de Alíquota"].str.lower() == "não")
            & (g["Transferência de Crédito"].str.lower() == "não")
            & (g["Diferimento"].str.lower() == "não")
        )
        g_reg = g[mask_reg]
        if not g_reg.empty:
            g = g_reg

        # 3) escolhe a linha com menor Código da Classificação Tributária (para desempate)
        def class_code_val(x):
            try:
                # tenta float, depois int, se der ruim joga lá pra cima
                s = str(x).replace(",", ".")
                return float(s)
            except Exception:
                try:
                    return int(str(x).strip())
                except Exception:
                    return 999999999

        if "Código da Classificação Tributária" in g.columns:
            best_idx = min(
                g.index,
                key=lambda i: class_code_val(g.loc[i, "Código da Classificação Tributária"]),
            )
            row = g.loc[best_idx]
        else:
            row = g.iloc[0]

        index[cst_key] = {
            "COD_CLASS": str(row.get("Código da Classificação Tributária", "")).strip(),
            "DESC_CLASS": str(row.get("Descrição do Código da Classificação Tributária", "")).strip(),
            "TIPO_ALIQUOTA": str(row.get("Tipo de Alíquota", "")).strip(),
            "TRIB_REG": str(row.get("Tributação Regular", "")).strip(),
            "RED_ALIQ": str(row.get("Redução de Alíquota", "")).strip(),
            "TRANSF_CRED": str(row.get("Transferência de Crédito", "")).strip(),
            "DIFERIMENTO": str(row.get("Diferimento", "")).strip(),
            "MONOFASICA": str(row.get("Monofásica", "")).strip(),
            "URL_LEI": str(row.get("Url da Legislação", "")).strip(),
        }

    return index

df_class = load_classificacao_base()
cclasstrib_index = build_cclasstrib_index(df_class)

def get_cclasstrib_for_cst(cst_ibscbs: Any) -> Optional[Dict[str, str]]:
    key = normalize_cst_key(cst_ibscbs)
    if not key:
        return None
    return cclasstrib_index.get(key)

# --------------------------------------------------
# PROCESSADOR SPED – RANKING DE SAÍDAS (C100/C170, CFOP 5/6/7)
# --------------------------------------------------
def process_sped_file(file_content: str) -> pd.DataFrame:
    """
    Processa o conteúdo do arquivo SPED PIS/COFINS para extrair dados de vendas.
    Retorna um DataFrame com colunas: NCM, DESCRICAO, CFOP, VALOR_TOTAL_VENDAS.
    """
    produtos = {}   # {COD_ITEM: {'NCM': NCM, 'DESCR_ITEM': DESCR_ITEM}}
    documentos = {} # {CHAVE_DOC: {'IND_OPER': '1'}}
    itens_venda = []

    cfop_saida_pattern = re.compile(r'^[567]\d{3}$')
    current_doc_key = None

    try:
        file_stream = io.StringIO(file_content)

        for line in file_stream:
            fields = line.strip().split('|')
            if not fields or len(fields) < 2:
                continue

            registro = fields[1]

            if registro == '0200':
                # |0200|COD_ITEM|DESCR_ITEM|...|COD_NCM(8)|...
                if len(fields) >= 9:
                    cod_item = fields[2]
                    descr_item = fields[3]
                    cod_ncm = fields[8]
                    produtos[cod_item] = {'NCM': cod_ncm, 'DESCR_ITEM': descr_item}

            elif registro == 'C100':
                # IMPORTANTE: layout EFD Contribuições – ajustar se necessário
                ind_oper = fields[2] if len(fields) > 2 else ''
                if ind_oper == '1':  # Saída
                    chv_nfe = fields[9] if len(fields) > 9 else ''
                    ser = fields[6] if len(fields) > 6 else ''
                    num_doc = fields[7] if len(fields) > 7 else ''

                    if chv_nfe:
                        current_doc_key = chv_nfe
                    elif ser and num_doc:
                        current_doc_key = f"{ser}-{num_doc}"
                    else:
                        current_doc_key = None

                    if current_doc_key:
                        documentos[current_doc_key] = {'IND_OPER': ind_oper}
                else:
                    current_doc_key = None

            elif (
                registro == 'C170'
                and current_doc_key
                and documentos.get(current_doc_key, {}).get('IND_OPER') == '1'
            ):
                # |C170|NUM_ITEM|COD_ITEM(3)|DESCR_COMPL|QTD|UNID|VL_ITEM(7)|...|CFOP(11)|...
                if len(fields) >= 12:
                    cod_item = fields[3]
                    vl_item_str = fields[7].replace(',', '.')
                    cfop = fields[11]

                    try:
                        vl_item = float(vl_item_str)
                    except ValueError:
                        continue

                    if cfop_saida_pattern.match(cfop):
                        itens_venda.append(
                            {
                                'COD_ITEM': cod_item,
                                'VL_ITEM': vl_item,
                                'CFOP': cfop,
                                'DOC_KEY': current_doc_key,
                            }
                        )

            elif registro in ('C190', 'C300', 'D100', 'E100'):
                current_doc_key = None

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return pd.DataFrame()

    # Agregação
    ranking_vendas = defaultdict(
        lambda: {'NCM': '', 'DESCR_ITEM': '', 'CFOP': '', 'TOTAL_VENDAS': 0.0}
    )

    for item in itens_venda:
        cod_item = item['COD_ITEM']
        vl_item = item['VL_ITEM']
        cfop = item['CFOP']

        produto_info = produtos.get(cod_item)
        if produto_info:
            ncm = produto_info['NCM']
            descr_item = produto_info['DESCR_ITEM']

            chave = (ncm, descr_item, cfop)
            ranking_vendas[chave]['NCM'] = ncm
            ranking_vendas[chave]['DESCR_ITEM'] = descr_item
            ranking_vendas[chave]['CFOP'] = cfop
            ranking_vendas[chave]['TOTAL_VENDAS'] += vl_item

    relatorio = []
    for chave, dados in ranking_vendas.items():
        relatorio.append(
            {
                'NCM': dados['NCM'],
                'DESCRICAO': dados['DESCR_ITEM'],
                'VALOR_TOTAL_VENDAS': dados['TOTAL_VENDAS'],
                'CFOP': dados['CFOP'],
            }
        )

    if not relatorio:
        return pd.DataFrame(columns=["NCM", "DESCRICAO", "CFOP", "VALOR_TOTAL_VENDAS"])

    df = pd.DataFrame(relatorio)
    df = df.sort_values("VALOR_TOTAL_VENDAS", ascending=False).reset_index(drop=True)
    return df

# --------------------------------------------------
# CABEÇALHO / TABS
# --------------------------------------------------
st.markdown(
    """
    <div class="pricetax-title">PRICETAX • IBS/CBS 2026 & Ranking SPED</div>
    <div class="pricetax-subtitle">
        Consulte o NCM do seu produto e gere o ranking de saídas pelo SPED PIS/COFINS com visão IBS/CBS + cClassTrib para 2026.
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "🔍 Consulta NCM → IBS/CBS 2026 + cClassTrib",
    "📊 Ranking de Saídas (SPED PIS/COFINS → IBS/CBS + cClassTrib)",
])

# --------------------------------------------------
# ABA 1 – CONSULTA NCM (com cClassTrib para XML)
# --------------------------------------------------
with tabs[0]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Consulta de produtos</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Informe o NCM e veja o regime de IVA, alíquotas IBS/CBS simuladas para 2026
                e o cClassTrib sugerido para NFe (venda padrão), com os campos necessários para o XML.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([3, 1])
    with col1:
        ncm_input = st.text_input(
            "Informe o NCM (com ou sem pontos)",
            placeholder="Ex.: 16023220 ou 16.02.32.20",
        )
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

            # Busca cClassTrib padrão para esse CST
            c_info = get_cclasstrib_for_cst(cst_ibscbs)

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

            st.markdown(
                f"""
                <div class="pricetax-card" style="margin-top:1rem;display:flex;gap:2rem;flex-wrap:wrap;">
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

            st.subheader("Parâmetros de classificação", divider="gray")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown("**Produto é alimento?**")
                st.markdown(
                    f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_alim)}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown("**Cesta Básica Nacional?**")
                st.markdown(
                    f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_cesta)}</span>",
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown("**Hortifrúti / Ovos?**")
                st.markdown(
                    f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_hf)}</span>",
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown("**Depende de destinação?**")
                st.markdown(
                    f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_dep)}</span>",
                    unsafe_allow_html=True,
                )

            c5, c6 = st.columns(2)
            with c5:
                st.markdown("**CST IBS/CBS (venda)**")
                st.markdown(
                    f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{cst_ibscbs or '—'}</span>",
                    unsafe_allow_html=True,
                )
            with c6:
                st.markdown("**Imposto Seletivo (IS)**")
                flag_is = row.get("FLAG_IMPOSTO_SELETIVO", "")
                st.markdown(
                    f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_is)}</span>",
                    unsafe_allow_html=True,
                )

            # -----------------------------
            # BLOCO: CAMPOS PARA XML 2026
            # -----------------------------
            st.subheader("Parâmetros para XML 2026 – NFe (venda padrão)", divider="gray")

            if c_info:
                col_xml1, col_xml2 = st.columns(2)
                with col_xml1:
                    st.markdown("**cClassTrib sugerido (NFe)**")
                    st.markdown(
                        f"<span style='color:{PRIMARY_YELLOW};font-weight:700;'>"
                        f"{c_info['COD_CLASS'] or '—'} – {c_info['DESC_CLASS'] or ''}"
                        f"</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("**Tipo de Alíquota**")
                    st.markdown(c_info["TIPO_ALIQUOTA"] or "—")

                with col_xml2:
                    st.markdown("**Flags do cenário (Classificação Tributária)**")
                    st.markdown(
                        f"- Tributação Regular: **{c_info['TRIB_REG'] or '—'}**  \n"
                        f"- Redução de Alíquota: **{c_info['RED_ALIQ'] or '—'}**  \n"
                        f"- Transferência de Crédito: **{c_info['TRANSF_CRED'] or '—'}**  \n"
                        f"- Diferimento: **{c_info['DIFERIMENTO'] or '—'}**  \n"
                        f"- Monofásica: **{c_info['MONOFASICA'] or '—'}**"
                    )

                # Alíquotas que vão pro XML (pIBS / pCBS) – visão prática pro ERP
                st.markdown("**Alíquotas para parametrização XML (pIBS / pCBS)**")
                st.markdown(
                    f"- pIBS (UF): **{pct_str(ibs_uf)}**  \n"
                    f"- pIBS (Município): **{pct_str(ibs_mun)}**  \n"
                    f"- pCBS: **{pct_str(cbs)}**  \n"
                    f"- pIVA Total: **{pct_str(total_iva)}**"
                )

                if c_info["URL_LEI"]:
                    st.markdown(
                        f"[Base legal (classificação tributária)]({c_info['URL_LEI']})"
                    )
            else:
                st.info(
                    "Não foi possível localizar um cClassTrib padrão para este CST na tabela de Classificação Tributária."
                )

            st.markdown("---")

            def clean_txt(v):
                s = str(v or "").strip()
                return "" if s.lower() == "nan" else s

            alerta_fmt = clean_txt(row.get("ALERTA_APP"))
            obs_alim   = clean_txt(row.get("OBS_ALIMENTO"))
            obs_dest   = clean_txt(row.get("OBS_DESTINACAO"))
            reg_extra  = clean_txt(row.get("OBS_REGIME_ESPECIAL"))

            if "RED_60" in (regime or "").upper():
                if not alerta_fmt:
                    alerta_fmt = "Redução de 60% aplicada; conferir aderência ao segmento e às condições legais."
                if not reg_extra:
                    reg_extra = (
                        "Ano teste 2026 – IBS 0,1% (UF) e CBS 0,9%. "
                        "Carga reduzida em 60% conforme regras de essencialidade/alimentos."
                    )

            st.markdown(f"**Base legal aplicada (TIPI/PRICETAX):** {fonte or '—'}")
            st.markdown(f"**Alerta PRICETAX:** {alerta_fmt or '—'}")
            st.markdown(f"**Observação sobre alimentos:** {obs_alim or '—'}")
            st.markdown(f"**Observação sobre destinação:** {obs_dest or '—'}")
            st.markdown(f"**Regime especial / motivo adicional:** {reg_extra or '—'}")

# --------------------------------------------------
# ABA 2 – RANKING DE SAÍDAS (SPED → IBS/CBS + cClassTrib)
# --------------------------------------------------
with tabs[1]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Análise de Vendas (Saídas SPED)</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Faça upload de arquivos SPED PIS/COFINS (.txt ou .zip). O sistema irá:
                <br><br>
                • Ler o Bloco C (C100/C170)<br>
                • Considerar apenas notas de saída (IND_OPER = 1)<br>
                • Filtrar CFOPs de saída (5.xxx, 6.xxx, 7.xxx)<br>
                • Consolidar vendas por NCM, Descrição do Item e CFOP<br>
                • Cruzar com a TIPI IBS/CBS 2026 e Classificação Tributária (cClassTrib)<br>
                • Gerar um ranking total com os principais campos para parametrizar o XML em 2026.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_rank = st.file_uploader(
        "Selecione arquivos SPED PIS/COFINS (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
        key="sped_upload_rank",
    )

    if uploaded_rank:
        if st.button("Processar SPED e Gerar Ranking", type="primary"):
            df_list = []
            total_files = len(uploaded_rank)
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("Processando arquivos SPED..."):
                for idx, up in enumerate(uploaded_rank, start=1):
                    nome = up.name
                    status_text.markdown(f"**Processando arquivo {idx}/{total_files}:** `{nome}`")

                    if nome.lower().endswith(".zip"):
                        z_bytes = up.read()
                        with zipfile.ZipFile(io.BytesIO(z_bytes), "r") as z:
                            for info in z.infolist():
                                if info.filename.lower().endswith(".txt"):
                                    conteudo = z.open(info).read()
                                    try:
                                        texto = conteudo.decode("latin-1")
                                    except UnicodeDecodeError:
                                        texto = conteudo.decode("utf-8", errors="ignore")

                                    df_rank = process_sped_file(texto)
                                    if not df_rank.empty:
                                        df_rank.insert(0, "ARQUIVO", info.filename)
                                        df_list.append(df_rank)
                    else:
                        conteudo = up.read()
                        try:
                            texto = conteudo.decode("latin-1")
                        except UnicodeDecodeError:
                            texto = conteudo.decode("utf-8", errors="ignore")

                        df_rank = process_sped_file(texto)
                        if not df_rank.empty:
                            df_rank.insert(0, "ARQUIVO", nome)
                            df_list.append(df_rank)

                    progress_bar.progress(idx / total_files)

            status_text.empty()
            progress_bar.empty()

            if not df_list:
                st.error(
                    "Nenhuma nota fiscal de saída com CFOP 5.xxx, 6.xxx ou 7.xxx foi encontrada nos arquivos enviados."
                )
            else:
                df_total = pd.concat(df_list, ignore_index=True)

                # -----------------------------
                # CRUZAMENTO COM TIPI IBS/CBS + cClassTrib
                # -----------------------------
                if df_tipi.empty:
                    st.warning(
                        "Base TIPI IBS/CBS 2026 não carregada. O ranking será exibido sem os campos de IBS/CBS/cClassTrib."
                    )
                else:
                    # Normaliza NCM e junta com TIPI
                    df_total["NCM_DIG"] = (
                        df_total["NCM"]
                        .astype(str)
                        .str.replace(r"\D", "", regex=True)
                        .str.zfill(8)
                    )

                    cols_tipi_merge = [
                        "NCM_DIG",
                        "REGIME_IVA_2026_FINAL",
                        "IBS_UF_TESTE_2026_FINAL",
                        "IBS_MUN_TESTE_2026_FINAL",
                        "CBS_TESTE_2026_FINAL",
                        "CST_IBSCBS",
                    ]
                    for c in cols_tipi_merge:
                        if c not in df_tipi.columns:
                            df_tipi[c] = ""

                    df_total = df_total.merge(
                        df_tipi[cols_tipi_merge],
                        on="NCM_DIG",
                        how="left",
                    )

                    # Converte alíquotas para float
                    df_total["IBS_UF_2026"] = df_total["IBS_UF_TESTE_2026_FINAL"].apply(to_float_br)
                    df_total["IBS_MUN_2026"] = df_total["IBS_MUN_TESTE_2026_FINAL"].apply(to_float_br)
                    df_total["CBS_2026"] = df_total["CBS_TESTE_2026_FINAL"].apply(to_float_br)
                    df_total["ALIQ_IVA_TOTAL_2026"] = (
                        df_total["IBS_UF_2026"] + df_total["IBS_MUN_2026"] + df_total["CBS_2026"]
                    )

                    # CST_KEY para buscar cClassTrib
                    df_total["CST_KEY"] = df_total["CST_IBSCBS"].apply(normalize_cst_key)

                    # mapeia cClassTrib sugerido
                    def map_cclass(key: str, field: str) -> str:
                        info = cclasstrib_index.get(key)
                        if not info:
                            return ""
                        return info.get(field, "")

                    df_total["CCLASSTRIB_SUGERIDO"] = df_total["CST_KEY"].apply(
                        lambda k: map_cclass(k, "COD_CLASS")
                    )
                    df_total["DESC_CCLASSTRIB"] = df_total["CST_KEY"].apply(
                        lambda k: map_cclass(k, "DESC_CLASS")
                    )
                    df_total["TIPO_ALIQUOTA_CCLASSTRIB"] = df_total["CST_KEY"].apply(
                        lambda k: map_cclass(k, "TIPO_ALIQUOTA")
                    )

                # Ordena pelo valor total de vendas
                df_total = df_total.sort_values("VALOR_TOTAL_VENDAS", ascending=False).reset_index(drop=True)

                # DataFrame para visualização com valor formatado BR
                df_vis = df_total.copy()
                df_vis["VALOR_TOTAL_VENDAS"] = df_vis["VALOR_TOTAL_VENDAS"].apply(
                    lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )

                # formata alíquotas em texto amigável (sem mexer no df_total numérico)
                if "IBS_UF_2026" in df_vis.columns:
                    for col in ["IBS_UF_2026", "IBS_MUN_2026", "CBS_2026", "ALI
