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
    page_title="PRICETAX • IBS/CBS & SPED PIS/COFINS",
    page_icon="💡",
    layout="wide",
)

# Cores ajustadas para a identidade visual PriceTax (Fundo Escuro, Destaque Amarelo/Dourado)
PRIMARY_GOLD = "#FFC300"  # Amarelo/Dourado principal
PRIMARY_DARK = "#000000"  # Fundo preto/muito escuro
SECONDARY_ACCENT = "#FFFFFF" # Branco para texto e elementos secundários
CARD_BG = "#101015" # Fundo dos cards

st.markdown(
    f"""
    <style>
    /* Configuração geral do Streamlit */
    .stApp {{
        background-color: {PRIMARY_DARK};
        color: {SECONDARY_ACCENT};
        font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Título principal */
    .pricetax-title {{
        font-size: 2.2rem;
        font-weight: 700;
        color: {PRIMARY_GOLD};
    }}
    .pricetax-subtitle {{
        font-size: 0.98rem;
        color: #E0E0E0;
    }}

    /* Cards gerais */
    .pricetax-card {{
        border-radius: 0.9rem;
        padding: 1.1rem 1.3rem;
        /* Gradiente mais sutil e escuro */
        background: linear-gradient(135deg, #101010 0%, #050505 100%);
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
        background: {PRIMARY_GOLD};
        color: {PRIMARY_DARK};
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
    /* Ajuste do pill-regime para usar o amarelo/dourado */
    .pill-regime {{
        border-color: {PRIMARY_GOLD};
        background: rgba(255, 195, 0, 0.1); /* Fundo sutilmente dourado */
        color: {PRIMARY_GOLD};
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
    .pricetax-metric-value {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {PRIMARY_GOLD};
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        border-bottom: 1px solid #333333;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: #EEEEEE;
    }}
    .stTabs [aria-selected="true"] p {{
        color: {PRIMARY_GOLD} !important;
        font-weight: 600;
    }}

    /* Inputs */
    .stTextInput > div > div > input {{
        background-color: #111318;
        color: {SECONDARY_ACCENT};
        border-radius: 0.6rem;
        border: 1px solid #333333;
    }}
    .stFileUploader > label div {{
        color: #DDDDDD;
    }}

    /* Botão primário: Alterado de vermelho para um estilo mais neutro/dourado */
    .stButton>button[kind="primary"] {{
        background-color: #111318; /* Fundo escuro */
        color: {PRIMARY_GOLD}; /* Texto dourado */
        border-radius: 0.6rem;
        border: 1px solid {PRIMARY_GOLD}; /* Borda dourada */
        font-weight: 600;
    }}
    .stButton>button[kind="primary"]:hover {{
        background-color: {PRIMARY_GOLD}; /* Fundo dourado no hover */
        color: {PRIMARY_DARK}; /* Texto escuro no hover */
        border-color: {PRIMARY_GOLD};
    }}
    
    /* Subheader: Ajustado para usar a cor branca/secundária para um contraste mais limpo */
    h2 {{
        color: {SECONDARY_ACCENT};
    }}
    
    /* Ajuste para o título do PIS/COFINS no display_sped_result */
    .pis-cofins-title {{
        font-size: 1.1rem; 
        font-weight: 600; 
        color: {PRIMARY_GOLD}; /* Usando o dourado para destaque */
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
    """Formata 0.1 -> '0,10%'."""
    return f"{v:.2f}".replace(".", ",") + "%"


# --------------------------------------------------
# BASE TIPI → IBS/CBS (2026) – PLANILHA REFINADA PRICETAX
# --------------------------------------------------
TIPI_DEFAULT_NAME = "PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx"


@st.cache_data(show_spinner=False)
def load_tipi_base() -> pd.DataFrame:
    """
    Carrega a base PRICETAX refinada de classificação IBS/CBS por NCM,
    com aplicação das regras da EC 132/2023 e LC 214/2025.
    """
    try:
        candidatos = [
            Path(TIPI_DEFAULT_NAME),
            Path.cwd() / TIPI_DEFAULT_NAME,
        ]
        try:
            candidatos.append(Path(__file__).parent / TIPI_DEFAULT_NAME)
        except NameError:
            pass

        base_path = None
        for c in candidatos:
            if c.exists():
                base_path = c
                break

        if base_path is None:
            return pd.DataFrame()

        df = pd.read_excel(base_path)
    except Exception:
        return pd.DataFrame()

    df = normalize_cols_upper(df)

    required_cols = [
        "NCM",
        "NCM_DESCRICAO",
        "CAPITULO_TIPI",
        "TIPO_ITEM",
        "SEGMENTO_PRICETAX",
        "SUBSEGMENTO",
        "CEST",
        "CST_IBSCBS",
        "CLASSTRIB_IBS_CBS",
        "DESCR_CLASSTRIB",
        "REGIME_IVA_2026",
        "FONTE_LEGAL_IVA",
        "NIVEL_CONFIANCA_PRICETAX",
        "FLAG_ALIMENTO",
        "FLAG_CESTA_BASICA",
        "FLAG_HORTIFRUTI_OVOS",
        "FLAG_RED_60",
        "FLAG_DEPENDE_DESTINACAO",
        "IBS_UF_TESTE_2026",
        "IBS_MUN_TESTE_2026",
        "CBS_TESTE_2026",
        "OBS_ALIMENTO",
        "OBS_DESTINACAO",
        "ALERTA_APP",
        "FLAG_MONOFASICO_CBS",
        "FLAG_IMPOSTO_SELETIVO",
        "FLAG_CASHBACK_SOCIAL",
        "OBS_REGIME_ESPECIAL",
        "REGIME_IVA_2026_FINAL",
        "FONTE_LEGAL_FINAL",
        "NIVEL_CONFIANCA_FINAL",
        "IBS_UF_TESTE_2026_FINAL",
        "IBS_MUN_TESTE_2026_FINAL",
        "CBS_TESTE_2026_FINAL",
    ]
    for c in required_cols:
        if c not in df.columns:
            df[c] = ""

    # Normaliza NCM para 8 dígitos numéricos
    df["NCM"] = df["NCM"].fillna("").astype(str)
    df["NCM_DIG"] = (
        df["NCM"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)
    )

    return df


def buscar_ncm(df: pd.DataFrame, ncm_str: str) -> Optional[pd.Series]:
    norm = only_digits(ncm_str)
    if len(norm) != 8 or df.empty:
        return None
    row = df.loc[df["NCM_DIG"] == norm]
    if row.empty:
        return None
    return row.iloc[0]


# --------------------------------------------------
# PARSER SPED PIS/COFINS (BLOCO M)
# --------------------------------------------------
M200_HEADERS = [
    "Valor Total da Contribuição Não-cumulativa do Período",
    "Valor do Crédito Descontado, Apurado no Próprio Período da Escrituração",
    "Valor do Crédito Descontado, Apurado em Período de Apuração Anterior",
    "Valor Total da Contribuição Não Cumulativa Devida",
    "Valor Retido na Fonte Deduzido no Período (Não Cumulativo)",
    "Outras Deduções do Regime Não Cumulativo no Período",
    "Valor da Contribuição Não Cumulativa a Recolher/Pagar",
    "Valor Total da Contribuição Cumulativa do Período",
    "Valor Retido na Fonte Deduzido no Período (Cumulativo)",
    "Outras Deduções do Regime Cumulativo no Período",
    "Valor da Contribuição Cumulativa a Recolher/Pagar",
    "Valor Total da Contribuição a Recolher/Pagar no Período",
]
M600_HEADERS = M200_HEADERS[:]

COD_CONT_DESC: Dict[str, str] = {
    "01": "Contribuição não-cumulativa apurada à alíquota básica",
    "02": "Contribuição não-cumulativa apurada à alíquota diferenciada/reduzida",
    "03": "Contribuição não-cumulativa – receitas com alíquota específica",
    "04": "Contribuição não-cumulativa – receitas sujeitas à alíquota zero",
    "05": "Contribuição não-cumulativa – receitas não alcançadas (isenção/suspensão)",
    "06": "Contribuição não-cumulativa – regime monofásico",
    "07": "Contribuição não-cumulativa – substituição tributária",
    "08": "Contribuição não-cumulativa – alíquota por unidade de medida",
    "09": "Contribuição não-cumulativa – outras hipóteses legais",
    "12": "Contribuição cumulativa – alíquota básica",
    "13": "Contribuição cumulativa – alíquota diferenciada",
    "14": "Contribuição cumulativa – alíquota zero",
    "15": "Contribuição cumulativa – outras hipóteses legais",
}

NAT_REC_DESC: Dict[str, str] = {
    "401": "Exportação de mercadorias para o exterior",
    "405": "Desperdícios, resíduos ou aparas de plástico, papel, vidro e metais",
    "908": "Vendas de mercadorias destinadas ao consumo",
    "911": "Receitas financeiras, inclusive variação cambial ativa tributável",
    "999": "Código genérico – Operações tributáveis à alíquota zero/isenção/suspensão",
}

NAT_BC_CRED_DESC: Dict[str, str] = {
    "01": "Aquisição de bens para revenda",
    "02": "Aquisição de bens e serviços utilizados como insumo",
    "03": "Energia elétrica e térmica",
    "04": "Aluguéis de prédios",
    "05": "Aluguéis de máquinas e equipamentos",
    "06": "Armazenagem de mercadoria e frete na venda",
    "07": "Arrendamento mercantil",
    "08": "Encargos de depreciação e amortização",
    "09": "Devolução de vendas",
    "10": "Outras operações com direito a crédito",
    "11": "Atividade de transporte de cargas",
    "12": "Atividade imobiliária",
    "13": "Atividade de construção civil",
    "14": "Atividade de serviços de saúde",
    "15": "Atividade de telecomunicações",
    "16": "Atividade de transporte de passageiros",
    "17": "Atividade de radiodifusão",
    "18": "Atividade de serviços de informática",
    "19": "Atividade de serviços de vigilância e transporte de valores",
    "20": "Atividade de serviços de limpeza, conservação e manutenção",
    "21": "Atividade de serviços de agenciamento de publicidade e propaganda",
    "22": "Atividade de serviços de engenharia e arquitetura",
    "23": "Atividade de serviços de consultoria e auditoria",
    "24": "Atividade de serviços de advocacia",
    "25": "Atividade de serviços de contabilidade",
    "26": "Atividade de serviços de treinamento e capacitação",
    "27": "Atividade de serviços de locação de bens móveis",
    "28": "Atividade de serviços de cessão de mão de obra",
    "29": "Atividade de serviços de corretagem de seguros",
    "30": "Atividade de serviços de representação comercial",
    "31": "Atividade de serviços de intermediação de negócios",
    "32": "Atividade de serviços de propaganda e publicidade",
    "33": "Atividade de serviços de assessoria e consultoria técnica",
    "34": "Atividade de serviços de organização de feiras e eventos",
    "35": "Atividade de serviços de pesquisa e desenvolvimento",
    "36": "Atividade de serviços de tratamento de dados",
    "37": "Atividade de serviços de logística",
    "38": "Atividade de serviços de armazenagem",
    "39": "Atividade de serviços de transporte rodoviário de cargas",
    "40": "Atividade de serviços de transporte ferroviário de cargas",
    "41": "Atividade de serviços de transporte aquaviário de cargas",
    "42": "Atividade de serviços de transporte aéreo de cargas",
    "43": "Atividade de serviços de transporte dutoviário de cargas",
    "44": "Atividade de serviços de transporte multimodal de cargas",
    "45": "Atividade de serviços de transporte de valores",
    "46": "Atividade de serviços de segurança",
    "47": "Atividade de serviços de vigilância",
    "48": "Atividade de serviços de limpeza e conservação",
    "49": "Atividade de serviços de manutenção e reparação",
    "50": "Atividade de serviços de instalação e montagem",
    "51": "Atividade de serviços de construção civil",
    "52": "Atividade de serviços de engenharia",
    "53": "Atividade de serviços de arquitetura",
    "54": "Atividade de serviços de agronomia",
    "55": "Atividade de serviços de geologia",
    "56": "Atividade de serviços de meteorologia",
    "57": "Atividade de serviços de oceanografia",
    "58": "Atividade de serviços de cartografia",
    "59": "Atividade de serviços de topografia",
    "60": "Atividade de serviços de aerofotogrametria",
    "61": "Atividade de serviços de hidrografia",
    "62": "Atividade de serviços de batimetria",
    "63": "Atividade de serviços de sismologia",
    "64": "Atividade de serviços de geofísica",
    "65": "Atividade de serviços de prospecção",
    "66": "Atividade de serviços de perfuração",
    "67": "Atividade de serviços de exploração",
    "68": "Atividade de serviços de produção",
    "69": "Atividade de serviços de refino",
    "70": "Atividade de serviços de distribuição",
    "71": "Atividade de serviços de comercialização",
    "72": "Atividade de serviços de importação",
    "73": "Atividade de serviços de exportação",
    "74": "Atividade de serviços de armazenagem",
    "75": "Atividade de serviços de transporte",
    "76": "Atividade de serviços de comunicação",
    "77": "Atividade de serviços de informática",
    "78": "Atividade de serviços de saúde",
    "79": "Atividade de serviços de educação",
    "80": "Atividade de serviços de cultura",
    "81": "Atividade de serviços de esporte",
    "82": "Atividade de serviços de lazer",
    "83": "Atividade de serviços de turismo",
    "84": "Atividade de serviços de hotelaria",
    "85": "Atividade de serviços de alimentação",
    "86": "Atividade de serviços de bebidas",
    "87": "Atividade de serviços de vestuário",
    "88": "Atividade de serviços de calçados",
    "89": "Atividade de serviços de joias",
    "90": "Atividade de serviços de relógios",
    "91": "Atividade de serviços de cosméticos",
    "92": "Atividade de serviços de perfumaria",
    "93": "Atividade de serviços de higiene",
    "94": "Atividade de serviços de limpeza",
    "95": "Atividade de serviços de conservação",
    "96": "Atividade de serviços de manutenção",
    "97": "Atividade de serviços de reparação",
    "98": "Atividade de serviços de instalação",
    "99": "Atividade de serviços de montagem",
}


def parse_sped_bloco_m(file_content: bytes) -> Dict[str, Any]:
    """
    Analisa o arquivo SPED PIS/COFINS (Bloco M) e extrai informações relevantes.
    """
    try:
        content = file_content.decode("latin-1")
    except UnicodeDecodeError:
        content = file_content.decode("utf-8", errors="ignore")

    lines = content.splitlines()
    data = {
        "competencia": "",
        "m200": {},
        "m600": {},
        "m210": [],
        "m610": [],
        "m400": [],
        "m800": [],
    }

    # 0. Busca a competência (Bloco 0000)
    for line in lines:
        if line.startswith("|0000|"):
            parts = line.split("|")
            if len(parts) >= 6:
                data["competencia"] = competencia_from_dt(parts[4], parts[5])
            break

    # 1. Busca M200 (PIS Não-Cumulativo)
    for line in lines:
        if line.startswith("|M200|"):
            parts = line.split("|")
            if len(parts) >= 14:
                for i, header in enumerate(M200_HEADERS):
                    data["m200"][header] = to_float_br(parts[i + 2])
            break

    # 2. Busca M600 (COFINS Não-Cumulativo)
    for line in lines:
        if line.startswith("|M600|"):
            parts = line.split("|")
            if len(parts) >= 14:
                for i, header in enumerate(M600_HEADERS):
                    data["m600"][header] = to_float_br(parts[i + 2])
            break

    # 3. Busca M210 (Detalhamento PIS Não-Cumulativo)
    for line in lines:
        if line.startswith("|M210|"):
            parts = line.split("|")
            if len(parts) >= 10:
                cod_cont = parts[2]
                desc = COD_CONT_DESC.get(cod_cont, f"Código {cod_cont} Desconhecido")
                data["m210"].append(
                    {
                        "cod_cont": cod_cont,
                        "descricao": desc,
                        "vl_rec_bruta": to_float_br(parts[3]),
                        "vl_bc_cont": to_float_br(parts[4]),
                        "aliq_pis": to_float_br(parts[5]),
                        "vl_cont": to_float_br(parts[6]),
                        "cod_rec": parts[7],
                        "vl_ajus_ac": to_float_br(parts[8]),
                        "vl_ajus_red": to_float_br(parts[9]),
                    }
                )

    # 4. Busca M610 (Detalhamento COFINS Não-Cumulativo)
    for line in lines:
        if line.startswith("|M610|"):
            parts = line.split("|")
            if len(parts) >= 10:
                cod_cont = parts[2]
                desc = COD_CONT_DESC.get(cod_cont, f"Código {cod_cont} Desconhecido")
                data["m610"].append(
                    {
                        "cod_cont": cod_cont,
                        "descricao": desc,
                        "vl_rec_bruta": to_float_br(parts[3]),
                        "vl_bc_cont": to_float_br(parts[4]),
                        "aliq_cofins": to_float_br(parts[5]),
                        "vl_cont": to_float_br(parts[6]),
                        "cod_rec": parts[7],
                        "vl_ajus_ac": to_float_br(parts[8]),
                        "vl_ajus_red": to_float_br(parts[9]),
                    }
                )

    # 5. Busca M400 (Receitas Não-Tributadas PIS)
    for line in lines:
        if line.startswith("|M400|"):
            parts = line.split("|")
            if len(parts) >= 4:
                data["m400"].append(
                    {
                        "vl_rec_nao_trib": to_float_br(parts[2]),
                        "vl_rec_cum": to_float_br(parts[3]),
                    }
                )

    # 6. Busca M800 (Receitas Não-Tributadas COFINS)
    for line in lines:
        if line.startswith("|M800|"):
            parts = line.split("|")
            if len(parts) >= 4:
                data["m800"].append(
                    {
                        "vl_rec_nao_trib": to_float_br(parts[2]),
                        "vl_rec_cum": to_float_br(parts[3]),
                    }
                )

    # 7. Busca M410 (Detalhamento Receitas Não-Tributadas PIS)
    for line in lines:
        if line.startswith("|M410|"):
            parts = line.split("|")
            if len(parts) >= 6:
                cod_nat_rec = parts[2]
                desc = NAT_REC_DESC.get(
                    cod_nat_rec, f"Código {cod_nat_rec} Desconhecido"
                )
                data["m400"].append(
                    {
                        "cod_nat_rec": cod_nat_rec,
                        "descricao": desc,
                        "vl_rec_nao_trib": to_float_br(parts[3]),
                        "cod_cta": parts[4],
                        "desc_compl": parts[5],
                    }
                )

    # 8. Busca M810 (Detalhamento Receitas Não-Tributadas COFINS)
    for line in lines:
        if line.startswith("|M810|"):
            parts = line.split("|")
            if len(parts) >= 6:
                cod_nat_rec = parts[2]
                desc = NAT_REC_DESC.get(
                    cod_nat_rec, f"Código {cod_nat_rec} Desconhecido"
                )
                data["m800"].append(
                    {
                        "cod_nat_rec": cod_nat_rec,
                        "descricao": desc,
                        "vl_rec_nao_trib": to_float_br(parts[3]),
                        "cod_cta": parts[4],
                        "desc_compl": parts[5],
                    }
                )

    return data


# --------------------------------------------------
# INTERFACE STREAMLIT
# --------------------------------------------------
def display_ncm_result(ncm_row: pd.Series):
    st.markdown(
        f'<div class="pricetax-card">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pricetax-title">NCM {ncm_row["NCM_DIG"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pricetax-subtitle">{ncm_row["NCM_DESCRICAO"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f'<div class="pricetax-metric-label">Segmento</div>'
            f'<div class="pricetax-metric-value">{ncm_row["SEGMENTO_PRICETAX"]}</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="pricetax-metric-label">Subsegmento</div>'
            f'<div class="pricetax-metric-value">{ncm_row["SUBSEGMENTO"]}</div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="pricetax-metric-label">Nível de Confiança</div>'
            f'<div class="pricetax-metric-value">{ncm_row["NIVEL_CONFIANCA_FINAL"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.subheader("Regime de Tributação IBS/CBS (2026)")

    st.markdown(
        f'<div class="pill pill-regime">Regime: {ncm_row["REGIME_IVA_2026_FINAL"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="pricetax-card-soft" style="margin-top: 15px;">'
        f'<p style="font-size: 0.9rem; color: #BBBBBB;">'
        f'**Classificação Tributária:** {ncm_row["CLASSTRIB_IBS_CBS"]} - {ncm_row["DESCR_CLASSTRIB"]}'
        f'</p>'
        f'<p style="font-size: 0.8rem; color: #888888; margin-top: 5px;">'
        f'**Fonte Legal:** {ncm_row["FONTE_LEGAL_FINAL"]}'
        f'</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Alíquotas de Teste (2026)")
    col_ibs_uf, col_ibs_mun, col_cbs = st.columns(3)

    with col_ibs_uf:
        st.markdown(
            f'<div class="pricetax-metric-label">IBS (Estadual)</div>'
            f'<div class="pricetax-metric-value">{pct_str(ncm_row["IBS_UF_TESTE_2026_FINAL"])}</div>',
            unsafe_allow_html=True,
        )
    with col_ibs_mun:
        st.markdown(
            f'<div class="pricetax-metric-label">IBS (Municipal)</div>'
            f'<div class="pricetax-metric-value">{pct_str(ncm_row["IBS_MUN_TESTE_2026_FINAL"])}</div>',
            unsafe_allow_html=True,
        )
    with col_cbs:
        st.markdown(
            f'<div class="pricetax-metric-label">CBS (Federal)</div>'
            f'<div class="pricetax-metric-value">{pct_str(ncm_row["CBS_TESTE_2026_FINAL"])}</div>',
            unsafe_allow_html=True,
        )

    if ncm_row["ALERTA_APP"]:
        st.markdown("---")
        st.markdown(
            f'<div class="pricetax-card-erro">'
            f'<p style="font-size: 0.9rem; color: #FFDCDC;">'
            f'**ALERTA:** {ncm_row["ALERTA_APP"]}'
            f'</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if ncm_row["OBS_ALIMENTO"]:
        st.markdown("---")
        st.info(f'**Observação Alimento:** {ncm_row["OBS_ALIMENTO"]}')

    if ncm_row["OBS_DESTINACAO"]:
        st.markdown("---")
        st.info(f'**Observação Destinação:** {ncm_row["OBS_DESTINACAO"]}')

    if ncm_row["OBS_REGIME_ESPECIAL"]:
        st.markdown("---")
        st.info(f'**Observação Regime Especial:** {ncm_row["OBS_REGIME_ESPECIAL"]}')


def display_sped_result(sped_data: Dict[str, Any]):
    st.markdown(
        f'<div class="pricetax-card">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pricetax-title">Análise SPED PIS/COFINS</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pricetax-subtitle">Competência: {sped_data["competencia"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Resumo M200/M600
    st.subheader("Resumo de Apuração (Blocos M200/M600)")
    col_pis, col_cofins = st.columns(2)

    with col_pis:
        st.markdown(
            f'<div class="pricetax-card-soft">',
            unsafe_allow_html=True,
        )
        # Ajuste da cor do título para usar o dourado
        st.markdown(
            f'<p class="pis-cofins-title">PIS (Não-Cumulativo)</p>',
            unsafe_allow_html=True,
        )
        for k, v in sped_data["m200"].items():
            st.markdown(
                f'<div style="display: flex; justify-content: space-between; margin-top: 5px;">'
                f'<span style="font-size: 0.85rem; color: #BBBBBB;">{k}:</span>'
                f'<span style="font-size: 0.9rem; font-weight: 500; color: {SECONDARY_ACCENT};">R$ {v:,.2f}'.replace(
                    ",", "X"
                ).replace(".", ",").replace("X", ".")
                + "</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_cofins:
        st.markdown(
            f'<div class="pricetax-card-soft">',
            unsafe_allow_html=True,
        )
        # Ajuste da cor do título para usar o dourado
        st.markdown(
            f'<p class="pis-cofins-title">COFINS (Não-Cumulativo)</p>',
            unsafe_allow_html=True,
        )
        for k, v in sped_data["m600"].items():
            st.markdown(
                f'<div style="display: flex; justify-content: space-between; margin-top: 5px;">'
                f'<span style="font-size: 0.85rem; color: #BBBBBB;">{k}:</span>'
                f'<span style="font-size: 0.9rem; font-weight: 500; color: {SECONDARY_ACCENT};">R$ {v:,.2f}'.replace(
                    ",", "X"
                ).replace(".", ",").replace("X", ".")
                + "</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Detalhamento M210/M610
    st.subheader("Detalhamento da Contribuição (Blocos M210/M610)")
    if sped_data["m210"] or sped_data["m610"]:
        tab_pis, tab_cofins = st.tabs(["PIS (M210)", "COFINS (M610)"])

        with tab_pis:
            for item in sped_data["m210"]:
                st.markdown(
                    f'<div class="pricetax-card-soft" style="margin-bottom: 10px;">'
                    f'<p style="font-size: 1rem; font-weight: 600; color: {SECONDARY_ACCENT};">'
                    f'[{item["cod_cont"]}] {item["descricao"]}'
                    f'</p>'
                    f'<div style="margin-top: 10px;">'
                    f'<span class="pricetax-metric-label">Receita Bruta:</span> '
                    f'<span class="pricetax-metric-value">R$ {item["vl_rec_bruta"]:,.2f}'.replace(
                        ",", "X"
                    ).replace(".", ",").replace("X", ".")
                    + "</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        with tab_cofins:
            for item in sped_data["m610"]:
                st.markdown(
                    f'<div class="pricetax-card-soft" style="margin-bottom: 10px;">'
                    f'<p style="font-size: 1rem; font-weight: 600; color: {SECONDARY_ACCENT};">'
                    f'[{item["cod_cont"]}] {item["descricao"]}'
                    f'</p>'
                    f'<div style="margin-top: 10px;">'
                    f'<span class="pricetax-metric-label">Receita Bruta:</span> '
                    f'<span class="pricetax-metric-value">R$ {item["vl_rec_bruta"]:,.2f}'.replace(
                        ",", "X"
                    ).replace(".", ",").replace("X", ".")
                    + "</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("Nenhum detalhamento de contribuição (M210/M610) encontrado.")

    st.markdown("---")

    # Receitas Não-Tributadas M400/M800
    st.subheader("Receitas Não-Tributadas (Blocos M400/M800)")
    if sped_data["m400"] or sped_data["m800"]:
        tab_pis_nt, tab_cofins_nt = st.tabs(
            ["PIS Não-Tributado (M400/M410)", "COFINS Não-Tributado (M800/M810)"]
        )

        with tab_pis_nt:
            for item in sped_data["m400"]:
                if "cod_nat_rec" in item:
                    st.markdown(
                        f'<div class="pricetax-card-soft" style="margin-bottom: 10px;">'
                        f'<p style="font-size: 1rem; font-weight: 600; color: {SECONDARY_ACCENT};">'
                        f'[{item["cod_nat_rec"]}] {item["descricao"]}'
                        f'</p>'
                        f'<div style="margin-top: 10px;">'
                        f'<span class="pricetax-metric-label">Valor da Receita Não-Tributada:</span> '
                        f'<span class="pricetax-metric-value">R$ {item["vl_rec_nao_trib"]:,.2f}'.replace(
                            ",", "X"
                        ).replace(".", ",").replace("X", ".")
                        + "</span>"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="pricetax-card-soft" style="margin-bottom: 10px;">'
                        f'<p style="font-size: 1rem; font-weight: 600; color: {SECONDARY_ACCENT};">'
                        f'Total PIS Não-Tributado'
                        f'</p>'
                        f'<div style="margin-top: 10px;">'
                        f'<span class="pricetax-metric-label">Valor da Receita Não-Tributada:</span> '
                        f'<span class="pricetax-metric-value">R$ {item["vl_rec_nao_trib"]:,.2f}'.replace(
                            ",", "X"
                        ).replace(".", ",").replace("X", ".")
                        + "</span>"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        with tab_cofins_nt:
            for item in sped_data["m800"]:
                if "cod_nat_rec" in item:
                    st.markdown(
                        f'<div class="pricetax-card-soft" style="margin-bottom: 10px;">'
                        f'<p style="font-size: 1rem; font-weight: 600; color: {SECONDARY_ACCENT};">'
                        f'[{item["cod_nat_rec"]}] {item["descricao"]}'
                        f'</p>'
                        f'<div style="margin-top: 10px;">'
                        f'<span class="pricetax-metric-label">Valor da Receita Não-Tributada:</span> '
                        f'<span class="pricetax-metric-value">R$ {item["vl_rec_nao_trib"]:,.2f}'.replace(
                            ",", "X"
                        ).replace(".", ",").replace("X", ".")
                        + "</span>"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="pricetax-card-soft" style="margin-bottom: 10px;">'
                        f'<p style="font-size: 1rem; font-weight: 600; color: {SECONDARY_ACCENT};">'
                        f'Total COFINS Não-Tributado'
                        f'</p>'
                        f'<div style="margin-top: 10px;">'
                        f'<span class="pricetax-metric-label">Valor da Receita Não-Tributada:</span> '
                        f'<span class="pricetax-metric-value">R$ {item["vl_rec_nao_trib"]:,.2f}'.replace(
                            ",", "X"
                        ).replace(".", ",").replace("X", ".")
                        + "</span>"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.info("Nenhuma receita não-tributada (M400/M800) encontrada.")


def main():
    st.title("PRICETAX • Classificador IBS/CBS & SPED PIS/COFINS")
    st.markdown(
        "Consulte o NCM do seu produto, visualize as alíquotas de IBS e CBS para 2026 e audite o SPED PIS/COFINS."
    )

    tab_ncm, tab_sped = st.tabs(
        ["Consulta NCM → IBS/CBS 2026", "SPED PIS/COFINS → Excel (Bloco M)"]
    )

    with tab_ncm:
        st.markdown(
            f'<div class="pricetax-card-soft" style="margin-bottom: 20px;">'
            f'<div class="pricetax-badge">CONSULTA DE PRODUTOS</div>'
            f'<p style="font-size: 0.9rem; color: #BBBBBB; margin-top: 10px;">'
            f'Informe o código NCM do seu produto e veja a tributação de IBS e CBS simulada para o ano de teste de 2026, com base nas regras de transição da EC 132/2023 e da LC 214/2025.'
            f'</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        ncm_input = st.text_input(
            "Informe o NCM (com ou sem pontos)",
            placeholder="Ex.: 10063021 ou 10.06.30.21",
            key="ncm_input",
        )

        if st.button("Consultar NCM", type="primary"):
            if ncm_input:
                with st.spinner("Buscando informações..."):
                    df_tipi = load_tipi_base()
                    ncm_row = buscar_ncm(df_tipi, ncm_input)

                    if ncm_row is not None:
                        display_ncm_result(ncm_row)
                    else:
                        st.error(
                            f"NCM **{ncm_input}** não encontrado na base de classificação IBS/CBS."
                        )
            else:
                st.warning("Por favor, informe um código NCM para consultar.")

    with tab_sped:
        st.markdown(
            f'<div class="pricetax-card-soft" style="margin-bottom: 20px;">'
            f'<div class="pricetax-badge">AUDITORIA SPED PIS/COFINS</div>'
            f'<p style="font-size: 0.9rem; color: #BBBBBB; margin-top: 10px;">'
            f'Faça o upload do seu arquivo SPED PIS/COFINS (bloco M) para extrair e visualizar os dados de apuração e detalhamento de receitas e créditos.'
            f'</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Selecione o arquivo SPED PIS/COFINS (.txt)",
            type=["txt"],
            key="sped_file_uploader",
        )

        if uploaded_file is not None:
            with st.spinner("Analisando arquivo SPED..."):
                file_content = uploaded_file.read()
                sped_data = parse_sped_bloco_m(file_content)
                display_sped_result(sped_data)


if __name__ == "__main__":
    main()
