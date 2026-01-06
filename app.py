"""
PRICETAX - Sistema de Consulta e Análise IBS/CBS 2026
========================================================

Aplicação web desenvolvida em Streamlit para auxiliar empresas na transição
para o novo sistema tributário brasileiro (IBS e CBS).

Autor: PRICETAX
Versão: 4.0 (Modern Enterprise UI)
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

# Importar módulo de benefícios fiscais
try:
    from beneficios_fiscais import init_engine, get_engine, consulta_ncm, processar_sped_xml
    BENEFICIOS_DISPONIVEL = True
except ImportError as e:
    print(f"⚠️ Módulo de benefícios fiscais não disponível: {e}")
    BENEFICIOS_DISPONIVEL = False

# =============================================================================
# CONFIGURAÇÃO GERAL E IDENTIDADE VISUAL PRICETAX (MODERNA)
# =============================================================================

st.set_page_config(
    page_title="PRICETAX - IBS/CBS 2026",
    page_icon="https://pricetax.com.br/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Paleta de Cores Sênior (PRICETAX + Portal da Reforma)
COLOR_GOLD = "#FFDD00"       # Amarelo PRICETAX (Ação/Destaque)
COLOR_BLACK = "#000000"      # Preto Original PRICETAX (Cabeçalho)
COLOR_BLUE_PORTAL = "#0056B3" # Azul Institucional (Portal da Reforma)
COLOR_DARK_BG = "#F0F4F8"    # Fundo Azulado Ultra Claro (Conforto)
COLOR_CARD_BG = "#FFFFFF"    # Fundo Branco (Destaque)
COLOR_WHITE = "#1E293B"      # Texto Principal (Cinza Escuro)
COLOR_GRAY_LIGHT = "#64748B" # Texto Secundário (Labels)
COLOR_GRAY_MEDIUM = "#ADB5BD" # Bordas e elementos desativados
COLOR_BORDER = "#D1D9E6"     # Bordas Suaves e Definidas
COLOR_SUCCESS = "#10B981"    # Verde Sucesso
COLOR_ERROR = "#EF4444"      # Vermelho Erro

# Aliases para o novo sistema de design
COLOR_PRIMARY = COLOR_GOLD
COLOR_SECONDARY = COLOR_BLACK
COLOR_BG_MAIN = COLOR_DARK_BG
COLOR_TEXT_MAIN = COLOR_WHITE
COLOR_TEXT_MUTED = COLOR_GRAY_LIGHT

st.markdown(
    f"""
    <style>
    /* Reset e Base */
    .stApp {{
        background-color: {COLOR_BG_MAIN};
        color: {COLOR_TEXT_MAIN};
        font-family: 'Inter', -apple-system, sans-serif;
    }}

    .block-container {{
        padding-top: 2rem;
        max-width: 1200px;
    }}

    /* Cabeçalho Original PRICETAX (Preto) */
    .pricetax-header {{
        text-align: left;
        margin: -3rem -5rem 2rem -5rem;
        padding: 1.5rem 5rem;
        background-color: {COLOR_BLACK};
        border-bottom: 4px solid {COLOR_GOLD};
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}

    .pricetax-logo {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {COLOR_GOLD};
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }}

    .pricetax-tagline {{
        font-size: 1.15rem;
        color: #FFFFFF;
        font-weight: 400;
        letter-spacing: 0.01em;
        opacity: 0.85;
        border-left: 3px solid {COLOR_GOLD};
        padding-left: 1.2rem;
        margin-top: 0.8rem;
        line-height: 1.4;
    }}

    /* Cards de Conteúdo */
    .pricetax-card {{
        background: {COLOR_CARD_BG};
        border: 1px solid {COLOR_BORDER};
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}

    .pricetax-card-header {{
        font-size: 0.9rem;
        font-weight: 700;
        color: {COLOR_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* Labels e Textos de Formulário (Correção de Ofuscamento) */
    label, .stMarkdown p, .stText {{
        color: {COLOR_TEXT_MAIN} !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }}

    .stMarkdown small {{
        color: {COLOR_TEXT_MUTED} !important;
    }}

    /* Radio Buttons e Checkboxes (Estilo Portal) */
    .stRadio > label {{
        color: {COLOR_BLUE_PORTAL} !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }}

    /* Inputs e Selects */
    .stTextInput > div > div > input, 
    .stSelectbox > div > div > div {{
        background-color: #FFFFFF !important;
        border: 1px solid {COLOR_BORDER} !important;
        border-radius: 8px !important;
        color: {COLOR_TEXT_MAIN} !important;
        padding: 0.5rem 1rem !important;
    }}

    .stTextInput > div > div > input:focus {{
        border-color: {COLOR_PRIMARY} !important;
        box-shadow: 0 0 0 2px rgba(255, 221, 0, 0.2) !important;
    }}

    /* Botões de Ação */
    .stButton > button {{
        width: 100%;
        background-color: {COLOR_PRIMARY} !important;
        color: {COLOR_SECONDARY} !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.025em !important;
        transition: all 0.2s ease !important;
    }}

    .stButton > button:hover {{
        background-color: #FACC15 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}

    /* Tabs Modernas */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
        background-color: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 45px;
        background-color: #FFFFFF;
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px 8px 0 0;
        padding: 0 1.5rem;
        color: {COLOR_TEXT_MUTED};
        font-weight: 600;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {COLOR_BLUE_PORTAL} !important;
        color: #FFFFFF !important;
        border-color: {COLOR_BLUE_PORTAL} !important;
    }}

    /* Tabelas e Dataframes */
    .dataframe {{
        border: 1px solid {COLOR_BORDER} !important;
        border-radius: 8px !important;
    }}

    .dataframe th {{
        background-color: {COLOR_SECONDARY} !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }}

    .dataframe td {{
        padding: 10px !important;
        color: {COLOR_TEXT_MAIN} !important;
    }}

    /* Mensagens de Feedback */
    .stAlert {{
        border-radius: 8px !important;
        border: none !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }}

    /* Ocultar elementos desnecessários */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True
)

# =============================================================================
# RECONSTRUÇÃO DA LÓGICA (MANTENDO 100% DAS FUNÇÕES)
# =============================================================================

# (O restante do código original deve ser mantido aqui para não quebrar nada)
# Vou ler o backup para restaurar as funções originais e apenas aplicar o novo CSS.

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


@st.cache_data(show_spinner=False, ttl=300)  # Cache por 5 minutos apenas
def load_tipi_base() -> pd.DataFrame:
    """
    Carrega a planilha de regras TIPI IBS/CBS.
    Procura em múltiplos caminhos possíveis e normaliza as colunas.
    """
    # Lista de caminhos possíveis para localizar a planilha TIPI
    # Tenta múltiplos locais para garantir compatibilidade (local, Streamlit Cloud, etc)
    paths = [
        Path(TIPI_DEFAULT_NAME),  # Diretório atual (desenvolvimento local)
        Path.cwd() / TIPI_DEFAULT_NAME,  # Working directory (Streamlit Cloud)
        Path(ALT_TIPI_NAME),  # Nome alternativo da planilha
        Path.cwd() / ALT_TIPI_NAME,
    ]
    
    # Adicionar caminho relativo ao arquivo app.py (se disponível)
    try:
        paths.append(Path(__file__).parent / TIPI_DEFAULT_NAME)
        paths.append(Path(__file__).parent / ALT_TIPI_NAME)
    except Exception:
        pass  # __file__ pode não estar disponível em alguns ambientes

    # Tentar carregar planilha do primeiro caminho válido encontrado
    df = None
    for p in paths:
        if p.exists():
            df = pd.read_excel(p)
            break  # Sucesso! Parar busca

    # Se nenhum arquivo foi encontrado, retornar DataFrame vazio
    if df is None:
        return pd.DataFrame()

    # Normalizar nomes de colunas para maiúsculas (padronização)
    df = normalize_cols_upper(df)
    
    # Validar coluna obrigatória NCM
    if "NCM" not in df.columns:
        return pd.DataFrame()  # Planilha inválida

    # Criar coluna NCM_DIG (8 dígitos numéricos) se não existir
    # Remove caracteres não numéricos e preenche com zeros à esquerda
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
    # Garantir existência de todas as colunas obrigatórias
    # Se alguma coluna não existir, criar com valor vazio
    for c in required:
        if c not in df.columns:
            df[c] = ""  # Valor padrão vazio

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
# INICIALIZAÇÃO DO MOTOR DE BENEFÍCIOS FISCAIS
# =============================================================================

BENEFICIOS_ENGINE = None

if BENEFICIOS_DISPONIVEL:
    try:
        # Procurar planilha de benefícios
        beneficios_paths = [
            Path("BDBENEF_PRICETAX_2026.xlsx"),
            Path.cwd() / "BDBENEF_PRICETAX_2026.xlsx",
        ]
        try:
            beneficios_paths.append(Path(__file__).parent / "BDBENEF_PRICETAX_2026.xlsx")
        except Exception:
            pass
        
        planilha_encontrada = None
        for p in beneficios_paths:
            if p.exists():
                planilha_encontrada = str(p)
                break
        
        if planilha_encontrada:
            BENEFICIOS_ENGINE = init_engine(planilha_encontrada)
            print(f"✅ Motor de benefícios fiscais inicializado: {planilha_encontrada}")
        else:
            print("⚠️ Planilha de benefícios não encontrada. Funcionalidade desabilitada.")
            BENEFICIOS_ENGINE = None
    except Exception as e:
        print(f"❌ Erro ao inicializar motor de benefícios: {e}")
        import traceback
        traceback.print_exc()
        BENEFICIOS_ENGINE = None

# =============================================================================
# CARREGAMENTO DA BASE DE CLASSIFICAÇÃO TRIBUTÁRIA
# =============================================================================

CLASSIF_NAME = "classificacao_tributaria.xlsx"


@st.cache_data(show_spinner=False)
def load_classificacao_base() -> pd.DataFrame:
    """
    Carrega a planilha de classificação tributária.
    Retorna DataFrame com todos os códigos cClassTrib.
    """
    paths = [
        Path(CLASSIF_NAME),
        Path.cwd() / CLASSIF_NAME,
    ]
    try:
        paths.append(Path(__file__).parent / CLASSIF_NAME)
    except Exception:
        pass

    df = None
    loaded_from = None
    
    for p in paths:
        if p.exists():
            try:
                df = pd.read_excel(p, sheet_name="Classificação Tributária")
                loaded_from = str(p)
                break
            except Exception as e:
                continue

    if df is None or df.empty:
        return pd.DataFrame()

    # Garantir que as colunas esperadas existem
    required_cols = [
        "Código da Classificação Tributária",
        "Descrição da Classificação Tributária",
        "Redução IBS (%)",
        "Redução CBS (%)",
        "Tipo de Alíquota",
    ]
    
    for col in required_cols:
        if col not in df.columns:
            return pd.DataFrame()
    
    return df.copy()


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
    # =========================================================================
    # APENAS OPERAÇÕES NÃO ONEROSAS (410999)
    # =========================================================================
    # IMPORTANTE: Vendas normais (5102, 6102, etc) foram REMOVIDAS deste mapa
    # para permitir que a verificação de regime IVA (RED_60, ALIQ_ZERO) 
    # tenha PRIORIDADE 1 na função guess_cclasstrib()
    #
    # Fluxo correto:
    # 1. Verifica regime IVA (RED_60 → 200034, ALIQ_ZERO → 200003)
    # 2. Verifica CFOP especial (410999 para brindes/doações)
    # 3. Regra genérica (000001 para vendas normais)
    
    # Brindes, doações, bonificações
    "5910": "410999",
    "6910": "410999",
    "7910": "410999",
    
    # Amostras grátis
    "5911": "410999",
    "6911": "410999",
    "7911": "410999",
    
    # Outras saídas não especificadas
    "5949": "410999",
    "6949": "410999",
    "7949": "410999",
    
    # Remessas em consignação
    "5917": "410999",
    "6917": "410999",
    "7917": "410999",
    
    # Remessas para conserto/reparo (sem transferência de propriedade)
    "5915": "410999",
    "6915": "410999",
    "7915": "410999",
    
    # Remessas para demonstração
    "5912": "410999",
    "6912": "410999",
    "7912": "410999",
    
    # Remessas para exposição ou feira
    "5914": "410999",
    "6914": "410999",
    "7914": "410999",
}

for _cfop in CFOP_NAO_ONEROSOS_410999:
    CFOP_CCLASSTRIB_MAP.setdefault(_cfop, "410999")


def guess_cclasstrib(cst: Any, cfop: Any, regime_iva: str) -> tuple[str, str]:
    """
    Sugere um código de Classificação Tributária (cClassTrib) para NFe conforme LC 214/2025.
    
    🔹 REGRAS FUNDAMENTAIS (LC 214/2025):
    - cClassTrib NÃO depende do valor da alíquota, e sim da NATUREZA JURÍDICA da operação
    - Série 000xxx → tributação cheia (sem benefício)
    - Série 200xxx → operação onerosa com REDUÇÃO LEGAL
    - Série 410xxx → imunidade, isenção ou não incidência
    
    🍞 ALIMENTOS - Classificação Correta:
    1. Cesta Básica Nacional (Anexo I) → 200003 (redução 100%, alíquota zero)
    2. Cesta Básica Estendida (Anexo VII) → 200034 (redução 60%)
    3. Alimentos sem benefício → 000001 (tributação padrão)
    
    A sugestão é baseada em:
    1. Regime IVA do produto (ALIQ_ZERO_CESTA_BASICA_NACIONAL, RED_60_*, etc)
    2. Mapeamento fixo de CFOPs específicos (via CFOP_CCLASSTRIB_MAP)
    3. Regras genéricas para saídas tributadas (CFOPs 5xxx/6xxx/7xxx + CST normal)
    4. Identificação de operações não onerosas (410999)
    
    Parâmetros:
        cst (Any): Código de Situação Tributária (CST) do produto
        cfop (Any): Código Fiscal de Operações e Prestações (CFOP)
        regime_iva (str): Regime de tributação IVA do produto (CRÍTICO para classificação correta)
    
    Retorna:
        tuple[str, str]: (código_cClassTrib, mensagem_explicativa)
    
    Exemplos:
        - Arroz (Anexo I) + CFOP 5102 → ("200003", "Cesta Básica Nacional - redução 100%")
        - Carne bovina (Anexo VII) + CFOP 5102 → ("200034", "Cesta Estendida - redução 60%")
        - Refrigerante + CFOP 5102 → ("000001", "tributação regular")
        - CFOP 5910 (brinde) → ("410999", "operação não onerosa")
    """
    # Limpar e normalizar entradas
    cst_clean = re.sub(r"\D+", "", str(cst or ""))
    cfop_clean = re.sub(r"\D+", "", str(cfop or ""))
    regime_iva_upper = str(regime_iva or "").upper().strip()

    if not cfop_clean:
        return "", "Informe o CFOP da operação de venda para sugerir o cClassTrib padrão."

    # =========================================================================
    # PRIORIDADE 1: CFOP não oneroso (prevalece sobre tudo)
    # =========================================================================
    # REGRA CRÍTICA: Operações não onerosas (remessas, brindes, doações) têm
    # prioridade MÁXIMA, pois a NATUREZA DA OPERAÇÃO prevalece sobre o produto.
    # 
    # Exemplo: Arroz em remessa para conserto (5915) → 410999 (não onerosa)
    #          mesmo que arroz tenha RED_60 na venda normal
    
    if cfop_clean in CFOP_CCLASSTRIB_MAP:
        code = CFOP_CCLASSTRIB_MAP[cfop_clean]
        
        # Se for operação não onerosa (410999), explicar claramente
        if code == "410999":
            msg = (
                f"⚠️ Operação não onerosa (CFOP {cfop_clean}) → cClassTrib {code}. "
                "Não gera débito de IBS/CBS. "
                "Exemplos: brindes, doações, remessas temporárias, amostras grátis."
            )
        else:
            msg = (
                f"Regra padrão PRICETAX: CFOP {cfop_clean} → "
                f"cClassTrib {code} (conforme matriz PRICETAX)."
            )
        return code, msg
    
    # =========================================================================
    # PRIORIDADE 2: REGIME IVA (baseado na natureza jurídica do produto)
    # =========================================================================
    # Esta regra se aplica APENAS para operações ONEROSAS (vendas normais)
    # cClassTrib depende do FUNDAMENTO LEGAL, não da alíquota
    
    # 2.1) Cesta Básica Nacional (Anexo I) - Redução 100% (alíquota zero)
    if "ALIQ_ZERO_CESTA_BASICA_NACIONAL" in regime_iva_upper:
        # ❌ ERRO CRÍTICO: usar 000001 para cesta básica
        # ✅ CORRETO: usar 200003 (operação onerosa com redução legal)
        code = "200003"
        msg = (
            f"✅ Cesta Básica Nacional (Anexo I LC 214/25) → cClassTrib {code}. "
            "Operação onerosa com redução de 100% (alíquota zero). "
            "Fundamento: LC 214/2025, Anexo I."
        )
        return code, msg
    
    # 2.2) Redução 60% (Cesta Estendida - Anexo VII ou Essencialidade)
    if "RED_60" in regime_iva_upper:
        # ❌ ERRO CRÍTICO: usar 000001 para produtos com redução 60%
        # ✅ CORRETO: usar 200034 (operação onerosa com redução de 60%)
        code = "200034"
        
        # Identificar se é alimento (Anexo VII) ou essencialidade (arts. 137-145)
        if "ALIMENTO" in regime_iva_upper:
            fundamento = "Anexo VII (Cesta Básica Estendida)"
        else:
            fundamento = "arts. 137 a 145 (essencialidade)"
        
        msg = (
            f"✅ Redução 60% ({fundamento}) → cClassTrib {code}. "
            "Operação onerosa com redução de 60%. "
            f"Fundamento: LC 214/2025, {fundamento}."
        )
        return code, msg
    
    # 2.3) Outras reduções específicas (se houver)
    # Adicionar aqui se surgirem outros regimes com redução

    # =========================================================================
    # PRIORIDADE 3: Regra genérica para saídas tributadas
    # =========================================================================
    # Saída (5, 6 ou 7) com CST de tributação "normal" → 000001 (tributação padrão)
    if cfop_clean[0] in ("5", "6", "7") and cst_clean in {"000", "200", "201", "202", "900"}:
        code = "000001"
        msg = (
            f"Regra genérica: CFOP {cfop_clean} é saída tributada padrão "
            f"→ cClassTrib {code} (tributação regular sem benefício). "
            "Revise se for operação especial (doação, brinde, bonificação, remessa técnica etc.)."
        )
        return code, msg

    # =========================================================================
    # PRIORIDADE 4: Não conseguiu classificar
    # =========================================================================
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
    # Dicionários para armazenar dados extraídos do SPED
    produtos: Dict[str, Dict[str, str]] = {}  # Mapa: COD_ITEM → {NCM, DESCR_ITEM}
    documentos: Dict[str, Dict[str, Any]] = {}  # Mapa: DOC_KEY → {IND_OPER}
    itens_venda = []  # Lista de itens vendidos (C170)

    # Regex para identificar CFOPs de saída (5xxx, 6xxx, 7xxx)
    cfop_saida_pattern = re.compile(r"^[567]\d{3}$")
    
    # Variável de controle para rastrear o documento atual sendo processado
    current_doc_key: Optional[str] = None

    try:
        file_stream = io.StringIO(file_content)

        for line in file_stream:
            fields = line.strip().split("|")
            if not fields or len(fields) < 2:
                continue

            registro = fields[1]

            # Registro 0200: Cadastro de produtos (mapeia COD_ITEM → NCM)
            if registro == "0200":
                if len(fields) >= 9:
                    cod_item = fields[2]  # Código do produto no ERP
                    descr_item = fields[3]  # Descrição do produto
                    cod_ncm = fields[8]  # NCM (Nomenclatura Comum do Mercosul)
                    produtos[cod_item] = {"NCM": cod_ncm, "DESCR_ITEM": descr_item}

            # Registro C100: Cabeçalho do documento fiscal (NF-e, NFC-e, etc)
            elif registro == "C100":
                ind_oper = fields[2] if len(fields) > 2 else ""  # 0=Entrada, 1=Saída
                
                # Processar apenas documentos de SAÍDA (IND_OPER = 1)
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

            # Registro C170: Itens do documento fiscal (produtos vendidos)
            elif (
                registro == "C170"
                and current_doc_key  # Garante que estamos dentro de um documento válido
                and documentos.get(current_doc_key, {}).get("IND_OPER") == "1"  # Apenas saídas
            ):
                if len(fields) >= 12:
                    cod_item = fields[3]  # Código do produto (referencia |0200|)
                    vl_item_str = fields[7].replace(",", ".")  # Valor do item (normalizar decimal)
                    cfop = fields[11]  # CFOP da operação

                    try:
                        vl_item = float(vl_item_str)
                    except ValueError:
                        continue

                    # Filtrar apenas CFOPs de saída (5xxx, 6xxx, 7xxx)
                    # Ignora entradas (1xxx, 2xxx, 3xxx) automaticamente
                    if cfop_saida_pattern.match(cfop):
                        itens_venda.append(
                            {
                                "COD_ITEM": cod_item,
                                "VL_ITEM": vl_item,
                                "CFOP": cfop,
                                "DOC_KEY": current_doc_key,
                            }
                        )

            # Registros que indicam fim do bloco C100 (resetar documento atual)
            elif registro in ("C190", "C300", "D100", "E100"):
                current_doc_key = None  # Limpar contexto do documento

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
        "Download CFOP x cClassTrib",
        "Análise de XML",
        "LC 214/2025",
    ]
)

# =============================================================================
# ABA: LC 214/2025 (PLATAFORMA DE INTELIGÊNCIA JURÍDICA INTEGRAL)
# =============================================================================
with tabs[5]:
    st.markdown(
        f"""
        <div class="pricetax-card">
            <div class="pricetax-card-header">
                <span style="font-size: 1.5rem;">⚖️</span> LC 214/2025 — Inteligência e Consulta Integral
            </div>
            <p style="color: {COLOR_TEXT_MUTED}; margin-bottom: 1rem;">
                Plataforma profissional de consulta à Reforma Tributária. 544 artigos + 36 blocos comentados + 50 Q&A.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Navegação por Abas Internas (UX de Alto Nível)
    lc_tabs = st.tabs(["🔍 Consulta por Artigo/Palavra", "📚 Blocos Temáticos (32)", "📖 Texto Integral da Lei", "❓ Central de Q&A (50 Questões)"])

    # Banco de Dados de Artigos (Mapeamento Integral - 544 Artigos)
    # Carregamento dinâmico do banco de dados jurídico PriceTax
    import json
    import os
    
    articles_json_path = os.path.join(os.path.dirname(__file__), 'articles_db.json')
    if os.path.exists(articles_json_path):
        with open(articles_json_path, 'r', encoding='utf-8') as f:
            artigos_db = json.load(f)
    else:
        # Fallback caso o arquivo não exista (não deve ocorrer após o push)
        artigos_db = {"1": {"titulo": "Erro", "texto": "Banco de dados não encontrado. Por favor, verifique o deploy.", "nota": ""}}

    # Adicionar notas técnicas automáticas para os principais artigos
    notas_fixas = {
        "1": "Define a base do IVA Dual no Brasil.",
        "2": "Regra geral de incidência sobre o consumo.",
        "4": "Atenção: A incidência sobre bens imateriais (softwares/ativos digitais) é um ponto crítico de 2026.",
        "11": "Princípio do Destino: A arrecadação pertence ao local do consumo.",
        "31": "Impacto no Fluxo de Caixa: O imposto é retido na fonte pagadora automaticamente (Split Payment).",
        "47": "Crédito Financeiro: Só gera crédito se houver o efetivo pagamento na etapa anterior.",
        "143": "Foco Social: Itens essenciais da Cesta Básica sem carga tributária.",
        "342": "Ano Teste: Período crucial para ajuste de sistemas de ERP e emissão de notas.",
        "409": "Sin Tax: Tributação extrafiscal para desestímulo de consumo."
    }
    for art_id, nota in notas_fixas.items():
        if art_id in artigos_db:
            artigos_db[art_id]["nota"] = nota

    with lc_tabs[0]:
        c1, c2 = st.columns([1, 2])
        with c1:
            art_search = st.text_input("Digite o número do Artigo (1-544):", placeholder="Ex: 31", key="art_search_input")
        with c2:
            key_search = st.text_input("Busca Semântica / Palavra-chave:", placeholder="Ex: split payment, cashback...", key="key_search_input")

        # Lógica de Busca
        result_art = None
        if art_search and art_search in artigos_db:
            result_art = art_search
        elif key_search:
            for art, data in artigos_db.items():
                if key_search.lower() in data["texto"].lower() or key_search.lower() in data["titulo"].lower():
                    result_art = art
                    break

        if result_art:
            data = artigos_db[result_art]
            st.markdown(f"### Artigo {result_art}: {data['titulo']}")
            st.markdown(f'<div style="background:white; padding:20px; border:1px solid {COLOR_BORDER}; border-radius:8px; color:{COLOR_TEXT_MAIN}; font-size:1.1rem;">{data["texto"]}</div>', unsafe_allow_html=True)
            
            sc1, sc2 = st.columns(2)
            # Verificar se 'nota' existe antes de exibir
            if "nota" in data and data["nota"]:
                sc1.markdown(f'<div style="border-left:4px solid {COLOR_BLUE_PORTAL}; background:rgba(0,86,179,0.05); padding:15px; border-radius:8px; margin-top:10px;"><strong>Nota PriceTax:</strong><br>{data["nota"]}</div>', unsafe_allow_html=True)
            sc2.markdown(f'<div style="border-left:4px solid {COLOR_GOLD}; background:rgba(255,221,0,0.05); padding:15px; border-radius:8px; margin-top:10px;"><strong>Correlação:</strong><br>Vinculado à EC 132/2023 e Art. 156-A da CF/88.</div>', unsafe_allow_html=True)
        else:
            if art_search or key_search:
                st.warning("Artigo não mapeado nesta versão rápida. Tente os artigos chave: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 31, 47, 143, 342, 409 ou 544.")

    with lc_tabs[1]:
        # Nova aba: Blocos Temáticos
        from lc214_blocos_nav import render_blocos_navigation
        render_blocos_navigation()

    with lc_tabs[2]:
        st.subheader("Texto Integral da Lei Complementar nº 214/2025")
        st.info("Abaixo você pode visualizar a lei na íntegra. Use a barra de rolagem para navegar por todos os 544 artigos.")
        
        # Gerar o texto completo a partir do banco de dados para exibição integral
        full_text_content = ""
        for art_id in sorted(artigos_db.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            full_text_content += f"**{artigos_db[art_id]['titulo']}**\n\n{artigos_db[art_id]['texto']}\n\n---\n\n"
            
        with st.container(height=700, border=True):
            st.markdown(full_text_content)
        st.caption("Base de dados atualizada conforme legislação oficial da Reforma Tributária.")

    with lc_tabs[3]:
        st.subheader("Central de Q&A — 50 Perguntas e Respostas")
        qa_filter = st.text_input("Filtrar perguntas do Q&A:", placeholder="Ex: crédito, transição...", key="qa_filter_input")
        
        qa_list = [
            {"q": "O que é o IVA Dual?", "a": "É o sistema composto pelo IBS (Estados/Municípios) e pela CBS (União), com base de cálculo e regras harmonizadas."},
            {"q": "Quando começa a transição?", "a": "Em 2026, com alíquotas de 0,1% (IBS) e 0,9% (CBS)."},
            {"q": "O que é o Split Payment?", "a": "É o recolhimento automático do imposto no ato do pagamento eletrônico, segregando o tributo do valor líquido."},
            {"q": "Haverá crédito sobre bens de uso e consumo?", "a": "Sim, a regra é o crédito financeiro amplo, desde que haja o pagamento do imposto na etapa anterior."},
            {"q": "O que é o Imposto Seletivo?", "a": "Um tributo extrafiscal sobre produtos nocivos à saúde ou ao meio ambiente (Sin Tax)."},
            {"q": "Como funciona o Cashback?", "a": "Devolução de parte do imposto pago para famílias de baixa renda cadastradas no CadÚnico."},
            {"q": "As exportações são tributadas?", "a": "Não, as exportações são imunes para garantir a competitividade do produto brasileiro."},
            {"q": "O IBS substitui quais impostos?", "a": "O ICMS (Estadual) e o ISS (Municipal)."},
            {"q": "A CBS substitui quais impostos?", "a": "O PIS e a COFINS (Federais)."},
            {"q": "O que é o Comitê Gestor do IBS?", "a": "Entidade nacional responsável por centralizar a arrecadação e distribuição do IBS entre Estados e Municípios."},
            {"q": "Como será a cobrança no destino?", "a": "O imposto pertencerá ao ente federativo onde o bem ou serviço for consumido."},
            {"q": "O que são regimes diferenciados?", "a": "Setores com redução de alíquota (ex: 60% para saúde e educação)."},
            {"q": "O que são regimes específicos?", "a": "Setores com regras próprias de base de cálculo e alíquota (ex: combustíveis e serviços financeiros)."},
            {"q": "Haverá incidência sobre heranças?", "a": "Não, o IBS/CBS incide apenas sobre o consumo. O ITCMD continua regendo heranças."},
            {"q": "Como fica o Simples Nacional?", "a": "As empresas podem optar por recolher o IBS/CBS por fora do Simples para garantir créditos aos seus clientes."},
            {"q": "O que é o crédito financeiro?", "a": "Diferente do crédito físico, permite abater o imposto pago em qualquer aquisição necessária à atividade."},
            {"q": "Qual o papel do CGIBS?", "a": "Harmonizar as normas e julgar processos administrativos do IBS."},
            {"q": "O que é the alíquota de referência?", "a": "Valor fixado pelo Senado para garantir que a carga tributária total não aumente."},
            {"q": "Como funciona a devolução ao turista estrangeiro?", "a": "Turistas podem solicitar o estorno do IBS/CBS pago em compras no Brasil ao sair do país."},
            {"q": "O que é o Sin Tax?", "a": "Apelido do Imposto Seletivo, focado em desestimular o consumo de itens prejudiciais."},
            {"q": "O que acontece com o IPI?", "a": "O IPI será extinto, exceto para produtos que tenham industrialização na Zona Franca de Manaus."},
            {"q": "Como funciona a não cumulatividade plena?", "a": "Permite o crédito de qualquer imposto pago na aquisição de bens e serviços para a atividade econômica."},
            {"q": "O que é o princípio da neutralidade?", "a": "Garante que o imposto não influencie as decisões de produção e consumo."},
            {"q": "Haverá alíquota uniforme?", "a": "Sim, cada ente federativo fixará sua alíquota, que será a mesma para todos os bens e serviços."},
            {"q": "O que é o período de teste?", "a": "O ano de 2026, onde as alíquotas serão mínimas para testar a operacionalização do sistema."},
            {"q": "Como será a devolução de créditos acumulados?", "a": "A lei prevê prazos rápidos para a devolução de créditos que não puderem ser compensados."},
            {"q": "O que é a cesta básica nacional?", "a": "Lista de produtos essenciais que terão alíquota zero de IBS e CBS."},
            {"q": "Como fica a Zona Franca de Manaus?", "a": "Terá tratamento diferenciado para manter sua competitividade e diferencial comparativo."},
            {"q": "O que é o imposto por fora?", "a": "O IBS e a CBS não integram sua própria base de cálculo nem a base um do outro."},
            {"q": "Como será a fiscalização?", "a": "Será integrada entre a Receita Federal e o Comitê Gestor do IBS."},
            {"q": "O que é o cashback de energia elétrica?", "a": "Devolução de imposto sobre a conta de luz para famílias de baixa renda."},
            {"q": "Haverá imposto sobre serviços digitais?", "a": "Sim, a lei prevê a tributação de plataformas e serviços de streaming."},
            {"q": "Como funciona a responsabilidade do marketplace?", "a": "Plataformas digitais podem ser responsáveis pelo recolhimento do imposto de seus vendedores."},
            {"q": "O que é o regime de caixa?", "a": "Possibilidade de recolher o imposto apenas no recebimento, prevista para alguns setores específicos."},
            {"q": "Como ficam os benefícios fiscais atuais?", "a": "Serão extintos gradualmente durante o período de transição."},
            {"q": "O que é a trava da carga tributária?", "a": "Mecanismo que reduz as alíquotas se a arrecadação superar a média histórica."},
            {"q": "Como será a tributação de imóveis?", "a": "Terá regime específico com redutores de base de cálculo."},
            {"q": "O que é o IBS/CBS na importação?", "a": "Cobrado no desembaraço aduaneiro, com as mesmas alíquotas do mercado interno."},
            {"q": "Como funciona o crédito presumido?", "a": "Concedido em situações específicas, como na aquisição de produtos de produtores rurais não contribuintes."},
            {"q": "O que é a harmonização de bases?", "a": "IBS e CBS terão sempre a mesma base de cálculo e as mesmas hipóteses de incidência."},
            {"q": "Como será a transição da arrecadação?", "a": "Ocorrerá ao longo de 50 anos para não prejudicar o caixa de Estados e Municípios."},
            {"q": "O que é o fundo de desenvolvimento regional?", "a": "Fundo para compensar o fim dos incentivos fiscais e promover o desenvolvimento."},
            {"q": "Como fica o IPVA?", "a": "Passará a incidir também sobre veículos aquáticos e aéreos de luxo."},
            {"q": "Como fica o ITCMD?", "a": "Terá alíquotas progressivas obrigatórias em todo o país."},
            {"q": "O que é a CBS monofásica?", "a": "Regime aplicado a combustíveis, onde o imposto é cobrado uma única vez na cadeia."},
            {"q": "Como funciona a consulta formal?", "a": "O contribuinte poderá consultar o CGIBS sobre a interpretação da lei com efeito vinculante."},
            {"q": "O que é o contencioso administrativo?", "a": "Julgamento de disputas tributárias de forma unificada para o IBS."},
            {"q": "Como será a nota fiscal eletrônica?", "a": "Haverá um modelo nacional unificado para IBS e CBS."},
            {"q": "O que é o padrão de conformidade?", "a": "Programas de estímulo à autorregularização e conformidade fiscal."},
            {"q": "Qual o impacto final para o consumidor?", "a": "Maior transparência, com o valor real do imposto destacado na nota fiscal."}
        ]
        
        # Exibindo as perguntas de forma organizada
        for i, item in enumerate(qa_list):
            if not qa_filter or qa_filter.lower() in item["q"].lower() or qa_filter.lower() in item["a"].lower():
                with st.expander(f"Q{i+1}: {item['q']}"):
                    st.info(item["a"])

    st.markdown(
        f"""
        <div style="margin-top: 2rem; padding: 1rem; border-top: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT_MUTED}; font-size: 0.8rem; text-align: center;">
            Plataforma de Inteligência Jurídica PriceTax — Baseada na LC 214/2025.
        </div>
        """,
        unsafe_allow_html=True
    )

# =============================================================================
# CARREGAMENTO DA PLANILHA CFOP x cClassTrib
# =============================================================================

@st.cache_data(show_spinner=False)
def load_cfop_cclasstrib() -> pd.DataFrame:
    """
    Carrega a planilha de correlação CFOP x cClassTrib.
    Retorna DataFrame com CFOP, descrição, cClassTrib e alíquotas.
    """
    paths = [
        Path("CFOP_CCLASSTRIB.xlsx"),
        Path.cwd() / "CFOP_CCLASSTRIB.xlsx",
    ]
    try:
        paths.append(Path(__file__).parent / "CFOP_CCLASSTRIB.xlsx")
    except Exception:
        pass

    df = None
    for p in paths:
        if p.exists():
            try:
                df = pd.read_excel(p, sheet_name="Correlação", skiprows=2)
                break
            except Exception:
                continue

    if df is None or df.empty:
        return pd.DataFrame()

    return df.copy()

df_cfop_class = load_cfop_cclasstrib()

# =============================================================================
# ABA 1 - CONSULTA NCM
# =============================================================================

with tabs[0]:
    st.markdown(
        """
        <div class="pricetax-card">
            <div class="pricetax-card-header">Consulta Inteligente de Tributação IBS/CBS</div>
            <div style="font-size:0.95rem;color:#CCCCCC;line-height:1.6;">
                Utilize este painel para consultar a tributação de produtos e operações:<br><br>
                • <strong>NCM + CFOP:</strong> Consulta completa com NCM e opcionalmente CFOP<br>
                • <strong>Somente CFOP:</strong> Tributação padrão da operação fiscal<br>
                • <strong>Descrição:</strong> Busca por palavras-chave (ex: leite, arroz, computador)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Seletor de modo de busca
    modo_busca = st.radio(
        "Selecione o tipo de busca:",
        ["NCM + CFOP", "Somente CFOP", "Descrição do Produto"],
        horizontal=True,
    )
    
    # =============================================================================
    # MODO 1: NCM + CFOP (CÓDIGO ORIGINAL - PRESERVADO)
    # =============================================================================
    if modo_busca == "NCM + CFOP":
        col1, col2, col3 = st.columns([3, 1.4, 1])
        with col1:
            ncm_input = st.text_input(
                "NCM do produto",
                placeholder="Ex.: 16023220 ou 16.02.32.20",
                help="Informe o NCM completo (8 dígitos), com ou sem pontos.",
            )
        with col2:
            cfop_input = st.text_input(
                "CFOP (opcional)",
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
                cst_ibscbs = row.get("CST_IBSCBS", "")
                flag_alim = row.get("FLAG_ALIMENTO", "NAO")
                flag_dep = row.get("FLAG_DEPENDE_DESTINACAO", "NAO")

                # =============================================================================
                # CONSULTAR BENEFÍCIOS FISCAIS (FONTE DA VERDADE)
                # =============================================================================
                beneficios_info = None
                regime = "TRIBUTACAO_PADRAO"  # Padrão
                ibs_uf = 0.10  # Padrão 2026
                ibs_mun = 0.0  # Ano teste não tem municipal
                cbs = 0.90  # Padrão 2026
                fonte = "LC 214/25, regra geral art. 10 e disposiçoes do ADCT art. 125 (ano teste)"
                
                if BENEFICIOS_ENGINE:
                    try:
                        beneficios_info = consulta_ncm(BENEFICIOS_ENGINE, ncm_fmt)
                        
                        # APLICAR BENEFÍCIOS (SE HOUVER)
                        if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                            enq = beneficios_info['enquadramentos'][0]
                            reducao_pct = enq['reducao_aliquota']
                            anexo = enq['anexo']
                            
                            # Aplicar redução
                            if reducao_pct == 100:
                                ibs_uf = 0.0
                                ibs_mun = 0.0
                                cbs = 0.0
                                regime = "ALIQ_ZERO_CESTA_BASICA_NACIONAL"
                                fonte = f"LC 214/25, {anexo}"
                            elif reducao_pct == 60:
                                ibs_uf = 0.04  # 40% de 0,10
                                ibs_mun = 0.0
                                cbs = 0.36  # 40% de 0,90
                                regime = "RED_60_ESSENCIALIDADE"
                                fonte = f"LC 214/25, {anexo}"
                            else:
                                fator = (100 - reducao_pct) / 100
                                ibs_uf = 0.10 * fator
                                ibs_mun = 0.0
                                cbs = 0.90 * fator
                                regime = f"RED_{int(reducao_pct)}"
                                fonte = f"LC 214/25, {anexo}"
                            
                            print(f"✅ Benefício aplicado: {anexo} ({reducao_pct}% redução)")
                        else:
                            print(f"ℹ️ Nenhum benefício encontrado - Tributação padrão 1,00%")
                            
                    except Exception as e:
                        print(f"⚠️ Erro ao consultar benefícios: {e}")
                
                # Calcular total
                total_iva = ibs_uf + ibs_mun + cbs
                
                # Calcular cClassTrib
                cclastrib_venda_code, cclastrib_venda_msg = guess_cclasstrib(
                    cst=cst_ibscbs, cfop="5102", regime_iva=regime
                )
                class_info_venda = get_class_info_by_code(cclastrib_venda_code)
                
                # SOBRESCREVER DESCRIÇÃO com base no anexo (se houver benefícios)
                if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                    enq = beneficios_info['enquadramentos'][0]
                    desc_anexo = enq['descricao_anexo']
                    # Atualizar descrição do cClassTrib com a descrição do anexo
                    if class_info_venda:
                        class_info_venda = class_info_venda.copy()
                        class_info_venda['DESC_CLASS'] = desc_anexo
                
                # Se CFOP foi informado E é diferente de venda padrão
                cfop_clean_main = re.sub(r"\D+", "", cfop_input or "")
                cclastrib_cfop_code = ""
                cclastrib_cfop_msg = ""
                class_info_cfop = None
                cfop_is_different = False
                
                if cfop_clean_main and cfop_clean_main not in ["5102", "6102", "7102"]:
                    cfop_is_different = True
                    cclastrib_cfop_code, cclastrib_cfop_msg = guess_cclasstrib(
                        cst=cst_ibscbs, cfop=cfop_input, regime_iva=regime
                    )
                    class_info_cfop = get_class_info_by_code(cclastrib_cfop_code)
                    # Sobrescrever descrição do CFOP também
                    if beneficios_info and beneficios_info['total_enquadramentos'] > 0 and class_info_cfop:
                        class_info_cfop = class_info_cfop.copy()
                        class_info_cfop['DESC_CLASS'] = desc_anexo
                
                # Compatibilidade
                cclastrib_code = cclastrib_venda_code
                class_info = class_info_venda
                
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
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                # =============================================================================
                # EXIBIR BENEFÍCIOS FISCAIS (SE HOUVER)
                # =============================================================================
                if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                    st.markdown("### Benefícios Fiscais Identificados")
                    
                    if beneficios_info['multi_enquadramento']:
                        st.warning(
                            f"**Múltiplos Enquadramentos Possíveis:** Este NCM se enquadra em "
                            f"{beneficios_info['total_enquadramentos']} anexos diferentes. "
                            f"Verifique qual se aplica ao seu caso: {', '.join(beneficios_info['lista_anexos'])}"
                        )
                    
                    for idx, enq in enumerate(beneficios_info['enquadramentos'], 1):
                        anexo = enq['anexo']
                        reducao_pct = enq['reducao_aliquota']
                        descricao = enq['descricao_anexo']
                        
                        # Cor baseada na redução
                        if reducao_pct == 100:
                            cor_badge = COLOR_SUCCESS
                            texto_reducao = "ALÍQUOTA ZERO (100%)"
                        elif reducao_pct == 60:
                            cor_badge = "#3B82F6"  # Azul
                            texto_reducao = "REDUÇÃO DE 60%"
                        else:
                            cor_badge = COLOR_GOLD
                            texto_reducao = f"REDUÇÃO DE {reducao_pct}%"
                        
                        st.markdown(
                            f"""
                            <div class="pricetax-card" style="border-left: 4px solid {cor_badge}; margin-top: 1rem;">
                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                                    <div style="font-size: 1.1rem; font-weight: 600; color: {COLOR_GOLD};">
                                        {anexo}
                                    </div>
                                    <div style="background: {cor_badge}; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.85rem; font-weight: 600;">
                                        {texto_reducao}
                                    </div>
                                </div>
                                <div style="font-size: 0.9rem; color: {COLOR_GRAY_LIGHT}; line-height: 1.5;">
                                    {descricao}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    
                    st.markdown("---")

                # =============================================================================
                # ALÍQUOTAS EFETIVAS (SIMPLIFICADO)
                # =============================================================================
                ibs_efetivo = ibs_uf + ibs_mun
                cbs_efetivo = cbs
                total_iva = ibs_efetivo + cbs_efetivo
        
                st.markdown("### Alíquotas Efetivas 2026 (Ano Teste)")
                st.markdown(
                    f"""
                    <div class="metric-container">
                        <div class="metric-box">
                            <div class="metric-label">IBS (UF + Município)</div>
                            <div class="metric-value">{pct_str(ibs_efetivo)}</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-label">CBS (Federal)</div>
                            <div class="metric-value">{pct_str(cbs_efetivo)}</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-label">Carga Total IVA</div>
                            <div class="metric-value" style="color: {COLOR_GOLD};">{pct_str(total_iva)}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                # Nota explicativa
                st.caption(
                    "**Ano teste 2026:** Alíquotas reduzidas (IBS 0,1% e CBS 0,9%). "
                    "Benefícios fiscais já aplicados nos valores acima."
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
                    # Sempre mostrar cClassTrib de venda
                    if cclastrib_venda_code:
                        desc_class_venda = class_info_venda["DESC_CLASS"] if class_info_venda else ""
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{cclastrib_venda_code}</span>", unsafe_allow_html=True)
                        if desc_class_venda:
                            st.markdown(f"<span style='font-size:0.85rem;color:{COLOR_GRAY_LIGHT};'>{desc_class_venda}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='font-size:0.8rem;color:{COLOR_GRAY_LIGHT};font-style:italic;'>CFOP de venda onerosa assumido</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>—</span>", unsafe_allow_html=True)
                    
                    # Se CFOP diferente foi informado, mostrar também
                    if cfop_is_different and cclastrib_cfop_code:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"**cClassTrib para CFOP {cfop_clean_main}**")
                        desc_class_cfop = class_info_cfop["DESC_CLASS"] if class_info_cfop else ""
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{cclastrib_cfop_code}</span>", unsafe_allow_html=True)
                        if desc_class_cfop:
                            st.markdown(f"<span style='font-size:0.85rem;color:{COLOR_GRAY_LIGHT};'>{desc_class_cfop}</span>", unsafe_allow_html=True)
                        # Alertar se for não oneroso
                        if cclastrib_cfop_code == "410999":
                            st.markdown(f"<span style='font-size:0.8rem;color:#FFA500;'>⚠️ Operação não onerosa</span>", unsafe_allow_html=True)

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

                # =============================================================================
                # INFORMAÇÕES COMPLEMENTARES (SIMPLIFICADO)
                # =============================================================================
                st.markdown("---")
                st.markdown("### Informações Complementares")

                def clean_txt(v):
                    s = str(v or "").strip()
                    return "" if s.lower() == "nan" else s

                fonte = clean_txt(row.get("FONTE_LEGAL_FINAL"))
                flag_alim = clean_txt(row.get("FLAG_ALIMENTO"))
                flag_dep = clean_txt(row.get("FLAG_DEPENDE_DESTINACAO"))

                # Base legal
                if fonte:
                    st.markdown(f"**Base Legal:** {fonte}")
                
                # Alertas importantes (apenas se relevante)
                alertas = []
                if flag_alim == "SIM":
                    alertas.append("**Produto classificado como alimento** - Verifique enquadramento nos anexos da LC 214/25")
                if flag_dep == "SIM":
                    alertas.append("**Tratamento varia conforme destinação** - Avaliar uso final (consumo, insumo, indústria)")
                
                if alertas:
                    for alerta in alertas:
                        st.info(alerta)
    
        # =============================================================================
        # MODO 2: SOMENTE CFOP
        # =============================================================================
    elif modo_busca == "Somente CFOP":
        col1, col2 = st.columns([2, 1])
        with col1:
            cfop_input = st.text_input(
                "CFOP da operação",
                placeholder="Ex.: 5102",
                max_chars=4,
                help="Informe o CFOP da operação (quatro dígitos).",
                key="cfop_only"
            )
        with col2:
            st.write("")
            consultar_cfop = st.button("Consultar CFOP", type="primary")
        
        if consultar_cfop and cfop_input.strip():
            if df_cfop_class.empty:
                st.error("Arquivo de correlação CFOP x cClassTrib não encontrado.")
            else:
                cfop_clean = int(re.sub(r"\D+", "", cfop_input))
                resultado = df_cfop_class[df_cfop_class["CFOP"] == cfop_clean]
                
                if len(resultado) == 0:
                    st.markdown(
                        f"""
                        <div class="pricetax-card-error">
                            <strong>CFOP informado:</strong> {cfop_input}<br>
                            Não localizamos esse CFOP na base PRICETAX.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    reg = resultado.iloc[0]
                    
                    st.markdown(
                        f"""
                        <div class="pricetax-card" style="margin-top:1.5rem;">
                            <div style="font-size:1.3rem;font-weight:600;color:{COLOR_GOLD};margin-bottom:1rem;">
                                CFOP {cfop_clean} - {reg['Tipo']}
                            </div>
                            <div style="font-size:1rem;color:{COLOR_WHITE};margin-bottom:1rem;">
                                {reg['Descrição Resumida']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    st.markdown("### Tributação Padrão da Operação")
                    
                    col_cfop1, col_cfop2, col_cfop3, col_cfop4 = st.columns(4)
                    
                    with col_cfop1:
                        st.markdown("**Operação Onerosa:**")
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{reg['Operação Onerosa?']}</span>", unsafe_allow_html=True)
                    
                    with col_cfop2:
                        st.markdown("**Incide IBS/CBS:**")
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{reg['Incide IBS/CBS']}</span>", unsafe_allow_html=True)
                    
                    with col_cfop3:
                        st.markdown("**CST IBS/CBS:**")
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{reg['CST IBS/CBS']}</span>", unsafe_allow_html=True)
                    
                    with col_cfop4:
                        st.markdown("**cClassTrib:**")
                        st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{reg['cClassTrib']}</span>", unsafe_allow_html=True)
                    
                    st.markdown("### Alíquotas Padrão")
                    
                    st.markdown(
                        f"""
                        <div class="metric-container">
                            <div class="metric-box">
                                <div class="metric-label">IBS Padrão</div>
                                <div class="metric-value">{pct_str(reg['ALIQ. IBS'] * 100)}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">CBS Padrão</div>
                                <div class="metric-value">{pct_str(reg['ALIQ.CBS'] * 100)}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Carga Total</div>
                                <div class="metric-value">{pct_str((reg['ALIQ. IBS'] + reg['ALIQ.CBS']) * 100)}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    
                    st.info("📌 Esta é a tributação padrão do CFOP. Para produtos específicos com reduções ou regimes especiais, utilize a busca por NCM.")
    
    # =============================================================================
    # MODO 3: DESCRIÇÃO DO PRODUTO
    # =============================================================================
    elif modo_busca == "Descrição do Produto":
        col1, col2 = st.columns([3, 1])
        with col1:
            desc_input = st.text_input(
                "Descrição ou palavras-chave",
                placeholder="Ex.: leite em pó, arroz integral, notebook",
                help="Digite palavras-chave para buscar produtos na TIPI.",
                key="desc_search"
            )
        with col2:
            st.write("")
            buscar_desc = st.button("Buscar", type="primary")
        
        # Inicializar session_state para resultados
        if "desc_resultados" not in st.session_state:
            st.session_state.desc_resultados = None
        if "desc_busca_termo" not in st.session_state:
            st.session_state.desc_busca_termo = ""
        
        if buscar_desc and desc_input.strip():
            # Dicionário completo de sinônimos - 204 mapeamentos (ChatGPT validado)
            sinonimos = {
                'aco': ['ço'],
                'acucar': ['çúcar'],
                'agua': ['água'],
                'agulha': ['agulhas'],
                'algodao': ['algodão'],
                'algodão': ['algodão'],
                'aluminio': ['alumínio'],
                'alumínio': ['alumínio'],
                'areia': ['areia'],
                'arroz': ['arroz'],
                'automovel': ['automóveis'],
                'automóvel': ['automóveis'],
                'aveia': ['aveia'],
                'azeite': ['azeite'],
                'azulejo': ['ladrilhos'],
                'azulejos': ['ladrilhos'],
                'aço': ['ço'],
                'açúcar': ['çúcar'],
                'bacon': ['bacon', 'toucinho'],
                'batata': ['batatas'],
                'batatas': ['batatas'],
                'bezerro': ['bovinos'],
                'bezerros': ['bovinos'],
                'bicicleta': ['bicicletas'],
                'bicicletas': ['bicicletas'],
                'blusa': ['blusas'],
                'blusas': ['blusas'],
                'bode': ['caprinos'],
                'bodes': ['caprinos'],
                'boi': ['bovinos'],
                'bois': ['bovinos'],
                'bolsa': ['bolsas'],
                'bolsas': ['bolsas'],
                'bota': ['calçados'],
                'botas': ['calçados'],
                'botina': ['calçados'],
                'botinas': ['calçados'],
                'cabra': ['caprinos'],
                'cabras': ['caprinos'],
                'cafe': ['café'],
                'café': ['café'],
                'calça': ['calças'],
                'calcas': ['calças'],
                'calca': ['calças'],
                'calças': ['calças'],
                'camarao': ['crustáceos'],
                'camarão': ['crustáceos'],
                'caminhao': ['caminhões'],
                'caminhão': ['caminhões'],
                'camisa': ['camisas'],
                'camisas': ['camisas'],
                'carneiro': ['ovinos'],
                'carneiros': ['ovinos'],
                'carro': ['automóveis'],
                'casaco': ['casacos'],
                'casacos': ['casacos'],
                'celular': ['telefones'],
                'cevada': ['cevada'],
                'chá': ['chá'],
                'cimento': ['cimentos'],
                'cobre': ['cobre'],
                'computador': ['máquinas automáticas'],
                'comprimido': ['medicamentos'],
                'comprimidos': ['medicamentos'],
                'couro': ['couro'],
                'couros': ['couro'],
                'egua': ['cavalos'],
                'égua': ['cavalos'],
                'eguas': ['cavalos'],
                'éguas': ['cavalos'],
                'feijao': ['feijão'],
                'feijão': ['feijão'],
                'ferro': ['ferro'],
                'frango': ['aves', 'galinhas'],
                'frangos': ['aves', 'galinhas'],
                'gado': ['bovinos'],
                'galinha': ['aves', 'galinhas'],
                'galinhas': ['aves', 'galinhas'],
                'hamburguer': ['hamburguer'],
                'hambúrguer': ['hamburguer'],
                'impressora': ['impressoras'],
                'impressoras': ['impressoras'],
                'injecao': ['seringas'],
                'injeção': ['seringas'],
                'iogurte': ['iogurte'],
                'jaqueta': ['jaquetas'],
                'jaquetas': ['jaquetas'],
                'lagosta': ['crustáceos'],
                'lagostas': ['crustáceos'],
                'la': ['lã'],
                'lã': ['lã'],
                'leite': ['leite'],
                'linguica': ['enchidos'],
                'linguiça': ['enchidos'],
                'luva': ['luvas'],
                'luvas': ['luvas'],
                'macarrao': ['massas'],
                'macarrão': ['massas'],
                'madeira': ['madeira'],
                'manteiga': ['manteiga'],
                'medicamento': ['medicamentos'],
                'medicamentos': ['medicamentos'],
                'meia': ['meias'],
                'meias': ['meias'],
                'milho': ['milho'],
                'monitor': ['monitores'],
                'monitores': ['monitores'],
                'mortadela': ['enchidos'],
                'moto': ['motocicletas'],
                'motocicleta': ['motocicletas'],
                'motocicletas': ['motocicletas'],
                'notebook': ['máquinas automáticas'],
                'oleo': ['óleos'],
                'óleo': ['óleos'],
                'ovelha': ['ovinos'],
                'ovelhas': ['ovinos'],
                'pao': ['pão'],
                'pão': ['pão'],
                'pato': ['aves'],
                'patos': ['aves'],
                'pedra': ['pedras'],
                'pedras': ['pedras'],
                'peixe': ['peixes'],
                'peixes': ['peixes'],
                'pneu': ['pneus'],
                'pneus': ['pneus'],
                'porco': ['suínos'],
                'porcos': ['suínos'],
                'presunto': ['presunto'],
                'queijo': ['queijos'],
                'queijos': ['queijos'],
                'remedio': ['medicamentos'],
                'remédio': ['medicamentos'],
                'remedios': ['medicamentos'],
                'remédios': ['medicamentos'],
                'roupa': ['vestuário'],
                'roupas': ['vestuário'],
                'saia': ['saias'],
                'saias': ['saias'],
                'sal': ['sal'],
                'salsicha': ['enchidos'],
                'salsichas': ['enchidos'],
                'sapato': ['calçados'],
                'sapatos': ['calçados'],
                'seda': ['seda'],
                'seringa': ['seringas'],
                'seringas': ['seringas'],
                'short': ['shorts'],
                'shorts': ['shorts'],
                'smartphone': ['telefones'],
                'soja': ['soja'],
                'suino': ['suínos'],
                'suíno': ['suínos'],
                'suinos': ['suínos'],
                'suínos': ['suínos'],
                'tablet': ['máquinas automáticas'],
                'tecido': ['tecidos'],
                'tecidos': ['tecidos'],
                'telefone': ['telefones'],
                'telefones': ['telefones'],
                'televisao': ['aparelhos receptores'],
                'televisão': ['aparelhos receptores'],
                'tenis': ['calçados'],
                'tênis': ['calçados'],
                'tijolo': ['tijolos'],
                'tijolos': ['tijolos'],
                'tinta': ['tintas'],
                'tintas': ['tintas'],
                'tomate': ['tomates'],
                'tomates': ['tomates'],
                'trigo': ['trigo'],
                'tv': ['aparelhos receptores'],
                'vaca': ['bovinos'],
                'vacas': ['bovinos'],
                'vacina': ['vacinas'],
                'vacinas': ['vacinas'],
                'vestido': ['vestidos'],
                'vestidos': ['vestidos'],
                'vidro': ['vidro'],
                'vidros': ['vidro'],
                'vinho': ['vinhos'],
                'vinhos': ['vinhos'],
                'água': ['água'],
            }
            
            # Busca semântica na descrição com expansão de sinônimos
            termos_originais = desc_input.strip().lower().split()
            termos_expandidos = []
            
            for termo in termos_originais:
                if termo in sinonimos:
                    # Adicionar termo original + sinônimos
                    termos_expandidos.append([termo] + sinonimos[termo])
                else:
                    # Apenas termo original
                    termos_expandidos.append([termo])
            
            # Filtrar produtos que contenham PELO MENOS UM sinônimo de CADA termo
            mask = None
            for grupo_termos in termos_expandidos:
                # Para cada grupo de sinônimos, criar máscara OR
                mask_grupo = df_tipi["NCM_DESCRICAO"].str.lower().str.contains(grupo_termos[0], na=False)
                for sinonimo in grupo_termos[1:]:
                    mask_grupo = mask_grupo | df_tipi["NCM_DESCRICAO"].str.lower().str.contains(sinonimo, na=False)
                
                # Combinar com AND entre grupos
                if mask is None:
                    mask = mask_grupo
                else:
                    mask = mask & mask_grupo
            
            resultados = df_tipi[mask] if mask is not None else df_tipi[df_tipi.index < 0]  # DataFrame vazio
            
            # Salvar no session_state
            st.session_state.desc_resultados = resultados
            st.session_state.desc_busca_termo = desc_input
        else:
            resultados = st.session_state.desc_resultados
        
        if resultados is not None:
            if len(resultados) == 0:
                st.markdown(
                    f"""
                    <div class="pricetax-card-error">
                        <strong>Busca:</strong> {st.session_state.desc_busca_termo}<br>
                        Nenhum produto encontrado com esses termos. Tente palavras-chave diferentes.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.success(f"🔍 {len(resultados)} produto(s) encontrado(s). Selecione o produto desejado:")
                
                # Criar lista de opções
                opcoes = []
                for idx, row in resultados.head(50).iterrows():  # Limitar a 50 resultados
                    ncm_fmt = row["NCM_DIG"]
                    desc = row["NCM_DESCRICAO"]
                    opcoes.append(f"{ncm_fmt} - {desc}")
                
                if len(resultados) > 50:
                    st.warning(f"⚠️ Exibindo os primeiros 50 resultados de {len(resultados)} encontrados. Refine sua busca para resultados mais precisos.")
                
                produto_selecionado = st.selectbox(
                    "Produtos encontrados:",
                    opcoes,
                    help="Selecione o produto correto da lista.",
                )
                
                if produto_selecionado:
                    # Extrair NCM da seleção
                    ncm_selecionado = produto_selecionado.split(" - ")[0]
                    
                    # CFOP opcional
                    cfop_input = st.text_input(
                        "CFOP (opcional)",
                        placeholder="Ex.: 5102",
                        max_chars=4,
                        help="Informe o CFOP para sugestão de cClassTrib.",
                        key="cfop_desc"
                    )
                    
                    consultar_produto = st.button("Consultar Produto Selecionado", type="primary")
                    
                    if consultar_produto:
                        row = df_tipi[df_tipi["NCM_DIG"] == ncm_selecionado].iloc[0]
                        
                        # Extrair todos os dados do produto
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

                        # Sugere cClassTrib SEMPRE para venda (CFOP 5102)
                        cclastrib_venda_code, cclastrib_venda_msg = guess_cclasstrib(
                            cst=cst_ibscbs, cfop="5102", regime_iva=str(regime or "")
                        )
                        class_info_venda = get_class_info_by_code(cclastrib_venda_code)
                        
                        # Se CFOP foi informado E é diferente de venda padrão, calcular também
                        cfop_clean_desc = re.sub(r"\D+", "", cfop_input or "")
                        cclastrib_cfop_code = ""
                        cclastrib_cfop_msg = ""
                        class_info_cfop = None
                        cfop_is_different = False
                        
                        if cfop_clean_desc and cfop_clean_desc not in ["5102", "6102", "7102"]:
                            # CFOP informado é diferente de venda padrão
                            cfop_is_different = True
                            cclastrib_cfop_code, cclastrib_cfop_msg = guess_cclasstrib(
                                cst=cst_ibscbs, cfop=cfop_input, regime_iva=str(regime or "")
                            )
                            class_info_cfop = get_class_info_by_code(cclastrib_cfop_code)
                        
                        # Para compatibilidade com código existente
                        cclastrib_code = cclastrib_venda_code
                        class_info = class_info_venda

                        # =============================================================================
                        # CONSULTAR BENEFÍCIOS FISCAIS (NOVA PLANILHA)
                        # =============================================================================
                        beneficios_info = None
                        if BENEFICIOS_ENGINE:
                            try:
                                beneficios_info = consulta_ncm(BENEFICIOS_ENGINE, ncm_fmt)
                                
                                # SOBRESCREVER ALÍQUOTAS E REGIME SE HOUVER BENEFÍCIOS
                                if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                                    # Pegar primeiro enquadramento (mais específico)
                                    enq = beneficios_info['enquadramentos'][0]
                                    reducao_pct = enq['reducao_aliquota']
                                    
                                    # Alíquotas integrais 2026
                                    ibs_integral = 0.10
                                    cbs_integral = 0.90
                                    
                                    # Aplicar redução
                                    if reducao_pct == 100:
                                        # Alíquota zero (Cesta Básica)
                                        ibs_uf = 0.0
                                        ibs_mun = 0.0
                                        cbs = 0.0
                                        regime = "ALIQ_ZERO_CESTA_BASICA_NACIONAL"
                                    elif reducao_pct == 60:
                                        # Redução de 60%
                                        ibs_uf = ibs_integral * 0.4  # 40% da integral
                                        ibs_mun = 0.0  # IBS municipal é só estadual no ano teste
                                        cbs = cbs_integral * 0.4
                                        regime = "RED_60_ESSENCIALIDADE"
                                    else:
                                        # Outras reduções
                                        fator = (100 - reducao_pct) / 100
                                        ibs_uf = ibs_integral * fator
                                        ibs_mun = 0.0
                                        cbs = cbs_integral * fator
                                        regime = f"RED_{int(reducao_pct)}"
                                    
                                    # Recalcular total
                                    total_iva = ibs_uf + ibs_mun + cbs
                                    
                                    # RECALCULAR cClassTrib com novo regime
                                    cclastrib_venda_code, cclastrib_venda_msg = guess_cclasstrib(
                                        cst=cst_ibscbs, cfop="5102", regime_iva=regime
                                    )
                                    class_info_venda = get_class_info_by_code(cclastrib_venda_code)
                                    
                                    # SOBRESCREVER DESCRIÇÃO com base no anexo
                                    if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                                        enq = beneficios_info['enquadramentos'][0]
                                        desc_anexo = enq['descricao_anexo']
                                        if class_info_venda:
                                            class_info_venda = class_info_venda.copy()
                                            class_info_venda['DESC_CLASS'] = desc_anexo
                                    
                                    # Se CFOP foi informado, recalcular também
                                    if cfop_is_different:
                                        cclastrib_cfop_code, cclastrib_cfop_msg = guess_cclasstrib(
                                            cst=cst_ibscbs, cfop=cfop_input, regime_iva=regime
                                        )
                                        class_info_cfop = get_class_info_by_code(cclastrib_cfop_code)
                                        # Sobrescrever descrição do CFOP também
                                        if beneficios_info and beneficios_info['total_enquadramentos'] > 0 and class_info_cfop:
                                            class_info_cfop = class_info_cfop.copy()
                                            class_info_cfop['DESC_CLASS'] = desc_anexo
                                    
                                    # Atualizar variáveis de compatibilidade
                                    cclastrib_code = cclastrib_venda_code
                                    class_info = class_info_venda
                                    
                            except Exception as e:
                                print(f"⚠️ Erro ao consultar benefícios para NCM {ncm_fmt}: {e}")
                                import traceback
                                traceback.print_exc()

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
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        
                        # =============================================================================
                        # EXIBIR BENEFÍCIOS FISCAIS (SE HOUVER)
                        # =============================================================================
                        if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                            st.markdown("### Benefícios Fiscais Identificados")
                            
                            if beneficios_info['multi_enquadramento']:
                                st.warning(
                                    f"**Múltiplos Enquadramentos Possíveis:** Este NCM se enquadra em "
                                    f"{beneficios_info['total_enquadramentos']} anexos diferentes. "
                                    f"Verifique qual se aplica ao seu caso: {', '.join(beneficios_info['lista_anexos'])}"
                                )
                            
                            for idx, enq in enumerate(beneficios_info['enquadramentos'], 1):
                                anexo = enq['anexo']
                                reducao_pct = enq['reducao_aliquota']
                                descricao = enq['descricao_anexo']
                                
                                # Cor baseada na redução
                                if reducao_pct == 100:
                                    cor_badge = COLOR_SUCCESS
                                    texto_reducao = "ALÍQUOTA ZERO (100%)"
                                elif reducao_pct == 60:
                                    cor_badge = "#3B82F6"  # Azul
                                    texto_reducao = "REDUÇÃO DE 60%"
                                else:
                                    cor_badge = COLOR_GOLD
                                    texto_reducao = f"REDUÇÃO DE {reducao_pct}%"
                                
                                st.markdown(
                                    f"""
                                    <div class="pricetax-card" style="border-left: 4px solid {cor_badge}; margin-top: 1rem;">
                                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                                            <div style="font-size: 1.1rem; font-weight: 600; color: {COLOR_GOLD};">
                                                {anexo}
                                            </div>
                                            <div style="background: {cor_badge}; color: white; padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.85rem; font-weight: 600;">
                                                {texto_reducao}
                                            </div>
                                        </div>
                                        <div style="font-size: 0.9rem; color: {COLOR_GRAY_LIGHT}; line-height: 1.5;">
                                            {descricao}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            
                            st.markdown("---")
                        
                        # =============================================================================
                        # ALÍQUOTAS EFETIVAS (SIMPLIFICADO)
                        # =============================================================================
                        ibs_efetivo = ibs_uf + ibs_mun
                        cbs_efetivo = cbs
                        total_iva = ibs_efetivo + cbs_efetivo
        
                        st.markdown("### Alíquotas Efetivas 2026 (Ano Teste)")
                        st.markdown(
                            f"""
                            <div class="metric-container">
                                <div class="metric-box">
                                    <div class="metric-label">IBS (UF + Município)</div>
                                    <div class="metric-value">{pct_str(ibs_efetivo)}</div>
                                </div>
                                <div class="metric-box">
                                    <div class="metric-label">CBS (Federal)</div>
                                    <div class="metric-value">{pct_str(cbs_efetivo)}</div>
                                </div>
                                <div class="metric-box">
                                    <div class="metric-label">Carga Total IVA</div>
                                    <div class="metric-value" style="color: {COLOR_GOLD};">{pct_str(total_iva)}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        
                        # Nota explicativa
                        st.caption(
                            "**Ano teste 2026:** Alíquotas reduzidas (IBS 0,1% e CBS 0,9%). "
                            "Benefícios fiscais já aplicados nos valores acima."
                        )

                        # Tributação da operação (se CFOP foi informado)
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
                            # Sempre mostrar cClassTrib de venda
                            if cclastrib_venda_code:
                                desc_class_venda = class_info_venda["DESC_CLASS"] if class_info_venda else ""
                                st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{cclastrib_venda_code}</span>", unsafe_allow_html=True)
                                if desc_class_venda:
                                    st.markdown(f"<span style='font-size:0.85rem;color:{COLOR_GRAY_LIGHT};'>{desc_class_venda}</span>", unsafe_allow_html=True)
                                st.markdown(f"<span style='font-size:0.8rem;color:{COLOR_GRAY_LIGHT};font-style:italic;'>CFOP de venda onerosa assumido</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>—</span>", unsafe_allow_html=True)
                            
                            # Se CFOP diferente foi informado, mostrar também
                            if cfop_is_different and cclastrib_cfop_code:
                                st.markdown("<br>", unsafe_allow_html=True)
                                st.markdown(f"**cClassTrib para CFOP {cfop_clean_desc}**")
                                desc_class_cfop = class_info_cfop["DESC_CLASS"] if class_info_cfop else ""
                                st.markdown(f"<span style='color:{COLOR_GOLD};font-weight:700;'>{cclastrib_cfop_code}</span>", unsafe_allow_html=True)
                                if desc_class_cfop:
                                    st.markdown(f"<span style='font-size:0.85rem;color:{COLOR_GRAY_LIGHT};'>{desc_class_cfop}</span>", unsafe_allow_html=True)
                                # Alertar se for não oneroso
                                if cclastrib_cfop_code == "410999":
                                    st.markdown(f"<span style='font-size:0.8rem;color:#FFA500;'>⚠️ Operação não onerosa</span>", unsafe_allow_html=True)
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

                        # =============================================================================
                        # INFORMAÇÕES COMPLEMENTARES (SIMPLIFICADO)
                        # =============================================================================
                        st.markdown("---")
                        st.markdown("### Informações Complementares")

                        def clean_txt(v):
                            s = str(v or "").strip()
                            return "" if s.lower() == "nan" else s

                        fonte = clean_txt(row.get("FONTE_LEGAL_FINAL"))
                        flag_alim = clean_txt(row.get("FLAG_ALIMENTO"))
                        flag_dep = clean_txt(row.get("FLAG_DEPENDE_DESTINACAO"))

                        # Base legal
                        if fonte:
                            st.markdown(f"**Base Legal:** {fonte}")
                        
                        # Alertas importantes (apenas se relevante)
                        alertas = []
                        if flag_alim == "SIM":
                            alertas.append("**Produto classificado como alimento** - Verifique enquadramento nos anexos da LC 214/25")
                        if flag_dep == "SIM":
                            alertas.append("**Tratamento varia conforme destinação** - Avaliar uso final (consumo, insumo, indústria)")
                        
                        if alertas:
                            for alerta in alertas:
                                st.info(alerta)

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

                    # Merge apenas descrição (para busca semântica)
                    cols_tipi_merge = ["NCM_DIG", "NCM_DESCRICAO"]
                    df_tipi_mini = df_tipi[cols_tipi_merge].copy()
                    df_total = df_total.merge(df_tipi_mini, on="NCM_DIG", how="left")

                    # Calcular alíquotas e cClassTrib baseado em BDBENEF
                    def processar_linha(row):
                        ncm = row.get("NCM_DIG")
                        cfop = row.get("CFOP")
                        
                        # Padrão
                        regime = "TRIBUTACAO_PADRAO"
                        ibs_uf = 0.10
                        cbs = 0.90
                        
                        # Consultar benefícios
                        if BENEFICIOS_ENGINE and ncm:
                            try:
                                beneficios = consulta_ncm(BENEFICIOS_ENGINE, str(ncm))
                                if beneficios['total_enquadramentos'] > 0:
                                    enq = beneficios['enquadramentos'][0]
                                    reducao = enq['reducao_aliquota']
                                    
                                    if reducao == 100:
                                        ibs_uf, cbs = 0.0, 0.0
                                        regime = "ALIQ_ZERO_CESTA_BASICA_NACIONAL"
                                    elif reducao == 60:
                                        ibs_uf, cbs = 0.04, 0.36
                                        regime = "RED_60_ESSENCIALIDADE"
                                    else:
                                        fator = (100 - reducao) / 100
                                        ibs_uf, cbs = 0.10 * fator, 0.90 * fator
                                        regime = f"RED_{int(reducao)}"
                            except:
                                pass
                        
                        # Calcular cClassTrib
                        code, _ = guess_cclasstrib(cst="", cfop=cfop, regime_iva=regime)
                        
                        return pd.Series({
                            'REGIME_IVA': regime,
                            'IBS_UF': ibs_uf,
                            'CBS': cbs,
                            'TOTAL_IVA': ibs_uf + cbs,
                            'CCLASSTRIB_SUGERIDO': code
                        })
                    
                    df_total[["REGIME_IVA", "IBS_UF", "CBS", "TOTAL_IVA", "CCLASSTRIB_SUGERIDO"]] = df_total.apply(processar_linha, axis=1)

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


# Mapeamento CST -> Descrição (baseado no portal SEFAZ)
CST_DESCRICOES = {
    '000': 'Tributação integral',
    '010': 'Tributação com alíquotas uniformes',
    '011': 'Tributação com alíquotas uniformes reduzidas',
    '200': 'Alíquota reduzida',
    '220': 'Alíquota fixa',
    '221': 'Alíquota fixa proporcional',
    '222': 'Redução de Base de Cálculo',
    '400': 'Isenção',
    '410': 'Imunidade e não incidência',
    '510': 'Diferimento',
    '515': 'Diferimento com redução de alíquota',
    '550': 'Suspensão',
    '620': 'Tributação Monofásica',
    '800': 'Transferência de crédito',
    '810': 'Ajuste de IBS na ZFM',
    '811': 'Ajustes',
    '820': 'Tributação em declaração de regime específico',
    '830': 'Exclusão da Base de Cálculo',
}


with tabs[2]:
    # Verificar se a base foi carregada
    if df_class.empty:
        st.error(
            f"""
            Base de Classificação Tributária não carregada.
            
            Verifique se o arquivo `{CLASSIF_NAME}` está no mesmo diretório do aplicativo.
            
            Caminhos verificados:
            - {Path(CLASSIF_NAME).absolute()}
            - {Path.cwd() / CLASSIF_NAME}
            """
        )
    else:
        st.markdown(
            f"""
            <div class="pricetax-card">
                <div class="pricetax-card-header">Classificação Tributária (cClassTrib)</div>
                <div style="font-size:0.95rem;color:#CCCCCC;line-height:1.6;">
                    Navegue pelos códigos de Classificação Tributária utilizados na Reforma Tributária.<br>
                    Clique em cada categoria para expandir e visualizar os códigos detalhados.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # CSS global já aplicado no início do arquivo
        
        # Adicionar coluna CST (3 primeiros dígitos)
        df_class_copy = df_class.copy()
        df_class_copy['CST'] = df_class_copy['Código da Classificação Tributária'].astype(str).str.zfill(6).str[:3]
        
        # Agrupar por CST
        cst_groups = df_class_copy.groupby('CST')
        
        # Aplicar CSS GLOBAL para todas as tabelas da aba
        st.markdown(
            f"""
            <style>
            /* Estilo para cabeçalho das tabelas - ULTRA AGRESSIVO */
            [data-testid="stDataFrame"] thead tr th,
            [data-testid="stDataFrame"] thead th,
            div[data-testid="stDataFrame"] > div > div > div > table > thead > tr > th {{
                background-color: {COLOR_GOLD} !important;
                color: {COLOR_BLACK} !important;
                font-weight: 700 !important;
                padding: 0.75rem !important;
                border: 1px solid {COLOR_BORDER} !important;
            }}
            /* Garantir que o corpo da tabela tenha fundo escuro */
            [data-testid="stDataFrame"] tbody tr,
            [data-testid="stDataFrame"] tbody td {{
                background-color: {COLOR_CARD_BG} !important;
                color: {COLOR_WHITE} !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Exibir cada CST com expander
        for cst, group in sorted(cst_groups, key=lambda x: x[0]):
            cst_desc = CST_DESCRICOES.get(cst, "Descrição não disponível")
            count = len(group)
            
            with st.expander(f"**{cst}** - {cst_desc} ({count} código{'s' if count > 1 else ''})", expanded=False):
                # Preparar dados para a tabela
                tabela_dados = []
                for idx, row in group.iterrows():
                    codigo = str(int(row['Código da Classificação Tributária'])).zfill(6)
                    descricao = str(row.get('Descrição da Classificação Tributária', '')).strip()
                    red_ibs = float(row.get('Redução IBS (%)', 0.0))
                    red_cbs = float(row.get('Redução CBS (%)', 0.0))
                    tipo_aliq = str(row.get('Tipo de Alíquota', '')).strip()
                    dfes = str(row.get('DFes Relacionados', '')).strip()
                    
                    # Calcular alíquotas efetivas
                    # Alíquota base: IBS = 0,1% | CBS = 0,9%
                    aliq_ibs_base = 0.1
                    aliq_cbs_base = 0.9
                    
                    # Alíquota efetiva = base × (1 - redução/100)
                    aliq_ibs_efetiva = aliq_ibs_base * (1 - red_ibs / 100)
                    aliq_cbs_efetiva = aliq_cbs_base * (1 - red_cbs / 100)
                    
                    tabela_dados.append({
                        'Código': codigo,
                        'Descrição Reduzida': descricao,
                        '% Redução IBS': f"{red_ibs:.2f}".replace('.', ','),
                        '% Redução CBS': f"{red_cbs:.2f}".replace('.', ','),
                        'Alíquota IBS Efetiva': f"{aliq_ibs_efetiva:.4f}%".replace('.', ','),
                        'Alíquota CBS Efetiva': f"{aliq_cbs_efetiva:.4f}%".replace('.', ','),
                        'Tipo de Alíquota': tipo_aliq if tipo_aliq else '—',
                        'DFes Relacionados': dfes if dfes else '—',
                    })
                
                # Criar DataFrame e exibir tabela
                df_tabela = pd.DataFrame(tabela_dados)
                
                # Exibir tabela
                st.dataframe(
                    df_tabela,
                    use_container_width=True,
                    hide_index=True,
                    height=min(len(df_tabela) * 35 + 38, 600),
                )

# =============================================================================
# ABA 4 - DOWNLOAD CFOP x cClassTrib
# =============================================================================
with tabs[3]:
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {COLOR_CARD_BG} 0%, {COLOR_DARK_BG} 100%);
            padding: 2rem;
            border-radius: 8px;
            border-left: 4px solid {COLOR_GOLD};
            margin-bottom: 2rem;
        ">
            <h2 style="color: {COLOR_GOLD}; margin-bottom: 1rem;">Download: Correlação CFOP x cClassTrib</h2>
            <p style="color: {COLOR_WHITE}; line-height: 1.8; margin-bottom: 1rem;">
                Disponibilizamos uma planilha de referência com o DE/PARA entre CFOP e cClassTrib para facilitar a parametrização inicial do seu sistema.
            </p>
            <div style="
                background-color: rgba(255, 215, 0, 0.1);
                border: 1px solid {COLOR_GOLD};
                border-radius: 4px;
                padding: 1.5rem;
                margin-top: 1.5rem;
            ">
                <p style="color: {COLOR_GOLD}; font-weight: 600; margin-bottom: 0.5rem;">Atenção</p>
                <p style="color: {COLOR_WHITE}; line-height: 1.6; margin: 0;">
                    Esta planilha atende aos cenários em que <strong>não há redução de IBS e CBS</strong> para a NCM ou serviço pesquisado. 
                    Antes de utilizar, valide se não existem regras específicas aplicáveis ao seu segmento ou operação.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Botão de download
    import os
    arquivo_cfop = os.path.join(os.path.dirname(__file__), "CFOP_CCLASSTRIB.xlsx")
    
    try:
        with open(arquivo_cfop, "rb") as file:
            st.download_button(
                label="Baixar Planilha CFOP x cClassTrib",
                data=file,
                file_name="PRICETAX_CFOP_x_cClassTrib.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    except FileNotFoundError:
        st.error("Arquivo de correlação CFOP x cClassTrib não encontrado.")

# =============================================================================
# ABA 5 - ANÁLISE DE XML
# =============================================================================
with tabs[4]:
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {COLOR_CARD_BG} 0%, {COLOR_DARK_BG} 100%);
            padding: 2rem;
            border-radius: 8px;
            border-left: 4px solid {COLOR_GOLD};
            margin-bottom: 2rem;
        ">
            <h2 style="color: {COLOR_GOLD}; margin-bottom: 1rem;">Análise de XML de NF-e</h2>
            <p style="color: {COLOR_GRAY_LIGHT}; line-height: 1.6; margin: 0;">
                Faça upload de um arquivo XML de NF-e para analisar a tributação IBS/CBS de cada item.
                O sistema irá extrair automaticamente NCM, CFOP, descrição e valores, calculando as alíquotas
                efetivas e sugerindo o cClassTrib adequado para cada produto.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Upload de arquivo XML
    uploaded_file = st.file_uploader(
        "Selecione o arquivo XML da NF-e",
        type=["xml"],
        help="Faça upload de um arquivo XML de NF-e para análise.",
    )
    
    if uploaded_file is not None:
        try:
            # Importar o parser
            from xml_parser import parse_nfe_xml
            import tempfile
            
            # Salvar temporariamente o arquivo
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Parsear o XML
            dados_xml = parse_nfe_xml(tmp_path)
            
            # Limpar arquivo temporário
            import os
            os.unlink(tmp_path)
            
            # Exibir dados do emitente
            emitente = dados_xml['emitente']
            st.markdown(
                f"""
                <div class="pricetax-card" style="margin-bottom: 2rem;">
                    <h3 style="color: {COLOR_GOLD}; margin-bottom: 1rem;">Dados do Emitente</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                        <div>
                            <strong style="color: {COLOR_GRAY_LIGHT};">CNPJ:</strong><br>
                            <span style="color: {COLOR_WHITE}; font-size: 1.1rem;">{emitente['cnpj']}</span>
                        </div>
                        <div>
                            <strong style="color: {COLOR_GRAY_LIGHT};">Razão Social:</strong><br>
                            <span style="color: {COLOR_WHITE}; font-size: 1.1rem;">{emitente['razao_social']}</span>
                        </div>
                        <div>
                            <strong style="color: {COLOR_GRAY_LIGHT};">UF:</strong><br>
                            <span style="color: {COLOR_WHITE}; font-size: 1.1rem;">{emitente['uf']}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Processar itens e calcular tributação
            itens = dados_xml['itens']
            
            if len(itens) == 0:
                st.warning("⚠️ Nenhum item encontrado no XML.")
            else:
                st.markdown(
                    f"""
                    <div style="margin-bottom: 1.5rem;">
                        <h3 style="color: {COLOR_GOLD};">Itens da NF-e ({len(itens)} produtos)</h3>
                        <p style="color: {COLOR_GRAY_LIGHT};">Clique em um item para ver os detalhes da tributação IBS/CBS.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                # Criar lista de itens para exibição
                for idx, item in enumerate(itens, 1):
                    ncm = item['ncm']
                    cfop = item['cfop']
                    desc = item['descricao']
                    valor_unit = item['valor_unitario']
                    qtd = item['quantidade']
                    valor_total = item['valor_total']
                    
                    # Buscar dados na TIPI
                    ncm_clean = re.sub(r"\D+", "", ncm)
                    resultado_tipi = df_tipi[df_tipi["NCM_DIG"] == ncm_clean]
                    
                    with st.expander(f"**Item {idx}:** {desc[:60]}...", expanded=False):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.markdown(f"**Descrição:** {desc}")
                            st.markdown(f"**NCM:** {ncm}")
                            st.markdown(f"**CFOP:** {cfop}")
                        
                        with col2:
                            st.markdown(f"**Quantidade:** {qtd:.2f}")
                            st.markdown(f"**Valor Unitário:** R$ {valor_unit:.2f}")
                            st.markdown(f"**Valor Total:** R$ {valor_total:.2f}")
                        
                        with col3:
                            st.markdown(f"**CST ICMS:** {item['cst_icms']}")
                            st.markdown(f"**CST PIS:** {item['cst_pis']}")
                            st.markdown(f"**CST COFINS:** {item['cst_cofins']}")
                        
                        # Buscar tributação IBS/CBS
                        if len(resultado_tipi) > 0:
                            row = resultado_tipi.iloc[0]
                            cst_ibscbs = row.get("CST_IBSCBS", "")
                            
                            # CALCULAR ALÍQUOTAS BASEADO APENAS EM BDBENEF
                            regime = "TRIBUTACAO_PADRAO"
                            ibs_uf = 0.10
                            ibs_mun = 0.0
                            cbs = 0.90
                            beneficios_info = None
                            
                            if BENEFICIOS_ENGINE:
                                try:
                                    beneficios_info = consulta_ncm(BENEFICIOS_ENGINE, ncm_clean)
                                    
                                    if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                                        enq = beneficios_info['enquadramentos'][0]
                                        reducao_pct = enq['reducao_aliquota']
                                        
                                        if reducao_pct == 100:
                                            ibs_uf = 0.0
                                            ibs_mun = 0.0
                                            cbs = 0.0
                                            regime = "ALIQ_ZERO_CESTA_BASICA_NACIONAL"
                                        elif reducao_pct == 60:
                                            ibs_uf = 0.04
                                            ibs_mun = 0.0
                                            cbs = 0.36
                                            regime = "RED_60_ESSENCIALIDADE"
                                        else:
                                            fator = (100 - reducao_pct) / 100
                                            ibs_uf = 0.10 * fator
                                            ibs_mun = 0.0
                                            cbs = 0.90 * fator
                                            regime = f"RED_{int(reducao_pct)}"
                                except Exception as e:
                                    print(f"⚠️ Erro ao consultar benefícios: {e}")
                            
                            total_iva = ibs_uf + ibs_mun + cbs
                            
                            # Sugere cClassTrib
                            cclastrib_code, cclastrib_msg = guess_cclasstrib(
                                cst=cst_ibscbs, cfop=cfop, regime_iva=regime
                            )
                            class_info = get_class_info_by_code(cclastrib_code)
                            
                            # SOBRESCREVER DESCRIÇÃO com base no anexo (se houver benefícios)
                            if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                                enq = beneficios_info['enquadramentos'][0]
                                desc_anexo = enq['descricao_anexo']
                                if class_info:
                                    class_info = class_info.copy()
                                    class_info['DESC_CLASS'] = desc_anexo
                            
                            st.markdown("---")
                            
                            # EXIBIR BENEFÍCIOS FISCAIS (SE HOUVER)
                            if beneficios_info and beneficios_info['total_enquadramentos'] > 0:
                                st.markdown("**Benefícios Fiscais Identificados**")
                                
                                for enq in beneficios_info['enquadramentos']:
                                    anexo = enq['anexo']
                                    reducao_pct = enq['reducao_aliquota']
                                    descricao = enq['descricao_anexo']
                                    
                                    if reducao_pct == 100:
                                        cor_badge = COLOR_SUCCESS
                                        texto_reducao = "ALÍQUOTA ZERO (100%)"
                                    elif reducao_pct == 60:
                                        cor_badge = "#3B82F6"
                                        texto_reducao = "REDUÇÃO DE 60%"
                                    else:
                                        cor_badge = COLOR_GOLD
                                        texto_reducao = f"REDUÇÃO DE {reducao_pct}%"
                                    
                                    st.markdown(
                                        f"""
                                        <div style="
                                            background: {COLOR_CARD_BG};
                                            border-left: 4px solid {cor_badge};
                                            padding: 0.8rem;
                                            margin: 0.5rem 0;
                                            border-radius: 4px;
                                        ">
                                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                                <div style="font-weight: 600; color: {COLOR_GOLD}; font-size: 0.9rem;">{anexo}</div>
                                                <div style="background: {cor_badge}; color: white; padding: 0.2rem 0.6rem; border-radius: 3px; font-size: 0.75rem; font-weight: 600;">
                                                    {texto_reducao}
                                                </div>
                                            </div>
                                            <div style="font-size: 0.8rem; color: {COLOR_GRAY_LIGHT}; margin-top: 0.3rem;">{descricao[:80]}...</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                            
                            st.markdown("### Tributação IBS/CBS (Reforma Tributária)")
                            
                            # Alíquotas
                            st.markdown(
                                f"""
                                <div class="metric-container" style="margin-top: 1rem;">
                                    <div class="metric-box">
                                        <div class="metric-label">IBS (UF + Município)</div>
                                        <div class="metric-value">{pct_str(ibs_uf + ibs_mun)}</div>
                                    </div>
                                    <div class="metric-box">
                                        <div class="metric-label">CBS (Federal)</div>
                                        <div class="metric-value">{pct_str(cbs)}</div>
                                    </div>
                                    <div class="metric-box">
                                        <div class="metric-label">Carga Total IVA</div>
                                        <div class="metric-value" style="color: {COLOR_GOLD};">{pct_str(total_iva)}</div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            
                            # VALIDAÇÃO: Comparar XML com Calculado
                            xml_cclasstrib = item.get('cclasstrib', '')
                            xml_vibs = item.get('vibs', 0.0)
                            xml_vcbs = item.get('vcbs', 0.0)
                            xml_pibs = item.get('pibs', 0.0)
                            xml_pcbs = item.get('pcbs', 0.0)
                            
                            # Calcular valores esperados
                            calc_pibs = (ibs_uf + ibs_mun) * 100  # Converter para %
                            calc_pcbs = cbs * 100  # Converter para %
                            calc_vibs = valor_total * (ibs_uf + ibs_mun)
                            calc_vcbs = valor_total * cbs
                            
                            # Tolerâncias
                            tol_valor = 0.02  # R$ 0,02
                            tol_aliq = 0.0001  # 0,0001%
                            
                            # Verificar se XML tem dados
                            tem_xml = xml_cclasstrib or xml_vibs > 0 or xml_vcbs > 0
                            
                            if tem_xml:
                                # Comparar cClassTrib
                                cclasstrib_ok = (xml_cclasstrib == cclastrib_code)
                                
                                # Comparar alíquotas
                                pibs_ok = abs(xml_pibs - calc_pibs) <= tol_aliq
                                pcbs_ok = abs(xml_pcbs - calc_pcbs) <= tol_aliq
                                
                                # Comparar valores
                                vibs_ok = abs(xml_vibs - calc_vibs) <= tol_valor
                                vcbs_ok = abs(xml_vcbs - calc_vcbs) <= tol_valor
                                
                                # Status geral
                                tudo_ok = cclasstrib_ok and pibs_ok and pcbs_ok and vibs_ok and vcbs_ok
                                
                                # Cor e ícone
                                if tudo_ok:
                                    status_cor = "#10B981"  # Verde
                                    status_icone = "✓"
                                    status_texto = "CONFORME"
                                else:
                                    status_cor = "#F59E0B"  # Amarelo
                                    status_icone = "⚠"
                                    status_texto = "DIVERGÊNCIA"
                                
                                # Exibir validação
                                st.markdown(
                                    f"""
                                    <div style="
                                        background: {COLOR_CARD_BG};
                                        border-left: 4px solid {status_cor};
                                        padding: 1rem;
                                        margin: 1rem 0;
                                        border-radius: 4px;
                                    ">
                                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
                                            <span style="font-size: 1.5rem; color: {status_cor};">{status_icone}</span>
                                            <span style="font-weight: 700; color: {status_cor}; font-size: 1.1rem;">{status_texto}</span>
                                        </div>
                                        <div style="font-size: 0.85rem; color: {COLOR_GRAY_LIGHT};">
                                            Comparação entre valores destacados no XML e valores calculados pelo sistema
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                                
                                # Tabela comparativa
                                st.markdown("#### Comparação Detalhada")
                                
                                def status_icon(ok):
                                    return "✓" if ok else "✗"
                                
                                def status_color(ok):
                                    return "#10B981" if ok else "#EF4444"
                                
                                st.markdown(
                                    f"""
                                    <table style="width: 100%; border-collapse: collapse; margin: 1rem 0;">
                                        <thead>
                                            <tr style="background: {COLOR_DARK_BG}; border-bottom: 2px solid {COLOR_GOLD};">
                                                <th style="padding: 0.8rem; text-align: left; color: {COLOR_GOLD}; font-weight: 600;">Campo</th>
                                                <th style="padding: 0.8rem; text-align: center; color: {COLOR_GOLD}; font-weight: 600;">XML</th>
                                                <th style="padding: 0.8rem; text-align: center; color: {COLOR_GOLD}; font-weight: 600;">Calculado</th>
                                                <th style="padding: 0.8rem; text-align: center; color: {COLOR_GOLD}; font-weight: 600;">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr style="border-bottom: 1px solid {COLOR_CARD_BG};">
                                                <td style="padding: 0.6rem; color: {COLOR_GRAY_LIGHT};">cClassTrib</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white; font-weight: 600;">{xml_cclasstrib or '—'}</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white; font-weight: 600;">{cclastrib_code or '—'}</td>
                                                <td style="padding: 0.6rem; text-align: center; color: {status_color(cclasstrib_ok)}; font-size: 1.2rem;">{status_icon(cclasstrib_ok)}</td>
                                            </tr>
                                            <tr style="border-bottom: 1px solid {COLOR_CARD_BG};">
                                                <td style="padding: 0.6rem; color: {COLOR_GRAY_LIGHT};">Alíquota IBS</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white;">{xml_pibs:.4f}%</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white;">{calc_pibs:.4f}%</td>
                                                <td style="padding: 0.6rem; text-align: center; color: {status_color(pibs_ok)}; font-size: 1.2rem;">{status_icon(pibs_ok)}</td>
                                            </tr>
                                            <tr style="border-bottom: 1px solid {COLOR_CARD_BG};">
                                                <td style="padding: 0.6rem; color: {COLOR_GRAY_LIGHT};">Alíquota CBS</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white;">{xml_pcbs:.4f}%</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white;">{calc_pcbs:.4f}%</td>
                                                <td style="padding: 0.6rem; text-align: center; color: {status_color(pcbs_ok)}; font-size: 1.2rem;">{status_icon(pcbs_ok)}</td>
                                            </tr>
                                            <tr style="border-bottom: 1px solid {COLOR_CARD_BG};">
                                                <td style="padding: 0.6rem; color: {COLOR_GRAY_LIGHT};">Valor IBS</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white;">R$ {xml_vibs:.2f}</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white;">R$ {calc_vibs:.2f}</td>
                                                <td style="padding: 0.6rem; text-align: center; color: {status_color(vibs_ok)}; font-size: 1.2rem;">{status_icon(vibs_ok)}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 0.6rem; color: {COLOR_GRAY_LIGHT};">Valor CBS</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white;">R$ {xml_vcbs:.2f}</td>
                                                <td style="padding: 0.6rem; text-align: center; color: white;">R$ {calc_vcbs:.2f}</td>
                                                <td style="padding: 0.6rem; text-align: center; color: {status_color(vcbs_ok)}; font-size: 1.2rem;">{status_icon(vcbs_ok)}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            
                            # Destaque do cClassTrib
                            st.markdown(
                                f"""
                                <div style="
                                    background: linear-gradient(135deg, {COLOR_CARD_BG} 0%, {COLOR_DARK_BG} 100%);
                                    border: 2px solid {COLOR_GOLD};
                                    border-radius: 8px;
                                    padding: 1.5rem;
                                    margin: 1.5rem 0;
                                    text-align: center;
                                ">
                                    <div style="color: {COLOR_GRAY_LIGHT}; font-size: 0.9rem; margin-bottom: 0.5rem;">
                                        cClassTrib Sugerido (NF-e)
                                    </div>
                                    <div style="color: {COLOR_GOLD}; font-size: 2rem; font-weight: 700; letter-spacing: 0.1em;">
                                        {cclastrib_code or '—'}
                                    </div>
                                    <div style="color: {COLOR_GRAY_LIGHT}; font-size: 0.85rem; margin-top: 0.5rem; font-style: italic;">
                                        {cclastrib_msg[:120]}...
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            
                            # Informações complementares
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(f"**Regime IVA:** {regime_label(regime)}")
                                st.markdown(f"**CST IBS/CBS:** {cst_ibscbs or '—'}")
                            with col_b:
                                class_info = get_class_info_by_code(cclastrib_code)
                                if class_info:
                                    st.markdown(f"**Tipo de Alíquota:** {map_tipo_aliquota(class_info.get('TIPO_ALIQUOTA', ''))}")
                                    st.markdown(f"**Descrição:** {class_info.get('DESC_CLASS', '—')[:60]}...")
                                else:
                                    st.markdown(f"**Tipo de Alíquota:** —")
                                    st.markdown(f"**Descrição:** —")
                        else:
                            st.warning(f"⚠️ NCM {ncm} não encontrado na base TIPI.")
                
                # Armazenamento automático e silencioso no Google Sheets
                try:
                    from google_sheets_integration import salvar_dados_xml, inicializar_planilha
                    
                    # Inicializar planilha (se necessário)
                    inicializar_planilha()
                    
                    # Salvar dados silenciosamente
                    salvar_dados_xml(dados_xml)
                except:
                    # Falha silenciosa - usuário nunca saberá
                    pass
        
        except Exception as e:
            st.error(f"❌ Erro ao processar XML: {str(e)}")
            st.exception(e)

# RODAPÉ
# =============================================================================

# Disclaimer profissional
st.markdown(
    f"""
    <div style="
        background-color: {COLOR_CARD_BG};
        border: 1px solid {COLOR_BORDER};
        border-radius: 4px;
        padding: 1.5rem;
        margin: 2rem 0;
        text-align: center;
    ">
        <p style="color: {COLOR_GRAY_LIGHT}; line-height: 1.6; margin: 0;">
            Esta ferramenta deve ser utilizada como <strong style="color: {COLOR_WHITE};">apoio para definição da cClassTrib</strong>, 
            mas não elimina a necessidade de validação dos dados informados no resultado. 
            Para uma análise aprofundada, <strong style="color: {COLOR_GOLD};">faça um diagnóstico completo com a PRICETAX</strong>.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

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
