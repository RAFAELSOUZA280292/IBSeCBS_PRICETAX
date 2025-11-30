import io
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st
import plotly.express as px

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
    return None if row.empty else row.iloc[0]

df_tipi = load_tipi_base()

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
                # |C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|CHV_NFE|...
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
# PARSER BLOCO M (PIS/COFINS) – AUDITORIA
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

def parse_sped_bloco_m(file_content: bytes) -> Dict[str, Any]:
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

    for line in lines:
        if line.startswith("|0000|"):
            parts = line.split("|")
            if len(parts) >= 6:
                data["competencia"] = competencia_from_dt(parts[4], parts[5])
            break

    for line in lines:
        if line.startswith("|M200|"):
            parts = line.split("|")
            if len(parts) >= 14:
                for i, header in enumerate(M200_HEADERS):
                    data["m200"][header] = to_float_br(parts[i + 2])
            break

    for line in lines:
        if line.startswith("|M600|"):
            parts = line.split("|")
            if len(parts) >= 14:
                for i, header in enumerate(M600_HEADERS):
                    data["m600"][header] = to_float_br(parts[i + 2])
            break

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
# CABEÇALHO / TABS
# --------------------------------------------------
st.markdown(
    """
    <div class="pricetax-title">PRICETAX • IBS/CBS 2026 & Ranking SPED</div>
    <div class="pricetax-subtitle">
        Consulte o NCM do seu produto, gere ranking de saídas pelo SPED e audite o Bloco M (PIS/COFINS).
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "🔍 Consulta NCM → IBS/CBS 2026",
    "📊 Ranking de Saídas (SPED PIS/COFINS)",
    "📝 Bloco M (PIS/COFINS) – Auditoria",
])

# --------------------------------------------------
# ABA 1 – CONSULTA NCM
# --------------------------------------------------
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

            st.markdown(f"**Base legal aplicada:** {fonte or '—'}")
            st.markdown(f"**Alerta PRICETAX:** {alerta_fmt or '—'}")
            st.markdown(f"**Observação sobre alimentos:** {obs_alim or '—'}")
            st.markdown(f"**Observação sobre destinação:** {obs_dest or '—'}")
            st.markdown(f"**Regime especial / motivo adicional:** {reg_extra or '—'}")

# --------------------------------------------------
# ABA 2 – RANKING DE SAÍDAS (SPED) – TOTAL + DOWNLOAD + GRÁFICO
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
                • Gerar um ranking TOTAL com opção de download e gráfico TOP 10.
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
                df_total = df_total.sort_values("VALOR_TOTAL_VENDAS", ascending=False).reset_index(drop=True)

                # DataFrame para visualização com valor formatado BR
                df_vis = df_total.copy()
                df_vis["VALOR_TOTAL_VENDAS"] = df_vis["VALOR_TOTAL_VENDAS"].apply(
                    lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )

                st.success("Processamento concluído!")
                st.markdown("---")

                def to_excel(df: pd.DataFrame) -> bytes:
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        df.to_excel(w, index=False, sheet_name="RANKING_SAIDAS")
                    buf.seek(0)
                    return buf.read()

                st.download_button(
                    "📥 Baixar Ranking de Saídas (Excel)",
                    data=to_excel(df_total),
                    file_name="PRICETAX_Ranking_Saidas_Sped.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                st.markdown("### Ranking de Saídas – TODAS AS LINHAS")
                st.dataframe(df_vis, use_container_width=True)

                total_vendas = df_total["VALOR_TOTAL_VENDAS"].sum()
                total_vendas_fmt = (
                    f"{total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )

                st.markdown(
                    f"""
                    <div class="pricetax-card-soft" style="margin-top:1rem;">
                        <div style="font-size:1rem;color:{PRIMARY_YELLOW};font-weight:600;">📊 Insight PRICETAX</div>
                        <div style="margin-top:0.4rem;font-size:0.9rem;color:#E0E0E0;">
                            • Total geral de vendas (saídas CFOP 5/6/7): <b>R$ {total_vendas_fmt}</b><br>
                            • Arquivos analisados: <b>{total_files}</b><br>
                            • Ranking consolidado por NCM + Descrição + CFOP.<br>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Gráfico TOP 10 – Pizza por NCM
                st.markdown("### 🔥 TOP 10 – Distribuição Percentual por NCM")

                df_top10 = (
                    df_total.groupby("NCM")["VALOR_TOTAL_VENDAS"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                )

                if not df_top10.empty:
                    fig = px.pie(
                        names=df_top10.index,
                        values=df_top10.values,
                        title="TOP 10 – Percentual por NCM (Vendas de Saída)",
                        hole=0.45,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Não há dados suficientes para montar o gráfico TOP 10 por NCM.")
    else:
        st.info("Nenhum arquivo enviado ainda. Selecione um ou mais SPEDs para iniciar a análise.")

# --------------------------------------------------
# ABA 3 – BLOCO M (PIS/COFINS)
# --------------------------------------------------
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

            def display_sped_bloco_m_result(data: Dict[str, Any]):
                st.subheader("Resumo de Apuração (Blocos M200/M600)")
                col_pis, col_cofins = st.columns(2)

                with col_pis:
                    st.markdown("**PIS (Não-Cumulativo)**")
                    for k, v in data["m200"].items():
                        v_fmt = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        st.markdown(f"- {k}: R$ {v_fmt}")

                with col_cofins:
                    st.markdown("**COFINS (Não-Cumulativo)**")
                    for k, v in data["m600"].items():
                        v_fmt = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        st.markdown(f"- {k}: R$ {v_fmt}")

                st.markdown("---")
                st.subheader("Detalhamento da Contribuição (Blocos M210/M610)")
                if data["m210"]:
                    st.markdown("**PIS (M210)**")
                    for item in data["m210"]:
                        v_fmt = f"{item['vl_rec_bruta']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        st.markdown(f'- [{item["cod_cont"]}] {item["descricao"]} - Receita Bruta: R$ {v_fmt}')
                if data["m610"]:
                    st.markdown("**COFINS (M610)**")
                    for item in data["m610"]:
                        v_fmt = f"{item['vl_rec_bruta']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        st.markdown(f'- [{item["cod_cont"]}] {item["descricao"]} - Receita Bruta: R$ {v_fmt}')

                st.markdown("---")
                st.subheader("Receitas Não-Tributadas (Blocos M400/M800)")
                if data["m400"]:
                    st.markdown("**PIS Não-Tributado (M400/M410)**")
                    for item in data["m400"]:
                        if "cod_nat_rec" in item:
                            v_fmt = f"{item['vl_rec_nao_trib']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            st.markdown(f'- [{item["cod_nat_rec"]}] {item["descricao"]} - Valor: R$ {v_fmt}')
                        else:
                            v_fmt = f"{item['vl_rec_nao_trib']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            st.markdown(f'- Total PIS Não-Tributado: R$ {v_fmt}')
                if data["m800"]:
                    st.markdown("**COFINS Não-Tributado (M800/M810)**")
                    for item in data["m800"]:
                        if "cod_nat_rec" in item:
                            v_fmt = f"{item['vl_rec_nao_trib']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            st.markdown(f'- [{item["cod_nat_rec"]}] {item["descricao"]} - Valor: R$ {v_fmt}')
                        else:
                            v_fmt = f"{item['vl_rec_nao_trib']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            st.markdown(f'- Total COFINS Não-Tributado: R$ {v_fmt}')

            display_sped_bloco_m_result(sped_data)
        else:
            st.error("Não foi possível encontrar os registros M200 ou M600 no arquivo SPED. Verifique se o arquivo está correto.")
