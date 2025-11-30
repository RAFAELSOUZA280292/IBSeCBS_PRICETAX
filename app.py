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
# UTILITÁRIOS
# --------------------------------------------------
def only_digits(s: Optional[str]) -> str:
    return re.sub(r"\D+", "", s or "")

def to_float_br(s) -> float:
    if not s:
        return 0.0
    s = str(s)
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
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

# --------------------------------------------------
# CARREGAR BASE TIPI (PROCURA PLANILHA OFICIAL OU MIND7)
# --------------------------------------------------
TIPI_DEFAULT_NAME = "PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx"
ALT_TIPI_NAME = "TIPI_IBS_CBS_CLASSIFICADA_MIND7.xlsx"

@st.cache_data(show_spinner=False)
def load_tipi_base() -> pd.DataFrame:
    paths = [
        Path(TIPI_DEFAULT_NAME), Path.cwd() / TIPI_DEFAULT_NAME,
        Path(ALT_TIPI_NAME), Path.cwd() / ALT_TIPI_NAME
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

df_tipi = load_tipi_base()

# --------------------------------------------------
# PARSER SPED PIS/COFINS (BLOCO M) - LÓGICA FUNCIONAL
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
# PARSER SPED – EXTRAI TODAS AS NOTAS E FILTRA ITENS DE SAÍDA POR CFOP
# --------------------------------------------------
def parse_sped_saida(nome_arquivo: str, conteudo: str):
    itens = []
    current_nf = None

    for raw in conteudo.splitlines():
        if not raw or raw == "|":
            continue

        campos = raw.split("|")
        if len(campos) < 3:
            continue

        reg = campos[1].upper()

        # C100 – cabeçalho (não filtra por IND_OPER)
        if reg == "C100":
            cod_mod = campos[6].strip()
            serie   = campos[7].strip()
            numero  = campos[8].strip()
            dt_doc  = campos[9].strip()
            vl_doc  = campos[12].strip() if len(campos) > 12 else ""
            current_nf = {
                "ID_NF": f"{nome_arquivo}__{numero}_{serie}",
                "ARQUIVO": nome_arquivo,
                "COD_MOD": cod_mod,
                "SERIE": serie,
                "NUMERO": numero,
                "DT_DOC": dt_doc,
                "VL_DOC": to_float_br(vl_doc),
            }

        # C170 – itens
        elif reg == "C170" and current_nf:
            # Campos: NUM_ITEM(2), COD_ITEM(3), DESCR_COMPL(4), QTD(5), VL_ITEM(7), CFOP(11), NCM(??)
            qtd = to_float_br(campos[5]) if len(campos) > 5 else 0.0
            vl_item = to_float_br(campos[7]) if len(campos) > 7 else 0.0
            cfop   = campos[11].strip() if len(campos) > 11 else ""
            ncm    = campos[8].strip() if len(campos) > 8 else ""
            descr  = campos[4].strip() if len(campos) > 4 else ""

            # Só considera saídas (CFOP 5xxx ou 6xxx)
            if cfop and (cfop.startswith("5") or cfop.startswith("6")):
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

# Consolida SPED e cruza com TIPI
def processar_speds_vendas(files, df_tipi):
    itens_all = []

    for up in files:
        nome = up.name
        if nome.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(up.read()), "r") as z:
                for info in z.infolist():
                    if info.filename.lower().endswith(".txt"):
                        conteudo = z.open(info).read().decode("utf-8", errors="replace")
                        itens_all.extend(parse_sped_saida(info.filename, conteudo))
        else:
            conteudo = up.read().decode("utf-8", errors="replace")
            itens_all.extend(parse_sped_saida(nome, conteudo))

    if not itens_all:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_itens = pd.DataFrame(itens_all)

    # Normaliza NCM
    df_itens["NCM_DIG"] = (
        df_itens["NCM"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(8)
    )

    # Cruza com TIPI
    df_merged = df_itens.merge(
        df_tipi,
        how="left",
        left_on="NCM_DIG",
        right_on="NCM_DIG",
    )

    # Erros de NCM
    df_erros = df_merged[df_merged["NCM_DESCRICAO"].isna()][
        ["NCM_DIG", "DESCR_ITEM", "CFOP", "VL_TOTAL_ITEM"]
    ]

    df_validos = df_merged[df_merged["NCM_DESCRICAO"].notna()].copy()

    # Calcula alíquotas efetivas
    df_validos["IBS_UF"]  = pd.to_numeric(df_validos["IBS_UF_TESTE_2026_FINAL"], errors="coerce").fillna(0)
    df_validos["IBS_MUN"] = pd.to_numeric(df_validos["IBS_MUN_TESTE_2026_FINAL"], errors="coerce").fillna(0)
    df_validos["CBS"]     = pd.to_numeric(df_validos["CBS_TESTE_2026_FINAL"], errors="coerce").fillna(0)

    df_validos["IBS_EFETIVO"]    = df_validos["IBS_UF"] + df_validos["IBS_MUN"]
    df_validos["TOTAL_IVA_2026"] = df_validos["IBS_EFETIVO"] + df_validos["CBS"]

    # Ranking por produto
    df_ranking = (
        df_validos.groupby([
            "NCM_DIG", "NCM_DESCRICAO", "CFOP",
            "REGIME_IVA_2026_FINAL",
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

    df_validos = df_validos.sort_values(["DT_DOC", "ID_NF"])
    return df_validos, df_ranking, df_erros

# --------------------------------------------------
# INTERFACE – TABS
# --------------------------------------------------
st.markdown(
    """
    <div class="pricetax-title">PRICETAX • IBS/CBS 2026 & Ranking SPED</div>
    <div class="pricetax-subtitle">
        Consulte o NCM do seu produto e analise suas vendas pelo SPED com a tributação de 2026.
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "🔍 Consulta NCM → IBS/CBS 2026",
    "📊 Ranking de Produtos (via SPED) – IBS/CBS 2026",
    "📝 Bloco M (PIS/COFINS) – Auditoria", # Nova aba para o Bloco M
])

# Aba de consulta NCM (Mantida)
with tabs[0]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Consulta de produtos</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Informe o NCM e veja o regime de IVA e alíquotas IBS/CBS simuladas para 2026.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
            # Campos principais
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

            # Métricas
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

            # Parâmetros
            st.subheader("Parâmetros de classificação", divider="gray")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown("**Produto é alimento?**")
                st.markdown(f"<span style='color:{PRIMARY_YELLOW};font-weight:600;'>{badge_flag(flag_alim)}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown("**Cesta Básica Nacional?**")
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
            # Limpa textos "nan"
            def clean_txt(v):
                s = str(v or "").strip()
                return "" if s.lower() == "nan" else s

            alerta_fmt = clean_txt(row.get("ALERTA_APP"))
            obs_alim   = clean_txt(row.get("OBS_ALIMENTO"))
            obs_dest   = clean_txt(row.get("OBS_DESTINACAO"))
            reg_extra  = clean_txt(row.get("OBS_REGIME_ESPECIAL"))

            # Ajustes padrão para RED_60
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

# Aba de ranking SPED (Mantida)
with tabs[1]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Análise de Vendas (Saídas SPED)</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Faça upload de arquivos SPED Contribuições (.txt ou .zip). O sistema irá:
                <br><br>
                • Ler todas as notas de saída (C100/C170)<br>
                • Consolidar itens por CFOP, NCM e Descrição<br>
                • Gerar ranking de faturamento<br>
                • Cruzar com a tabela PRICETAX IBS/CBS para 2026<br>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Selecione arquivos SPED (.txt ou .zip)", type=["txt", "zip"], accept_multiple_files=True, key="sped_upload_rank"
    )

    if uploaded:
        if st.button("Processar SPED e Gerar Ranking", type="primary"):
            with st.spinner("Processando arquivos SPED..."):
                df_itens, df_ranking, df_erros = processar_speds_vendas(uploaded, df_tipi)

            if df_itens.empty:
                st.error("Nenhuma nota de saída foi encontrada nos arquivos fornecidos.")
            else:
                st.success("Processamento concluído!")
                st.markdown("---")

                # Função para criar Excel em memória
                def to_excel(df):
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        df.to_excel(w, index=False)
                    buf.seek(0)
                    return buf

                # Downloads
                colA, colB, colC = st.columns(3)
                with colA:
                    st.download_button(
                        "📥 Itens Detalhados (C170 + IVA 2026)",
                        data=to_excel(df_itens),
                        file_name="PRICETAX_Itens_Detalhados_2026.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                with colB:
                    st.download_button(
                        "📥 Ranking de Produtos",
                        data=to_excel(df_ranking),
                        file_name="PRICETAX_Ranking_Produtos_2026.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                with colC:
                    st.download_button(
                        "📥 Erros de NCM",
                        data=to_excel(df_erros),
                        file_name="PRICETAX_Erros_NCM.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                st.markdown("---")

                # Tabela ranking
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

                total_fat = df_itens["VL_TOTAL_ITEM"].sum()
                total_notas = df_itens["ID_NF"].nunique()

                st.markdown(
                    f"""
                    <div class="pricetax-card-soft" style="margin-top:1rem;">
                        <div style="font-size:1rem;color:{PRIMARY_YELLOW};font-weight:600;">📊 Insight PRICETAX</div>
                        <div style="margin-top:0.4rem;font-size:0.9rem;color:#E0E0E0;">
                            • Faturamento total analisado: <b>R$ {total_fat:,.2f}</b><br>
                            • Total de notas de saída: <b>{total_notas}</b><br>
                            • Ranking baseado em CFOP + NCM + Descrição, cruzado com IVA 2026<br>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Nenhum arquivo enviado ainda. Selecione um ou mais SPEDs para iniciar a análise.")

# Nova Aba para Bloco M (Corrigida)
with tabs[2]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Auditoria Bloco M (PIS/COFINS)</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Faça o upload do seu arquivo SPED PIS/COFINS (.txt) para extrair e visualizar os dados de apuração e detalhamento de receitas e créditos (Blocos M200, M600, M210, M610, M400, M800).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_bloco_m = st.file_uploader(
        "Selecione o arquivo SPED PIS/COFINS (.txt)",
        type=["txt"],
        key="sped_bloco_m_upload",
    )

    if uploaded_bloco_m is not None:
        with st.spinner("Analisando arquivo SPED (Bloco M)..."):
            file_content = uploaded_bloco_m.read()
            sped_data = parse_sped_bloco_m(file_content)

        if sped_data["m200"] or sped_data["m600"]:
            st.success(f"Análise do Bloco M concluída para a competência: {sped_data['competencia']}")
            st.markdown("---")

            # Função para exibir os resultados do Bloco M (simplificada para este contexto)
            def display_sped_bloco_m_result(data: Dict[str, Any]):
                st.subheader("Resumo de Apuração (Blocos M200/M600)")
                col_pis, col_cofins = st.columns(2)

                with col_pis:
                    st.markdown(f"**PIS (Não-Cumulativo)**")
                    for k, v in data["m200"].items():
                        st.markdown(f"- {k}: R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                with col_cofins:
                    st.markdown(f"**COFINS (Não-Cumulativo)**")
                    for k, v in data["m600"].items():
                        st.markdown(f"- {k}: R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                st.markdown("---")
                st.subheader("Detalhamento da Contribuição (Blocos M210/M610)")
                if data["m210"]:
                    st.markdown("**PIS (M210)**")
                    for item in data["m210"]:
                        st.markdown(f'- [{item["cod_cont"]}] {item["descricao"]} - Receita Bruta: R$ {item["vl_rec_bruta"]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))
                if data["m610"]:
                    st.markdown("**COFINS (M610)**")
                    for item in data["m610"]:
                        st.markdown(f'- [{item["cod_cont"]}] {item["descricao"]} - Receita Bruta: R$ {item["vl_rec_bruta"]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))

                st.markdown("---")
                st.subheader("Receitas Não-Tributadas (Blocos M400/M800)")
                if data["m400"]:
                    st.markdown("**PIS Não-Tributado (M400/M410)**")
                    for item in data["m400"]:
                        if "cod_nat_rec" in item:
                            st.markdown(f'- [{item["cod_nat_rec"]}] {item["descricao"]} - Valor: R$ {item["vl_rec_nao_trib"]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))
                        else:
                            st.markdown(f'- Total PIS Não-Tributado: R$ {item["vl_rec_nao_trib"]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))
                if data["m800"]:
                    st.markdown("**COFINS Não-Tributado (M800/M810)**")
                    for item in data["m800"]:
                        if "cod_nat_rec" in item:
                            st.markdown(f'- [{item["cod_nat_rec"]}] {item["descricao"]} - Valor: R$ {item["vl_rec_nao_trib"]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))
                        else:
                            st.markdown(f'- Total COFINS Não-Tributado: R$ {item["vl_rec_nao_trib"]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))


            display_sped_bloco_m_result(sped_data)
        else:
            st.error("Não foi possível encontrar os registros M200 ou M600 no arquivo SPED. Verifique se o arquivo está correto.")

# --------------------------------------------------
# FIM DA INTERFACE
# --------------------------------------------------
# O restante do código da interface (que não foi alterado) é mantido.
# As funções parse_sped_saida e processar_speds_vendas (para a aba de Ranking)
# são mantidas, pois fazem parte da funcionalidade original do seu arquivo.
# Apenas a lógica do Bloco M foi adicionada/corrigida.
