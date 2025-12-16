"""
PRICETAX - Sistema de Consulta e Análise IBS/CBS 2026
========================================================

Aplicação web desenvolvida em Streamlit para auxiliar empresas na transição
para o novo sistema tributário brasileiro (IBS e CBS).

Funcionalidades principais:
1. Consulta de NCM com simulação de alíquotas IBS/CBS
2. Ranking de vendas via análise de arquivos SPED PIS/COFINS
3. Sugestão automática de cClassTrib baseada em NCM e CFOP

Lógica de Cálculo de Alíquotas:
- Alíquotas integrais fixas (ano teste 2026): IBS 0,10% | CBS 0,90%
- Percentual de redução extraído do regime (ex: RED_60 = 60% de redução)
- Alíquotas efetivas calculadas aplicando a redução sobre as integrais
- Valores finais são obtidos da planilha de regras (já com reduções aplicadas)

Autor: PRICETAX
Versão: 3.0
Data: Dezembro 2024
"""

import base64
import io
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st
import altair as alt

# =============================================================================
# CONFIGURAÇÃO GERAL E IDENTIDADE VISUAL PRICETAX
# =============================================================================

st.set_page_config(
    page_title="PRICETAX - IBS/CBS 2026 & Ranking SPED",
    page_icon="https://pricetax.com.br/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Paleta de cores PRICETAX
COLOR_GOLD = "#FFD700"
COLOR_BLACK = "#000000"
COLOR_DARK_BG = "#0a0a0a"
COLOR_CARD_BG = "#1a1a1a"
COLOR_GREEN_NEON = "#00FF00"
COLOR_WHITE = "#FFFFFF"
COLOR_GRAY_LIGHT = "#CCCCCC"
COLOR_GRAY_MEDIUM = "#666666"
COLOR_BORDER = "#333333"
COLOR_ERROR = "#FF4444"

# Aplicação do tema PRICETAX
st.markdown(
    f"""
    <style>
    /* Reset e configurações globais */
    .stApp {{
        background-color: {COLOR_BLACK};
        color: {COLOR_WHITE};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    
    .block-container {{
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }}
    
    /* Cabeçalho PRICETAX */
    .pricetax-header {{
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    
    .pricetax-logo {{
        font-size: 2.8rem;
        font-weight: 700;
        color: {COLOR_GOLD};
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }}
    
    .pricetax-tagline {{
        font-size: 1.1rem;
        color: {COLOR_GRAY_LIGHT};
        font-weight: 300;
        letter-spacing: 0.02em;
    }}
    
    /* Cards profissionais */
    .pricetax-card {{
        background: {COLOR_CARD_BG};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }}
    
    .pricetax-card-header {{
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: {COLOR_GOLD};
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    
    .pricetax-card-error {{
        background: rgba(255, 68, 68, 0.1);
        border: 1px solid {COLOR_ERROR};
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }}
    
    /* Métricas e valores */
    .metric-container {{
        display: flex;
        gap: 2rem;
        flex-wrap: wrap;
        margin: 1.5rem 0;
    }}
    
    .metric-box {{
        flex: 1;
        min-width: 200px;
    }}
    
    .metric-label {{
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {COLOR_GRAY_MEDIUM};
        margin-bottom: 0.5rem;
    }}
    
    .metric-value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {COLOR_GOLD};
        line-height: 1;
    }}
    
    .metric-value-secondary {{
        font-size: 2rem;
        font-weight: 600;
        color: {COLOR_WHITE};
    }}
    
    /* Tags e badges */
    .tag {{
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0.2rem;
    }}
    
    .tag-regime {{
        background: rgba(255, 215, 0, 0.15);
        border: 1px solid {COLOR_GOLD};
        color: {COLOR_GOLD};
    }}
    
    .tag-info {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid {COLOR_BORDER};
        color: {COLOR_GRAY_LIGHT};
    }}
    
    .tag-success {{
        background: rgba(0, 255, 0, 0.1);
        border: 1px solid {COLOR_GREEN_NEON};
        color: {COLOR_GREEN_NEON};
    }}
    
    .tag-error {{
        background: rgba(255, 68, 68, 0.1);
        border: 1px solid {COLOR_ERROR};
        color: {COLOR_ERROR};
    }}
    
    /* Inputs e formulários */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {{
        background-color: {COLOR_DARK_BG};
        color: {COLOR_WHITE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 0.6rem;
    }}
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: {COLOR_GOLD};
        box-shadow: 0 0 0 1px {COLOR_GOLD};
    }}
    
    .stFileUploader > label > div {{
        color: {COLOR_GRAY_LIGHT};
    }}
    
    /* Botões */
    .stButton > button[kind="primary"] {{
        background-color: {COLOR_GOLD};
        color: {COLOR_BLACK};
        border: none;
        border-radius: 4px;
        font-weight: 600;
        padding: 0.6rem 2rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background-color: #FFF;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 215, 0, 0.3);
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2rem;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 1rem 0;
        color: {COLOR_GRAY_MEDIUM};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.9rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {COLOR_GOLD};
        border-bottom: 2px solid {COLOR_GOLD};
    }}
    
    /* Tabelas */
    .dataframe {{
        background-color: {COLOR_CARD_BG} !important;
        color: {COLOR_WHITE} !important;
    }}
    
    .dataframe th {{
        background-color: {COLOR_DARK_BG} !important;
        color: {COLOR_GOLD} !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }}
    
    .dataframe td {{
        border-color: {COLOR_BORDER} !important;
    }}
    
    /* Divisores */
    hr {{
        border-color: {COLOR_BORDER};
        margin: 2rem 0;
    }}
    
    /* Seções de informação */
    .info-section {{
        background: rgba(255, 215, 0, 0.05);
        border-left: 3px solid {COLOR_GOLD};
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 0 4px 4px 0;
    }}
    
    .info-section-title {{
        font-weight: 600;
        color: {COLOR_GOLD};
        margin-bottom: 0.5rem;
    }}
    
    /* Ocultar elementos do Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def only_digits(s: Optional[str]) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    return re.sub(r"\D+", "", s or "")


def to_float_br(s) -> float:
    """
    Converte string em formato brasileiro para float.
    Aceita formatos como: 1.234,56 ou 1234.56
    """
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


def pct_str(v: float) -> str:
    """Formata um número como percentual no padrão brasileiro."""
    return f"{v:.2f}".replace(".", ",") + "%"


def competencia_from_dt(dt_ini: str, dt_fin: str) -> str:
    """Extrai competência (MM/AAAA) a partir das datas do registro 0000."""
    for raw in (dt_ini or "", dt_fin or ""):
        dig = only_digits(raw)
        if len(dig) == 8:
            return f"{dig[2:4]}/{dig[4:8]}"
    return ""


def normalize_cols_upper(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nomes de colunas para maiúsculas."""
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def regime_label(regime: str) -> str:
    """Retorna o label formatado do regime tributário."""
    r = (regime or "").upper()
    mapping = {
        "ALIQ_ZERO_CESTA_BASICA_NACIONAL": "Alíquota Zero - Cesta Básica Nacional",
        "ALIQ_ZERO_HORTIFRUTI_OVOS": "Alíquota Zero - Hortifrúti e Ovos",
        "RED_60_ALIMENTOS": "Redução de 60% - Alimentos",
        "RED_60_ESSENCIALIDADE": "Redução de 60% - Essencialidade",
        "TRIBUTACAO_PADRAO": "Tributação Padrão",
    }
    return mapping.get(r, regime or "Regime não mapeado")


def label_from_sped_header(text: str, default_name: str) -> str:
    """
    Monta rótulo "MM/AAAA - NOME DA EMPRESA" a partir do registro |0000|.
    Se não conseguir, retorna o nome padrão (nome do arquivo).
    """
    try:
        for line in text.splitlines():
            if line.startswith("|0000|"):
                parts = line.split("|")
                dt_ini = parts[4] if len(parts) > 4 else ""
                dt_fin = parts[5] if len(parts) > 5 else ""
                nome = parts[6] if len(parts) > 6 else ""
                comp = competencia_from_dt(dt_ini, dt_fin)
                nome_clean = nome.strip() or default_name
                if comp:
                    return f"{comp} - {nome_clean}"
                return nome_clean
    except Exception:
        pass
    return default_name


def format_flag(value: str) -> str:
    """Formata flags SIM/NÃO de forma profissional."""
    v = str(value or "").strip().upper()
    if v == "SIM":
        return '<span class="tag tag-success">SIM</span>'
    else:
        return '<span class="tag tag-error">NÃO</span>'


def map_tipo_aliquota(codigo: str) -> str:
    """
    Mapeia código de tipo de alíquota para descrição legível.
    Baseado no portal SEFAZ de Classificação Tributária.
    """
    mapping = {
        "1": "Específica",
        "2": "Padrão",
        "3": "Estimada",
        "4": "Uniforme Nacional",
        "5": "Uniforme Setorial",
    }
    return mapping.get(str(codigo).strip(), codigo or "—")

# =============================================================================
# CARREGAMENTO DA BASE TIPI
# =============================================================================

TIPI_DEFAULT_NAME = "PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx"
ALT_TIPI_NAME = "TIPI_IBS_CBS_CLASSIFICADA_MIND7.xlsx"


@st.cache_data(show_spinner=False)
def load_tipi_base() -> pd.DataFrame:
    """
    Carrega a planilha de regras TIPI IBS/CBS.
    Procura em múltiplos caminhos possíveis e normaliza as colunas.
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
        df["NCM_DIG"] = (
            df["NCM"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)
        )

    required = [
        "NCM_DESCRICAO",
        "REGIME_IVA_2026_FINAL",
        "FONTE_LEGAL_FINAL",
        "FLAG_ALIMENTO",
        "FLAG_CESTA_BASICA",
        "FLAG_HORTIFRUTI_OVOS",
        "FLAG_RED_60",
        "FLAG_DEPENDE_DESTINACAO",
        "IBS_UF_TESTE_2026_FINAL",
        "IBS_MUN_TESTE_2026_FINAL",
        "CBS_TESTE_2026_FINAL",
        "CST_IBSCBS",
        "ALERTA_APP",
        "OBS_ALIMENTO",
        "OBS_DESTINACAO",
        "OBS_REGIME_ESPECIAL",
        "FLAG_IMPOSTO_SELETIVO",
    ]
    for c in required:
        if c not in df.columns:
            df[c] = ""

    return df


def buscar_ncm(df: pd.DataFrame, ncm_raw: str):
    """Busca um NCM na base de dados."""
    n = only_digits(ncm_raw)
    if len(n) != 8 or df.empty:
        return None
    row = df.loc[df["NCM_DIG"] == n]
    return None if row.empty or row.isnull().all().all() else row.iloc[0]


# Carrega a base TIPI
df_tipi = load_tipi_base()

# =============================================================================
# CARREGAMENTO DA BASE DE CLASSIFICAÇÃO TRIBUTÁRIA
# =============================================================================

CLASSIF_NAME = "classificacao_tributaria.xlsx"


@st.cache_data(show_spinner=False)
def load_classificacao_base() -> pd.DataFrame:
    """Carrega a planilha de classificação tributária."""
    paths = [
        Path(CLASSIF_NAME),
        Path.cwd() / CLASSIF_NAME,
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

    df = df.copy()
    return df


df_class = load_classificacao_base()


@st.cache_data(show_spinner=False)
def build_cclasstrib_code_index(df_class_: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    """Constrói índice de classificação tributária por código."""
    index: Dict[str, Dict[str, str]] = {}
    if df_class_.empty:
        return index

    col_cod = "Código da Classificação Tributária"
    for code, grp in df_class_.groupby(col_cod):
        if pd.isna(code):
            continue
        g = grp.copy()

        if "NFe" in g.columns:
            g_pref = g[g["NFe"].astype(str).str.lower() == "sim"]
            if not g_pref.empty:
                g = g_pref

        row = g.iloc[0]
        index[str(code).strip()] = {
            "DESC_CLASS": str(row.get("Descrição da Classificação Tributária", "")),
            "TIPO_ALIQUOTA": str(row.get("Tipo de Alíquota", "")),
            "TRIB_REG": str(row.get("Tributação Regular", "")),
            "RED_ALIQ": str(row.get("Redução de Alíquota", "")),
            "TRANSF_CRED": str(row.get("Transferência de Crédito", "")),
            "DIFERIMENTO": str(row.get("Diferimento", "")),
            "MONOFASICA": str(row.get("Tributação Monofásica Normal", "")),
        }

    return index


cclasstrib_index = build_cclasstrib_code_index(df_class)


def get_class_info_by_code(code: str) -> Optional[Dict[str, str]]:
    """Obtém informações de classificação tributária por código."""
    if not code:
        return None
    return cclasstrib_index.get(str(code).strip())

# =============================================================================
# MAPEAMENTO CFOP → cClassTrib
# =============================================================================

CFOP_NAO_ONEROSOS_410999 = [
    "5910", "6910", "7910",  # Remessa em bonificação, doação ou brinde
    "5911", "6911", "7911",  # Remessa de amostra grátis
    "5949", "6949", "7949",  # Outra saída não especificada
    "5917", "6917", "7917",  # Remessa de mercadoria em consignação mercantil ou industrial
]

CFOP_CCLASSTRIB_MAP = {
    # Vendas padrão (tributação regular)
    "5101": "000001",
    "5102": "000001",
    "5103": "000001",
    "5104": "000001",
    "5105": "000001",
    "5106": "000001",
    "5109": "000001",
    "5110": "000001",
    "5111": "000001",
    "5112": "000001",
    "5113": "000001",
    "5114": "000001",
    "5115": "000001",
    "5116": "000001",
    "5117": "000001",
    "5118": "000001",
    "5119": "000001",
    "5120": "000001",
    "5122": "000001",
    "5123": "000001",
    "5124": "000001",
    "5125": "000001",
    
    "6101": "000001",
    "6102": "000001",
    "6103": "000001",
    "6104": "000001",
    "6105": "000001",
    "6106": "000001",
    "6107": "000001",
    "6108": "000001",
    "6109": "000001",
    "6110": "000001",
    "6111": "000001",
    "6112": "000001",
    "6113": "000001",
    "6114": "000001",
    "6115": "000001",
    "6116": "000001",
    "6117": "000001",
    "6118": "000001",
    "6119": "000001",
    "6120": "000001",
    "6122": "000001",
    "6123": "000001",
    "6124": "000001",
    
    "7101": "000001",
    "7102": "000001",
    "7105": "000001",
    "7106": "000001",
    "7127": "000001",
    
    # Operações não onerosas
    "5910": "410999",
    "6910": "410999",
    "7910": "410999",
    "5911": "410999",
    "6911": "410999",
    "7911": "410999",
    "5949": "410999",
    "6949": "410999",
    "7949": "410999",
    "5917": "410999",
    "6917": "410999",
    "7917": "410999",
    
    # Operações específicas
    "5922": "000001",
    "6922": "000001",
    "6557": "000001",
}

for _cfop in CFOP_NAO_ONEROSOS_410999:
    CFOP_CCLASSTRIB_MAP.setdefault(_cfop, "410999")


def guess_cclasstrib(cst: Any, cfop: Any, regime_iva: str) -> tuple[str, str]:
    """
    Sugere um código de Classificação Tributária (cClassTrib) para NFe.
    
    A sugestão é baseada em:
    1. Mapeamento fixo de CFOPs específicos (via CFOP_CCLASSTRIB_MAP)
    2. Regras genéricas para saídas tributadas (CFOPs 5xxx/6xxx/7xxx + CST normal)
    3. Identificação de operações não onerosas (410999)
    
    Parâmetros:
        cst (Any): Código de Situação Tributária (CST) do produto
        cfop (Any): Código Fiscal de Operações e Prestações (CFOP)
        regime_iva (str): Regime de tributação IVA do produto (não utilizado atualmente)
    
    Retorna:
        tuple[str, str]: (código_cClassTrib, mensagem_explicativa)
    
    Exemplos:
        - CFOP 5102 + CST 000 → ("000001", "tributação regular")
        - CFOP 5910 (brinde) → ("410999", "operação não onerosa")
    """
    cst_clean = re.sub(r"\D+", "", str(cst or ""))
    cfop_clean = re.sub(r"\D+", "", str(cfop or ""))

    if not cfop_clean:
        return "", "Informe o CFOP da operação de venda para sugerir o cClassTrib padrão."

    # 1) Regra fixa via mapa
    if cfop_clean in CFOP_CCLASSTRIB_MAP:
        code = CFOP_CCLASSTRIB_MAP[cfop_clean]
        msg = (
            f"Regra padrão PRICETAX: CFOP {cfop_clean} → "
            f"cClassTrib {code} (conforme matriz PRICETAX)."
        )
        return code, msg

    # 2) Saída (5, 6 ou 7) com CST de tributação "normal" → 000001
    if cfop_clean[0] in ("5", "6", "7") and cst_clean in {"000", "200", "201", "202", "900"}:
        code = "000001"
        msg = (
            f"Regra genérica: CFOP {cfop_clean} é saída tributada padrão "
            f"→ cClassTrib {code} (tributação regular). "
            "Revise apenas se for operação especial (doação, brinde, bonificação, remessa técnica etc.)."
        )
        return code, msg

    # 3) Não conseguiu sugerir nada com segurança
    return "", (
        "Não foi possível localizar um cClassTrib padrão para o CFOP informado. "
        "Provável operação especial (devolução, bonificação, remessa, teste, garantia etc.) – revisar manualmente."
    )

# =============================================================================
# PROCESSADOR SPED - RANKING DE SAÍDAS
# =============================================================================

def process_sped_file(file_content: str) -> pd.DataFrame:
    """
    Processa o conteúdo do arquivo SPED PIS/COFINS para extrair dados de vendas.
    
    Esta função realiza as seguintes operações:
    1. Lê registros |0200| para mapear códigos de produtos a NCMs
    2. Identifica documentos de saída através do registro |C100| (IND_OPER = 1)
    3. Extrai itens vendidos do registro |C170| com CFOPs de saída (5xxx, 6xxx, 7xxx)
    4. Consolida vendas por NCM, descrição e CFOP
    5. Ordena o resultado por valor total de vendas (decrescente)
    
    Parâmetros:
        file_content (str): Conteúdo completo do arquivo SPED em formato texto
    
    Retorna:
        pd.DataFrame: DataFrame com colunas NCM, DESCRICAO, CFOP, VALOR_TOTAL_VENDAS
                      ordenado por valor de vendas (maior para menor)
    
    Nota:
        - Apenas operações de saída (IND_OPER = 1) são consideradas
        - CFOPs de entrada (1xxx, 2xxx, 3xxx) são automaticamente ignorados
    """
    produtos: Dict[str, Dict[str, str]] = {}
    documentos: Dict[str, Dict[str, Any]] = {}
    itens_venda = []

    cfop_saida_pattern = re.compile(r"^[567]\d{3}$")
    current_doc_key: Optional[str] = None

    try:
        file_stream = io.StringIO(file_content)

        for line in file_stream:
            fields = line.strip().split("|")
            if not fields or len(fields) < 2:
                continue

            registro = fields[1]

            if registro == "0200":
                if len(fields) >= 9:
                    cod_item = fields[2]
                    descr_item = fields[3]
                    cod_ncm = fields[8]
                    produtos[cod_item] = {"NCM": cod_ncm, "DESCR_ITEM": descr_item}

            elif registro == "C100":
                ind_oper = fields[2] if len(fields) > 2 else ""
                if ind_oper == "1":
                    chv_nfe = fields[9] if len(fields) > 9 else ""
                    ser = fields[6] if len(fields) > 6 else ""
                    num_doc = fields[7] if len(fields) > 7 else ""

                    if chv_nfe:
                        current_doc_key = chv_nfe
                    elif ser and num_doc:
                        current_doc_key = f"{ser}-{num_doc}"
                    else:
                        current_doc_key = None

                    if current_doc_key:
                        documentos[current_doc_key] = {"IND_OPER": ind_oper}
                else:
                    current_doc_key = None

            elif (
                registro == "C170"
                and current_doc_key
                and documentos.get(current_doc_key, {}).get("IND_OPER") == "1"
            ):
                if len(fields) >= 12:
                    cod_item = fields[3]
                    vl_item_str = fields[7].replace(",", ".")
                    cfop = fields[11]

                    try:
                        vl_item = float(vl_item_str)
                    except ValueError:
                        continue

                    if cfop_saida_pattern.match(cfop):
                        itens_venda.append(
                            {
                                "COD_ITEM": cod_item,
                                "VL_ITEM": vl_item,
                                "CFOP": cfop,
                                "DOC_KEY": current_doc_key,
                            }
                        )

            elif registro in ("C190", "C300", "D100", "E100"):
                current_doc_key = None

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return pd.DataFrame()

    ranking_vendas: Dict[tuple, Dict[str, Any]] = defaultdict(
        lambda: {"NCM": "", "DESCR_ITEM": "", "CFOP": "", "TOTAL_VENDAS": 0.0}
    )

    for item in itens_venda:
        cod_item = item["COD_ITEM"]
        vl_item = item["VL_ITEM"]
        cfop = item["CFOP"]

        produto_info = produtos.get(cod_item)
        if produto_info:
            ncm = produto_info["NCM"]
            descr_item = produto_info["DESCR_ITEM"]

            chave = (ncm, descr_item, cfop)
            ranking_vendas[chave]["NCM"] = ncm
            ranking_vendas[chave]["DESCR_ITEM"] = descr_item
            ranking_vendas[chave]["CFOP"] = cfop
            ranking_vendas[chave]["TOTAL_VENDAS"] += vl_item

    relatorio = []
    for chave, dados in ranking_vendas.items():
        relatorio.append(
            {
                "NCM": dados["NCM"],
                "DESCRICAO": dados["DESCR_ITEM"],
                "VALOR_TOTAL_VENDAS": dados["TOTAL_VENDAS"],
                "CFOP": dados["CFOP"],
            }
        )

    if not relatorio:
        return pd.DataFrame(
            columns=["NCM", "DESCRICAO", "CFOP", "VALOR_TOTAL_VENDAS"]
        )

    df = pd.DataFrame(relatorio)
    df = df.sort_values("VALOR_TOTAL_VENDAS", ascending=False).reset_index(drop=True)
    return df

# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================

# Cabeçalho PRICETAX com logo
# Carregar logo
logo_path = Path(__file__).parent / "logo_pricetax.png"
if not logo_path.exists():
    logo_path = Path("logo_pricetax.png")

if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_data}" style="max-width:350px;height:auto;" alt="PRICETAX">'
else:
    logo_html = '<div class="pricetax-logo">PRICETAX</div>'

st.markdown(
    f"""
    <div class="pricetax-header">
        {logo_html}
        <div class="pricetax-tagline">Soluções para transição inteligente na Reforma Tributária</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Tabs principais
tabs = st.tabs(
    [
        "Consulta NCM",
        "Ranking de Saídas SPED",
        "cClassTrib",
    ]
)

# =============================================================================
# ABA 1 - CONSULTA NCM
# =============================================================================

with tabs[0]:
    st.markdown(
        """
        <div class="pricetax-card">
            <div class="pricetax-card-header">Consulta por NCM e CFOP</div>
            <div style="font-size:0.95rem;color:#CCCCCC;line-height:1.6;">
                Utilize este painel como referência para parametrizar o item no ERP e no XML:<br><br>
                • Informe o <strong>NCM</strong> do produto e o <strong>CFOP de venda</strong> atualmente utilizado<br>
                • A partir do NCM e CFOP informado será retornado o cClassTrib e a tributação de IBS e CBS<br>
                • Exibe os principais campos para configuração do XML (pIBS, pCBS, cClassTrib)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3 = st.columns([3, 1.4, 1])
    with col1:
        ncm_input = st.text_input(
            "NCM do produto",
            placeholder="Ex.: 16023220 ou 16.02.32.20",
            help="Informe o NCM completo (8 dígitos), com ou sem pontos.",
        )
    with col2:
        cfop_input = st.text_input(
            "CFOP da venda (atual)",
            placeholder="Ex.: 5102",
            max_chars=4,
            help="CFOP utilizado hoje na venda do produto (quatro dígitos).",
        )
    with col3:
        st.write("")
        consultar = st.button("Consultar", type="primary")

    if consultar and ncm_input.strip():
        row = buscar_ncm(df_tipi, ncm_input)

        if row is None:
            st.markdown(
                f"""
                <div class="pricetax-card-error">
                    <strong>NCM informado:</strong> {ncm_input}<br>
                    Não localizamos esse NCM na base PRICETAX. Revise o código ou a planilha de referência.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            ncm_fmt = row["NCM_DIG"]
            desc = row["NCM_DESCRICAO"]
            regime = row["REGIME_IVA_2026_FINAL"]
            fonte = row["FONTE_LEGAL_FINAL"]
            flag_cesta = row["FLAG_CESTA_BASICA"]
            flag_hf = row["FLAG_HORTIFRUTI_OVOS"]
            flag_red = row["FLAG_RED_60"]
            flag_alim = row["FLAG_ALIMENTO"]
            flag_dep = row["FLAG_DEPENDE_DESTINACAO"]
            ibs_uf = to_float_br(row["IBS_UF_TESTE_2026_FINAL"])
            ibs_mun = to_float_br(row["IBS_MUN_TESTE_2026_FINAL"])
            cbs = to_float_br(row["CBS_TESTE_2026_FINAL"])
            total_iva = ibs_uf + ibs_mun + cbs
            cst_ibscbs = row.get("CST_IBSCBS", "")

            # Sugere cClassTrib
            cclastrib_code, cclastrib_msg = guess_cclasstrib(
                cst=cst_ibscbs, cfop=cfop_input, regime_iva=str(regime or "")
            )
            class_info = get_class_info_by_code(cclastrib_code)

            # Header do produto
            st.markdown(
                f"""
                <div class="pricetax-card" style="margin-top:1.5rem;">
                    <div style="font-size:1.3rem;font-weight:600;color:{COLOR_GOLD};margin-bottom:1rem;">
                        NCM {ncm_fmt}
                    </div>
                    <div style="font-size:1rem;color:{COLOR_WHITE};margin-bottom:1rem;">
                        {desc}
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:0.5rem;">
                        <span class="tag tag-regime">{regime_label(regime)}</span>
                        <span class="tag tag-info">Cesta Básica: {flag_cesta or "NÃO"}</span>
                        <span class="tag tag-info">Hortifrúti/Ovos: {flag_hf or "NÃO"}</span>
                        <span class="tag tag-info">Redução 60%: {flag_red or "NÃO"}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Cálculo das alíquotas
            ibs_integral = 0.10
            cbs_integral = 0.90
            
            percentual_reducao = 0.0
            regime_upper = (regime or "").upper()
            
            if "RED_60" in regime_upper:
                percentual_reducao = 60.0
            elif "ALIQ_ZERO" in regime_upper:
                percentual_reducao = 100.0
            
            ibs_efetivo = ibs_uf + ibs_mun
            cbs_efetivo = cbs
            total_iva = ibs_efetivo + cbs_efetivo
            
            st.markdown("### Alíquotas do Produto")
            
            # Alíquotas integrais
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-box">
                        <div class="metric-label">IBS Integral (fixo)</div>
                        <div class="metric-value">{pct_str(ibs_integral)}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">CBS Integral (fixo)</div>
                        <div class="metric-value">{pct_str(cbs_integral)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Percentual de redução
            if percentual_reducao > 0:
                st.markdown(
                    f"""
                    <div class="pricetax-card" style="margin-top:1.5rem;">
                        <div class="metric-label">Percentual de Redução Aplicado</div>
                        <div class="metric-value-secondary">{pct_str(percentual_reducao)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            # Alíquotas efetivas
            st.markdown(
                f"""
                <div class="metric-container" style="margin-top:1.5rem;">
                    <div class="metric-box">
                        <div class="metric-label">IBS Efetivo (após redução)</div>
                        <div class="metric-value">{pct_str(ibs_efetivo)}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">CBS Efetivo (após redução)</div>
                        <div class="metric-value">{pct_str(cbs_efetivo)}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Carga Total IVA Efetiva</div>
                        <div class="metric-value">{pct_str(total_iva)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Tributação da operação
            cfop_clean = re.sub(r"\D+", "", cfop_input or "")
            if cfop_clean:
                code_from_cfop = CFOP_CCLASSTRIB_MAP.get(cfop_clean)

                if code_from_cfop == "410999":
                    st.markdown(
                        f"""
                        <div class="info-section" style="margin-top:2rem;">
                            <div class="info-section-title">Operação Não Onerosa - CFOP {cfop_clean}</div>
                            <div>
                                cClassTrib: <strong>{cclastrib_code or '410999'}</strong><br>
                                Nenhum débito de IBS ou CBS é gerado nesta nota, independentemente da alíquota padrão do NCM.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                elif code_from_cfop == "000001":
                    st.markdown(
                        f"""
                        <div class="info-section" style="margin-top:2rem;">
                            <div class="info-section-title">Operação de Venda Onerosa Padrão - CFOP {cfop_clean}</div>
                            <div>
                                Aplica a mesma alíquota IBS/CBS exibida acima para este NCM, 
                                salvo existência de regime especial ou regra específica do cliente.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # Parâmetros de classificação
            st.markdown("---")
            st.markdown("### Parâmetros de Classificação Tributária")
            
            col_xml1, col_xml2, col_xml3 = st.columns(3)
            
            with col_xml1:
                st.markdown(f"**CST IBS/CBS:** {cst_ibscbs or '—'}")
                st.markdown(f"**Alimento:** {flag_alim or 'NÃO'}")
                st.markdown(f"**Depende de Destinação:** {flag_dep or 'NÃO'}")

            with col_xml2:
                st.markdown("**cClassTrib Sugerido (venda)**")
                if cclastrib_code:
                    desc_class = class_info["DESC_CLASS"] if class_info else ""
                    if desc_class:
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{cclastrib_code}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='font-size:0.9rem;color:{COLOR_GRAY_LIGHT};'>{desc_class}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{cclastrib_code}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>—</span>", unsafe_allow_html=True)

                st.markdown("**Tipo de Alíquota (cClassTrib)**")
                tipo_aliq_code = class_info["TIPO_ALIQUOTA"] if class_info else ""
                tipo_aliq_desc = map_tipo_aliquota(tipo_aliq_code)
                st.markdown(tipo_aliq_desc)

            with col_xml3:
                st.markdown("**Imposto Seletivo (IS)**")
                flag_is = row.get("FLAG_IMPOSTO_SELETIVO", "")
                st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:600;'>{flag_is or 'NÃO'}</span>", unsafe_allow_html=True)
                
                if class_info:
                    st.markdown("**Cenário da Classificação**")
                    st.markdown(
                        f"- Tributação Regular: **{class_info.get('TRIB_REG') or '—'}**  \n"
                        f"- Redução de Alíquota: **{class_info.get('RED_ALIQ') or '—'}**  \n"
                        f"- Transferência de Crédito: **{class_info.get('TRANSF_CRED') or '—'}**  \n"
                        f"- Diferimento: **{class_info.get('DIFERIMENTO') or '—'}**  \n"
                        f"- Monofásica: **{class_info.get('MONOFASICA') or '—'}**"
                    )

            # Observações e alertas (apenas se houver conteúdo relevante)
            st.markdown("---")
            st.markdown("### Informações Complementares")

            def clean_txt(v):
                s = str(v or "").strip()
                return "" if s.lower() == "nan" else s

            fonte = clean_txt(row.get("FONTE_LEGAL_FINAL"))
            alerta_fmt = clean_txt(row.get("ALERTA_APP"))
            obs_alim = clean_txt(row.get("OBS_ALIMENTO"))
            obs_dest = clean_txt(row.get("OBS_DESTINACAO"))
            reg_extra = clean_txt(row.get("OBS_REGIME_ESPECIAL"))

            # Exibir apenas campos com conteúdo
            if fonte:
                st.markdown(f"**Base Legal:** {fonte}")
            
            if alerta_fmt:
                st.markdown(f"**Alerta:** {alerta_fmt}")
            
            if obs_alim:
                st.markdown(f"**Observação (Alimentos):** {obs_alim}")
            
            if obs_dest:
                st.markdown(f"**Observação (Destinação):** {obs_dest}")
            
            if reg_extra:
                st.markdown(f"**Observações Adicionais:** {reg_extra}")
            
            # Se nenhum campo tiver conteúdo, mostrar mensagem
            if not any([fonte, alerta_fmt, obs_alim, obs_dest, reg_extra]):
                st.markdown("*Nenhuma observação adicional disponível para este NCM.*")

# =============================================================================
# ABA 2 - RANKING DE SAÍDAS SPED
# =============================================================================

with tabs[1]:
    st.markdown(
        """
        <div class="pricetax-card">
            <div class="pricetax-card-header">Ranking de Vendas - SPED PIS/COFINS</div>
            <div style="font-size:0.95rem;color:#CCCCCC;line-height:1.6;">
                Utilize este painel para identificar os itens mais relevantes na receita e preparar a base
                para IBS/CBS 2026:<br><br>
                • Importa arquivos SPED PIS/COFINS (<strong>.txt</strong> ou <strong>.zip</strong>)<br>
                • Lê o Bloco C (C100/C170) e considera apenas saídas (IND_OPER = 1)<br>
                • Consolida vendas por NCM, descrição do item e CFOP (5.xxx, 6.xxx, 7.xxx)<br>
                • Cruza automaticamente com a TIPI IBS/CBS PRICETAX 2026<br>
                • Sugere o <strong>cClassTrib</strong> para cada combinação NCM + CFOP<br>
                • Gera um ranking exportável em Excel, pronto para trabalho em ERP e BI
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_rank = st.file_uploader(
        "Arquivos SPED PIS/COFINS (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
        key="sped_upload_rank",
        help="Você pode selecionar um ou vários arquivos. Arquivos .zip são descompactados automaticamente.",
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

                    if nome.lower().endswith(".zip"):
                        z_bytes = up.read()
                        with zipfile.ZipFile(io.BytesIO(z_bytes), "r") as z:
                            for info in z.infolist():
                                if info.filename.lower().endswith(".txt"):
                                    status_text.markdown(
                                        f"**Processando arquivo {idx}/{total_files}:** `{info.filename}`"
                                    )
                                    conteudo = z.open(info).read()
                                    try:
                                        texto = conteudo.decode("latin-1")
                                    except UnicodeDecodeError:
                                        texto = conteudo.decode("utf-8", errors="ignore")

                                    df_rank = process_sped_file(texto)
                                    if not df_rank.empty:
                                        label = label_from_sped_header(texto, info.filename)
                                        df_rank.insert(0, "ARQUIVO", label)
                                        df_list.append(df_rank)
                    else:
                        status_text.markdown(
                            f"**Processando arquivo {idx}/{total_files}:** `{nome}`"
                        )
                        conteudo = up.read()
                        try:
                            texto = conteudo.decode("latin-1")
                        except UnicodeDecodeError:
                            texto = conteudo.decode("utf-8", errors="ignore")

                        df_rank = process_sped_file(texto)
                        if not df_rank.empty:
                            label = label_from_sped_header(texto, nome)
                            df_rank.insert(0, "ARQUIVO", label)
                            df_list.append(df_rank)

                    progress_bar.progress(idx / total_files)

            status_text.empty()
            progress_bar.empty()

            if not df_list:
                st.error("Nenhuma nota fiscal de saída com CFOP 5.xxx, 6.xxx ou 7.xxx foi encontrada nos arquivos enviados.")
            else:
                df_total = pd.concat(df_list, ignore_index=True)

                # Cruzamento com TIPI IBS/CBS
                if df_tipi.empty:
                    st.warning("Base TIPI IBS/CBS 2026 não carregada. O ranking será exibido sem os campos de IBS/CBS/cClassTrib.")
                else:
                    df_total["NCM_DIG"] = (
                        df_total["NCM"]
                        .astype(str)
                        .str.replace(r"\D", "", regex=True)
                        .str.zfill(8)
                    )

                    cols_tipi_merge = [
                        "NCM_DIG",
                        "NCM_DESCRICAO",
                        "REGIME_IVA_2026_FINAL",
                        "IBS_UF_TESTE_2026_FINAL",
                        "IBS_MUN_TESTE_2026_FINAL",
                        "CBS_TESTE_2026_FINAL",
                        "CST_IBSCBS",
                        "FLAG_ALIMENTO",
                        "FLAG_CESTA_BASICA",
                        "FLAG_HORTIFRUTI_OVOS",
                        "FLAG_RED_60",
                    ]
                    
                    df_tipi_mini = df_tipi[cols_tipi_merge].copy()

                    df_total = df_total.merge(
                        df_tipi_mini, on="NCM_DIG", how="left"
                    )

                    # Sugere cClassTrib para cada linha
                    def row_cclasstrib(row):
                        code, _ = guess_cclasstrib(
                            cst=row.get("CST_IBSCBS"),
                            cfop=row.get("CFOP"),
                            regime_iva=row.get("REGIME_IVA_2026_FINAL", "")
                        )
                        return code

                    df_total["CCLASSTRIB_SUGERIDO"] = df_total.apply(row_cclasstrib, axis=1)

                    # Formata valores
                    df_total["VALOR_TOTAL_VENDAS"] = df_total["VALOR_TOTAL_VENDAS"].apply(
                        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    )

                st.success(f"Processamento concluído! Total de {len(df_total)} linhas consolidadas.")
                
                st.markdown("### Ranking de Vendas")
                st.dataframe(df_total, use_container_width=True, height=600)

                # Download
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df_total.to_excel(writer, index=False, sheet_name="Ranking")
                buffer.seek(0)

                st.download_button(
                    label="Download Excel",
                    data=buffer,
                    file_name="ranking_vendas_ibscbs.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

# =============================================================================
# ABA 3 - CONSULTA CCLASSTRIB
# =============================================================================

with tabs[2]:
    st.markdown(
        """
        <div class="pricetax-card">
            <div class="pricetax-card-header">Consulta de Classificação Tributária (cClassTrib)</div>
            <div style="font-size:0.95rem;color:#CCCCCC;line-height:1.6;">
                Utilize este painel para consultar os códigos de Classificação Tributária (cClassTrib) 
                utilizados na Reforma Tributária:<br><br>
                • Busque por <strong>código</strong> (ex: 000001, 830001) ou por <strong>descrição</strong><br>
                • Visualize detalhes completos: tipo de alíquota, percentuais de redução, indicadores<br>
                • Baseado no portal oficial da SEFAZ
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Campo de busca
    col_busca1, col_busca2 = st.columns([3, 1])
    with col_busca1:
        busca_cclasstrib = st.text_input(
            "Buscar por código ou descrição",
            placeholder="Ex: 830001 ou 'energia elétrica'",
            help="Digite o código cClassTrib ou parte da descrição para buscar.",
        )
    with col_busca2:
        st.write("")
        buscar_class = st.button("Buscar", type="primary", key="buscar_class")
    
    if buscar_class and busca_cclasstrib.strip():
        busca_term = busca_cclasstrib.strip()
        
        if df_class.empty:
            st.error("Base de Classificação Tributária não carregada. Verifique se o arquivo 'classificacao_tributaria.xlsx' está disponível.")
        else:
            # Tentar buscar por código numérico
            resultados = pd.DataFrame()
            try:
                codigo_num = int(busca_term)
                resultados = df_class[
                    df_class["Código da Classificação Tributária"] == codigo_num
                ]
            except ValueError:
                pass
            
            # Se não encontrou por código, buscar por descrição
            if resultados.empty:
                busca_upper = busca_term.upper()
                resultados = df_class[
                    df_class["Descrição da Classificação Tributária"].astype(str).str.upper().str.contains(busca_upper, na=False)
                ]
            
            if resultados.empty:
                st.markdown(
                    f"""
                    <div class="pricetax-card-error">
                        <strong>Termo buscado:</strong> {busca_cclasstrib}<br>
                        Não encontramos nenhuma classificação tributária com este código ou descrição.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.success(f"Encontrados {len(resultados)} resultado(s) para '{busca_cclasstrib}'")
                
                # Exibir cada resultado
                for idx, row in resultados.iterrows():
                    codigo = str(int(row.get("Código da Classificação Tributária", 0))).zfill(6)
                    descricao = str(row.get("Descrição da Classificação Tributária", "")).strip()
                    tipo_aliq = str(row.get("Tipo de Alíquota", "")).strip()
                    
                    # Reduções percentuais
                    red_ibs = float(row.get("Redução IBS (%)", 0.0))
                    red_cbs = float(row.get("Redução CBS (%)", 0.0))
                    
                    # Indicadores
                    trib_reg = str(row.get("Tributação Regular", "")).strip().upper()
                    transf_cred = str(row.get("Transferência de Crédito", "")).strip().upper()
                    diferimento = str(row.get("Diferimento", "")).strip().upper()
                    monofasica = str(row.get("Tributação Monofásica Normal", "")).strip().upper()
                    cred_presumido = str(row.get("Crédito Presumido IBS ZFM", "")).strip().upper()
                    dfes = str(row.get("DFes Relacionados", "")).strip()
                    
                    st.markdown(
                        f"""
                        <div class="pricetax-card" style="margin-top:1.5rem;">
                            <div style="font-size:1.3rem;font-weight:600;color:{COLOR_GOLD};margin-bottom:0.5rem;">
                                cClassTrib {codigo}
                            </div>
                            <div style="font-size:1rem;color:{COLOR_WHITE};margin-bottom:1rem;">
                                {descricao}
                            </div>
                            <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
                                <span class="tag tag-regime">{tipo_aliq}</span>
                                {f'<span class="tag tag-info">DFes: {dfes}</span>' if dfes else ''}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    # Exibir IBS e CBS
                    st.markdown("### Alíquotas")
                    col_ibs, col_cbs = st.columns(2)
                    with col_ibs:
                        st.markdown(f"**IBS:** {pct_str(red_ibs)}")
                    with col_cbs:
                        st.markdown(f"**CBS:** {pct_str(red_cbs)}")
                    
                    if red_ibs > 0 or red_cbs > 0:
                        st.markdown(f"**Redução aplicada:** IBS {pct_str(red_ibs)} / CBS {pct_str(red_cbs)}")
                    else:
                        st.markdown("**Redução aplicada:** Nenhuma redução")
                    
                    # Detalhes em colunas
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**Indicadores**")
                        st.markdown(f"Tributação Regular: **{trib_reg if trib_reg != 'NAN' else '—'}**")
                        st.markdown(f"Transferência de Crédito: **{transf_cred if transf_cred != 'NAN' else '—'}**")
                    
                    with col2:
                        st.markdown("**Regimes Especiais**")
                        st.markdown(f"Diferimento: **{diferimento if diferimento != 'NAN' else '—'}**")
                        st.markdown(f"Monofásica: **{monofasica if monofasica != 'NAN' else '—'}**")
                    
                    with col3:
                        st.markdown("**Créditos**")
                        st.markdown(f"Crédito Presumido ZFM: **{cred_presumido if cred_presumido != 'NAN' else '—'}**")
                    
                    st.markdown("---")
    
    elif not busca_cclasstrib.strip():
        # Mostrar lista dos principais cClassTrib
        st.markdown("### Principais Códigos de Classificação Tributária")
        
        principais = [
            {"codigo": "000001", "desc": "Situações tributadas integralmente pelo IBS e CBS"},
            {"codigo": "200001", "desc": "Aquisições realizadas entre empresas autorizadas a operar em zonas de processamento de exportação"},
            {"codigo": "200003", "desc": "Vendas de produtos destinados à alimentação humana (Anexo I)"},
            {"codigo": "200014", "desc": "Fornecimento dos produtos hortícolas, frutas e ovos (Anexo XV)"},
            {"codigo": "200028", "desc": "Fornecimento dos serviços de educação (Anexo II)"},
            {"codigo": "200029", "desc": "Fornecimento dos serviços de saúde humana (Anexo III)"},
            {"codigo": "300001", "desc": "Isenção do IBS e CBS"},
            {"codigo": "410999", "desc": "Outras operações sem débito de IBS ou CBS"},
        ]
        
        for item in principais:
            st.markdown(
                f"""
                <div class="pricetax-card" style="margin-top:1rem;">
                    <div style="font-size:1.1rem;font-weight:600;color:{COLOR_GOLD};">
                        {item['codigo']}
                    </div>
                    <div style="font-size:0.9rem;color:{COLOR_GRAY_LIGHT};margin-top:0.3rem;">
                        {item['desc']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =============================================================================
# RODAPÉ
# =============================================================================

st.markdown("---")
st.markdown(
    f"""
    <div style="text-align:center;color:{COLOR_GRAY_MEDIUM};font-size:0.85rem;padding:2rem 0;">
        <strong style="color:{COLOR_GOLD};">PRICETAX</strong> - Soluções para transição inteligente na Reforma Tributária<br>
        Simplificando o complexo, potencializando os seus resultados.
    </div>
    """,
    unsafe_allow_html=True,
)
