# app.py
import io
import re
import zipfile
from pathlib import Path

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

PRIMARY_YELLOW = "#FFC300"
PRIMARY_BLACK = "#050608"
DARK_BLUE = "#001B3A"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {PRIMARY_BLACK};
        color: #F5F5F5;
        font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    .pricetax-title {{
        font-size: 2.2rem;
        font-weight: 700;
        color: {PRIMARY_YELLOW};
    }}
    .pricetax-subtitle {{
        font-size: 0.98rem;
        color: #E0E0E0;
    }}
    .pricetax-card {{
        border-radius: 0.9rem;
        padding: 1.1rem 1.3rem;
        background: linear-gradient(135deg, #1C1C1C 0%, #101010 60%, #060608 100%);
        border: 1px solid #333333;
    }}
    .pricetax-card-erro {{
        border-radius: 0.9rem;
        padding: 1.1rem 1.3rem;
        background: #3b1111;
        border: 1px solid #ff4d4d;
    }}
    .pricetax-badge {{
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        background: {PRIMARY_YELLOW};
        color: {PRIMARY_BLACK};
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .pricetax-metric-label {{
        font-size: 0.78rem;
        color: #BBBBBB;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .pricetax-metric-value {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {PRIMARY_YELLOW};
    }}
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
    .stTextInput > div > div > input {{
        background-color: #111318;
        color: #FFFFFF;
        border-radius: 0.6rem;
        border: 1px solid #333333;
    }}
    .stFileUploader > label div {{
        color: #DDDDDD;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# FUNÇÕES UTILITÁRIAS
# --------------------------------------------------
def only_digits(s: str) -> str:
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


# --------------------------------------------------
# BASE TIPI → IBS/CBS
# --------------------------------------------------
@st.cache_data(show_spinner=False)
def load_tipi_base() -> pd.DataFrame:
    """
    Carrega a base TIPI/IBS-CBS da PRICETAX.
    Espera o arquivo 'TIPI_IBS_CBS.xlsx' na raiz do projeto.
    """
    base_path = Path(__file__).parent / "TIPI_IBS_CBS.xlsx"

    if not base_path.exists():
        st.session_state["tipi_base_ok"] = False
        return pd.DataFrame()

    df = pd.read_excel(base_path, dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]

    # --- AJUSTE OS NOMES DAS COLUNAS AQUI, SE PRECISAR ---
    col_ncm = "NCM"
    col_desc = "DESCRICAO" if "DESCRICAO" in df.columns else "DESCRIÇÃO"

    # Tratamento IBS/CBS pode ter variações de nome
    candidato_trat = None
    for nome in [
        "TRATAMENTO_IBS_CBS",
        "TRATAMENTO",
        "TRATAMENTO GERAL",
        "TRATAMENTO_IBS",
    ]:
        if nome in df.columns:
            candidato_trat = nome
            break

    if candidato_trat is None:
        df["TRATAMENTO_IBS_CBS"] = ""
    else:
        df["TRATAMENTO_IBS_CBS"] = df[candidato_trat].fillna("").astype(str)

    # cClassTrib
    if "CCLASSTRIB" not in df.columns:
        df["CCLASSTRIB"] = ""

    # Alíquotas – vindas do gerador de alíquotas
    if "ALIQ_IBS" not in df.columns:
        df["ALIQ_IBS"] = ""
    if "ALIQ_CBS" not in df.columns:
        df["ALIQ_CBS"] = ""

    # NCM normalizado (só dígitos, 8 posições) para facilitar busca
    df[col_ncm] = df[col_ncm].fillna("").astype(str)
    df["NCM_DIG"] = (
        df[col_ncm].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)
    )

    st.session_state["tipi_base_ok"] = True
    st.session_state["tipi_cols"] = {
        "NCM": col_ncm,
        "DESCR": col_desc,
    }
    return df


def buscar_ncm(df: pd.DataFrame, ncm_str: str):
    norm = only_digits(ncm_str)
    if len(norm) != 8 or df.empty:
        return None

    row = df.loc[df["NCM_DIG"] == norm]
    if row.empty:
        return None
    return row.iloc[0]


# --------------------------------------------------
# PARSER SPED PIS/COFINS (BLOCO M) – VERSÃO STREAMLIT
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

COD_CONT_DESC = {
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

NAT_REC_DESC = {
    "401": "Exportação de mercadorias para o exterior",
    "405": "Desperdícios, resíduos ou aparas de plástico, papel, vidro e metais",
    "908": "Vendas de mercadorias destinadas ao consumo",
    "911": "Receitas financeiras, inclusive variação cambial ativa tributável",
    "999": "Código genérico – Operações tributáveis à alíquota zero/isenção/suspensão",
}

NAT_BC_CRED_DESC = {
    "01": "Aquisição de bens para revenda",
    "02": "Aquisição de bens e serviços utilizados como insumo",
    "03": "Energia elétrica e térmica",
    "04": "Aluguéis de prédios",
    "05": "Aluguéis de máquinas e equipamentos",
    "06": "Armazenagem de mercadoria e frete na venda",
    "07": "Arrendamento mercantil",
    "08": "Ativo imobilizado (depreciação)",
    "09": "Edificações e benfeitorias",
    "10": "Devolução de vendas",
    "11": "Ativos intangíveis (amortização)",
    "12": "Encargos de depreciação/amortização no custo",
    "13": "Outras operações geradoras de crédito",
    "18": "Crédito presumido",
    "19": "Fretes na aquisição",
    "20": "Armazenagem, seguros e vigilância na aquisição",
    "21": "Outros créditos vinculados à atividade",
}


def desc_cod_cont(codigo: str) -> str:
    c = (codigo or "").strip()
    return COD_CONT_DESC.get(c, f"(Descrição não cadastrada: {c})")


def desc_nat_rec(codigo: str) -> str:
    c = (codigo or "").strip()
    return NAT_REC_DESC.get(c, f"(Descrição não cadastrada: {c})")


def norm_nat_bc(codigo: str) -> str:
    d = only_digits((codigo or "").strip())
    if not d:
        return (codigo or "").strip()
    return d.zfill(2) if len(d) == 1 else d


def desc_nat_bc(codigo: str) -> str:
    c = norm_nat_bc(codigo)
    return NAT_BC_CRED_DESC.get(c, f"(Descrição não cadastrada: {c})") if c else ""


def parse_sped_conteudo(nome_arquivo: str, conteudo: str):
    empresa_cnpj = ""
    dt_ini = ""
    dt_fin = ""
    competencia = ""

    ap_pis = []
    credito_pis = []
    receitas_pis = []
    rec_isentas_pis = []
    ap_cofins = []
    credito_cofins = []
    receitas_cofins = []
    rec_isentas_cofins = []

    for raw in conteudo.splitlines():
        if not raw or raw == "|":
            continue
        campos = raw.rstrip("\n").split("|")
        if len(campos) < 3:
            continue
        reg = (campos[1] or "").upper()

        if reg == "0000":
            datas = [c for c in campos if re.fullmatch(r"\d{8}", c or "")]
            if len(datas) >= 2:
                dt_ini, dt_fin = datas[0], datas[1]
            else:
                dt_ini = campos[4] if len(campos) > 4 else ""
                dt_fin = campos[5] if len(campos) > 5 else ""
            competencia = competencia_from_dt(dt_ini, dt_fin)
            cand = [only_digits(c) for c in campos if len(only_digits(c)) == 14]
            if cand:
                empresa_cnpj = cand[0]

        elif reg == "M200":
            row = {"ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj}
            vals = campos[2 : 2 + len(M200_HEADERS)]
            for titulo, val in zip(M200_HEADERS, vals):
                row[titulo] = to_float_br(val)
            ap_pis.append(row)

        elif reg == "M105":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            credito_pis.append(
                {
                    "ARQUIVO": nome_arquivo,
                    "COMPETENCIA": competencia,
                    "CNPJ_ARQUIVO": empresa_cnpj,
                    "NAT_BC_CRED": nat,
                    "NAT_BC_CRED_DESC": desc_nat_bc(nat),
                    "CST_PIS": (campos[3] if len(campos) > 3 else "").strip(),
                    "VL_BC": to_float_br(campos[4] if len(campos) > 4 else 0),
                    "ALIQ": to_float_br(campos[5] if len(campos) > 5 else 0),
                    "VL_CRED": to_float_br(campos[6] if len(campos) > 6 else 0),
                }
            )

        elif reg == "M210":
            cod = (campos[2] if len(campos) > 2 else "").strip()
            receitas_pis.append(
                {
                    "ARQUIVO": nome_arquivo,
                    "COMPETENCIA": competencia,
                    "CNPJ_ARQUIVO": empresa_cnpj,
                    "COD_CONT": cod,
                    "DESCR_COD_CONT": desc_cod_cont(cod),
                    "VL_REC_BRT": to_float_br(campos[3] if len(campos) > 3 else 0),
                    "VL_BC_CONT": to_float_br(campos[4] if len(campos) > 4 else 0),
                    "VL_BC_PIS": to_float_br(campos[7] if len(campos) > 7 else 0),
                    "ALIQ_PIS": to_float_br(campos[8] if len(campos) > 8 else 0),
                    "VL_CONT_APUR": to_float_br(campos[11] if len(campos) > 11 else 0),
                    "VL_CONT_PER": to_float_br(campos[16] if len(campos) > 16 else 0),
                }
            )

        elif reg == "M410":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            rec_isentas_pis.append(
                {
                    "ARQUIVO": nome_arquivo,
                    "COMPETENCIA": competencia,
                    "CNPJ_ARQUIVO": empresa_cnpj,
                    "CODIGO_DET": nat,
                    "DESCR_CODIGO_DET": desc_nat_rec(nat),
                    "VL_REC": to_float_br(campos[3] if len(campos) > 3 else 0),
                }
            )

        elif reg == "M600":
            row = {"ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj}
            vals = campos[2 : 2 + len(M600_HEADERS)]
            for titulo, val in zip(M600_HEADERS, vals):
                row[titulo] = to_float_br(val)
            ap_cofins.append(row)

        elif reg == "M505":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            credito_cofins.append(
                {
                    "ARQUIVO": nome_arquivo,
                    "COMPETENCIA": competencia,
                    "CNPJ_ARQUIVO": empresa_cnpj,
                    "NAT_BC_CRED": nat,
                    "NAT_BC_CRED_DESC": desc_nat_bc(nat),
                    "CST_COFINS": (campos[3] if len(campos) > 3 else "").strip(),
                    "VL_BC": to_float_br(campos[4] if len(campos) > 4 else 0),
                    "ALIQ": to_float_br(campos[5] if len(campos) > 5 else 0),
                    "VL_CRED": to_float_br(campos[6] if len(campos) > 6 else 0),
                }
            )

        elif reg == "M610":
            cod = (campos[2] if len(campos) > 2 else "").strip()
            receitas_cofins.append(
                {
                    "ARQUIVO": nome_arquivo,
                    "COMPETENCIA": competencia,
                    "CNPJ_ARQUIVO": empresa_cnpj,
                    "COD_CONT": cod,
                    "DESCR_COD_CONT": desc_cod_cont(cod),
                    "VL_REC_BRT": to_float_br(campos[3] if len(campos) > 3 else 0),
                    "VL_BC_CONT": to_float_br(campos[4] if len(campos) > 4 else 0),
                    "VL_BC_COFINS": to_float_br(campos[7] if len(campos) > 7 else 0),
                    "ALIQ_COFINS": to_float_br(campos[8] if len(campos) > 8 else 0),
                    "VL_CONT_APUR": to_float_br(campos[11] if len(campos) > 11 else 0),
                    "VL_CONT_PER": to_float_br(campos[16] if len(campos) > 16 else 0),
                }
            )

        elif reg == "M810":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            rec_isentas_cofins.append(
                {
                    "ARQUIVO": nome_arquivo,
                    "COMPETENCIA": competencia,
                    "CNPJ_ARQUIVO": empresa_cnpj,
                    "CODIGO_DET": nat,
                    "DESCR_CODIGO_DET": desc_nat_rec(nat),
                    "VL_REC": to_float_br(campos[3] if len(campos) > 3 else 0),
                }
            )

    return {
        "ap_pis": ap_pis,
        "credito_pis": credito_pis,
        "receitas_pis": receitas_pis,
        "rec_isentas_pis": rec_isentas_pis,
        "ap_cofins": ap_cofins,
        "credito_cofins": credito_cofins,
        "receitas_cofins": receitas_cofins,
        "rec_isentas_cofins": rec_isentas_cofins,
    }


def processar_speds_uploaded(files):
    ap_pis_all, cred_pis_all, rec_pis_all, rec_is_pis_all = [], [], [], []
    ap_cof_all, cred_cof_all, rec_cof_all, rec_is_cof_all = [], [], [], []

    for up in files:
        nome = up.name

        if nome.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(up.read()), "r") as z:
                for info in z.infolist():
                    if info.filename.lower().endswith(".txt"):
                        with z.open(info, "r") as ftxt:
                            conteudo = ftxt.read().decode("utf-8", errors="replace")
                            d = parse_sped_conteudo(info.filename, conteudo)
                            ap_pis_all.extend(d["ap_pis"])
                            cred_pis_all.extend(d["credito_pis"])
                            rec_pis_all.extend(d["receitas_pis"])
                            rec_is_pis_all.extend(d["rec_isentas_pis"])
                            ap_cof_all.extend(d["ap_cofins"])
                            cred_cof_all.extend(d["credito_cofins"])
                            rec_cof_all.extend(d["receitas_cofins"])
                            rec_is_cof_all.extend(d["rec_isentas_cofins"])
        else:
            conteudo = up.read().decode("utf-8", errors="replace")
            d = parse_sped_conteudo(nome, conteudo)
            ap_pis_all.extend(d["ap_pis"])
            cred_pis_all.extend(d["credito_pis"])
            rec_pis_all.extend(d["receitas_pis"])
            rec_is_pis_all.extend(d["rec_isentas_pis"])
            ap_cof_all.extend(d["ap_cofins"])
            cred_cof_all.extend(d["credito_cofins"])
            rec_cof_all.extend(d["receitas_cofins"])
            rec_is_cof_all.extend(d["rec_isentas_cofins"])

    df_ap_pis = pd.DataFrame(ap_pis_all)
    df_cred_pis = pd.DataFrame(cred_pis_all)
    df_rec_pis = pd.DataFrame(rec_pis_all)
    df_ri_pis = pd.DataFrame(rec_is_pis_all)
    df_ap_cof = pd.DataFrame(ap_cof_all)
    df_cred_cof = pd.DataFrame(cred_cof_all)
    df_rec_cof = pd.DataFrame(rec_cof_all)
    df_ri_cof = pd.DataFrame(rec_is_cof_all)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as w:
        if not df_ap_pis.empty:
            df_ap_pis.to_excel(w, "AP PIS", index=False)
        if not df_cred_pis.empty:
            df_cred_pis.to_excel(w, "CREDITO PIS", index=False)
        if not df_rec_pis.empty:
            df_rec_pis.to_excel(w, "RECEITAS PIS", index=False)
        if not df_ri_pis.empty:
            df_ri_pis.to_excel(w, "RECEITAS ISENTAS PIS", index=False)

        if not df_ap_cof.empty:
            df_ap_cof.to_excel(w, "AP COFINS", index=False)
        if not df_cred_cof.empty:
            df_cred_cof.to_excel(w, "CREDITO COFINS", index=False)
        if not df_rec_cof.empty:
            df_rec_cof.to_excel(w, "RECEITAS COFINS", index=False)
        if not df_ri_cof.empty:
            df_ri_cof.to_excel(w, "RECEITAS ISENTAS COFINS", index=False)

    output.seek(0)
    return output


# --------------------------------------------------
# CABEÇALHO
# --------------------------------------------------
st.markdown(
    """
    <div class="pricetax-title">PRICETAX • Classificador IBS/CBS & SPED PIS/COFINS</div>
    <div class="pricetax-subtitle">
        Classificação de bens para IBS/CBS baseada em TIPI + cClassTrib, e análise do SPED Contribuições (Bloco M – PIS/COFINS).
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")
tabs = st.tabs(["🔍 Consulta TIPI → Tratamento IBS/CBS", "📁 SPED PIS/COFINS → Excel"])


# --------------------------------------------------
# ABA 1 – CONSULTA TIPI → IBS/CBS
# --------------------------------------------------
with tabs[0]:
    df_tipi = load_tipi_base()

    st.markdown(
        f"""
        <div class="pricetax-card">
            <span class="pricetax-badge">Módulo PRICETAX</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Informe um NCM e veja, na prática, o tratamento sugerido de IBS/CBS:
                descrição TIPI, cClassTrib e alíquotas de IBS/CBS (quando preenchidas na base).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    if df_tipi.empty or not st.session_state.get("tipi_base_ok", False):
        st.markdown(
            """
            <div class="pricetax-card-erro">
                <b>Base TIPI/IBS-CBS não carregada.</b><br>
                Garanta que o arquivo <code>TIPI_IBS_CBS.xlsx</code> está na raiz do projeto (mesmo nível do <code>app.py</code>).
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            ncm_input = st.text_input(
                "Informe o NCM (com ou sem pontos)",
                placeholder="Ex.: 8471.90.14 ou 84719014",
            )
        with col2:
            st.write("")  # alinhamento
            consultar = st.button("Consultar NCM", type="primary")

        if consultar and ncm_input.strip():
            row = buscar_ncm(df_tipi, ncm_input)
            if row is None:
                st.markdown(
                    f"""
                    <div class="pricetax-card-erro">
                        NCM: <b>{ncm_input}</b><br>
                        Não encontramos esse NCM na base <code>TIPI_IBS_CBS.xlsx</code>.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                ncm_fmt = str(row.get("NCM", "")).strip()
                desc = str(row.get("DESCRICAO", row.get("DESCRIÇÃO", ""))).strip()
                trat = str(row.get("TRATAMENTO_IBS_CBS", "")).strip()
                cct = str(row.get("CCLASSTRIB", "")).strip()

                aliq_ibs = str(row.get("ALIQ_IBS", "")).replace(",", ".").strip()
                aliq_cbs = str(row.get("ALIQ_CBS", "")).replace(",", ".").strip()

                try:
                    total_efetivo = ""
                    if aliq_ibs and aliq_cbs:
                        total_val = float(aliq_ibs) + float(aliq_cbs)
                        total_efetivo = f"{total_val:.2f}"
                except Exception:
                    total_efetivo = ""

                st.markdown(
                    f"""
                    <div class="pricetax-card" style="margin-top:0.8rem;">
                        <div style="font-size:1.05rem;font-weight:600;color:{PRIMARY_YELLOW};">
                            NCM {ncm_fmt} – {desc}
                        </div>
                        <div style="margin-top:0.4rem;font-size:0.9rem;color:#E0E0E0;">
                            <b>Tratamento IBS/CBS sugerido:</b><br>
                            {trat if trat else "Não informado na base."}
                        </div>
                        <div style="margin-top:0.7rem;display:flex;flex-wrap:wrap;gap:1.6rem;">
                            <div>
                                <div class="pricetax-metric-label">cClassTrib sugerido</div>
                                <div class="pricetax-metric-value">{cct if cct else "—"}</div>
                            </div>
                            <div>
                                <div class="pricetax-metric-label">Alíquota IBS (%)</div>
                                <div class="pricetax-metric-value">{aliq_ibs if aliq_ibs else "—"}</div>
                            </div>
                            <div>
                                <div class="pricetax-metric-label">Alíquota CBS (%)</div>
                                <div class="pricetax-metric-value">{aliq_cbs if aliq_cbs else "—"}</div>
                            </div>
                            <div>
                                <div class="pricetax-metric-label">Total IBS + CBS (%)</div>
                                <div class="pricetax-metric-value">{total_efetivo if total_efetivo else "—"}</div>
                            </div>
                        </div>
                        <div style="margin-top:0.8rem;font-size:0.85rem;color:#B0B0B0;border-top:1px dashed #333;padding-top:0.5rem;">
                            Para operações regulares, esse NCM tende a seguir a
                            <b>tributação padrão com crédito integral</b>, desde que não haja regra específica
                            de redução, isenção ou hipótese de Imposto Seletivo aplicável ao cClassTrib definido.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# --------------------------------------------------
# ABA 2 – SPED PIS/COFINS → EXCEL
# --------------------------------------------------
with tabs[1]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Bloco M – PIS/COFINS</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Faça o upload de um ou mais arquivos SPED Contribuições (<code>.txt</code> ou <code>.zip</code>).
                O módulo consolida os registros do Bloco M (M200, M600, M105, M505, M210, M610, M410, M810)
                e gera um Excel com abas analíticas.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    uploaded = st.file_uploader(
        "Selecione arquivos SPED Contribuições (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
    )

    if uploaded:
        if st.button("Processar SPED PIS/COFINS → Excel"):
            with st.spinner("Processando arquivos SPED e montando planilha de auditoria..."):
                output_xlsx = processar_speds_uploaded(uploaded)

            st.success("Processamento concluído. Faça o download da planilha abaixo.")
            st.download_button(
                "Baixar Excel do Bloco M",
                data=output_xlsx,
                file_name="Auditoria_SPED_PIS_COFINS_BlocoM.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.info("Nenhum arquivo selecionado ainda. Anexe um ou mais SPEDs para habilitar o processamento.")
