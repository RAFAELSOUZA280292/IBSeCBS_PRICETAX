# --------------------------------------------------
# app.py — PRICETAX IBS/CBS + SPED Saídas 2026
# --------------------------------------------------
import io
import re
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st


# --------------------------------------------------
# TEMA VISUAL PRICETAX
# --------------------------------------------------
st.set_page_config(
    page_title="PRICETAX • IBS/CBS 2026 & Ranking SPED",
    page_icon="💡",
    layout="wide",
)

PRIMARY_YELLOW = "#FFC300"
PRIMARY_BLACK = "#050608"
PRIMARY_CYAN = "#0EB8B3"
CARD_BG = "#101015"

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

    .pricetax-metric-label {{
        font-size: 0.78rem;
        color: #BBBBBB;
        text-transform: uppercase;
        letter-spacing: 0.05em;
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
    except:
        return 0.0


def normalize_cols_upper(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def pct_str(v: float) -> str:
    return f"{v:.2f}".replace(".", ",") + "%"
# --------------------------------------------------
# BASE PRICETAX – TABELA DE CLASSIFICAÇÃO IBS/CBS 2026
# --------------------------------------------------
TIPI_DEFAULT_NAME = "PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx"

@st.cache_data(show_spinner=False)
def load_tipi_base() -> pd.DataFrame:
    try:
        candidatos = [
            Path(TIPI_DEFAULT_NAME),
            Path.cwd() / TIPI_DEFAULT_NAME,
        ]
        try:
            candidatos.append(Path(__file__).parent / TIPI_DEFAULT_NAME)
        except:
            pass

        base_path = None
        for c in candidatos:
            if c.exists():
                base_path = c
                break
        if base_path is None:
            return pd.DataFrame()

        df = pd.read_excel(base_path)
    except:
        return pd.DataFrame()

    df = normalize_cols_upper(df)

    required_cols = [
        "NCM", "NCM_DESCRICAO",
        "REGIME_IVA_2026_FINAL",
        "FONTE_LEGAL_FINAL",
        "FLAG_ALIMENTO", "FLAG_CESTA_BASICA",
        "FLAG_HORTIFRUTI_OVOS", "FLAG_RED_60",
        "FLAG_DEPENDE_DESTINACAO",
        "IBS_UF_TESTE_2026_FINAL", "IBS_MUN_TESTE_2026_FINAL",
        "CBS_TESTE_2026_FINAL",
    ]
    for c in required_cols:
        if c not in df.columns:
            df[c] = ""

    df["NCM"] = df["NCM"].astype(str).fillna("")
    df["NCM_DIG"] = df["NCM"].str.replace(r"\D", "", regex=True).str.zfill(8)

    return df


def buscar_ncm(df: pd.DataFrame, ncm_str: str):
    norm = only_digits(ncm_str)
    if len(norm) != 8:
        return None
    row = df.loc[df["NCM_DIG"] == norm]
    if row.empty:
        return None
    return row.iloc[0]


# --------------------------------------------------
# PARSER SPED — LEITURA DE C100/C170 (SOMENTE SAÍDAS)
# --------------------------------------------------

def parse_sped_saida(nome_arquivo: str, conteudo: str):
    """
    Retorna lista de:
    - notas (C100)
    - itens (C170)
    Somente CFOP de SAÍDA: 5.xxx / 6.xxx
    """
    notas = []
    itens = []

    current_nf = None
    seq_item = 0

    for raw in conteudo.splitlines():
        if not raw or raw == "|":
            continue

        campos = raw.split("|")
        if len(campos) < 3:
            continue

        reg = campos[1].upper()

        # -----------------------------
        # C100 – Nota Fiscal
        # -----------------------------
        if reg == "C100":
            ind_oper = campos[2]  # 0=entrada / 1=saída
            cnpj_emit = campos[9]
            modelo = campos[6]
            serie = campos[7]
            numero = campos[8]
            dt_emissao = campos[9]
            dt_saida = campos[10]
            vl_doc = to_float_br(campos[12])
            cfop = campos[11]

            if ind_oper != "1":
                # ignora entradas
                current_nf = None
                continue

            # saída válida → registrar
            current_nf = {
                "ID_NF": f"{nome_arquivo}_{numero}_{serie}",
                "ARQUIVO": nome_arquivo,
                "CNPJ_EMITENTE": cnpj_emit,
                "MODELO": modelo,
                "SERIE": serie,
                "NUMERO": numero,
                "CFOP": cfop,
                "DT_EMISSAO": dt_emissao,
                "VL_DOC": vl_doc,
            }
            notas.append(current_nf)
            seq_item = 0

        # -----------------------------
        # C170 – Itens
        # -----------------------------
        elif reg == "C170" and current_nf:
            seq_item += 1
            ncm = campos[11]
            descricao = campos[3]
            qtd = to_float_br(campos[5])
            vl_unit = to_float_br(campos[6])
            vl_total = to_float_br(campos[7])

            itens.append({
                "ID_NF": current_nf["ID_NF"],
                "CFOP": current_nf["CFOP"],
                "DT_EMISSAO": current_nf["DT_EMISSAO"],
                "NCM": ncm,
                "DESCRICAO": descricao,
                "QTD": qtd,
                "VL_UNIT": vl_unit,
                "VL_TOTAL_ITEM": vl_total,
            })

    return notas, itens
# --------------------------------------------------
# FUNÇÃO PRINCIPAL → Processa os arquivos SPED e gera:
# 1) Itens detalhados (C170 + IVA 2026)
# 2) Ranking por produto
# 3) Lista de erros (NCM não encontrado)
# --------------------------------------------------

def processar_speds_vendas(arquivos, df_tipi):
    lista_itens = []
    lista_erros = []

    # --------------------------------------------------
    # 1) LER ARQUIVOS .TXT OU .ZIP
    # --------------------------------------------------
    for up in arquivos:
        nome = up.name

        # -------- ZIP -----------
        if nome.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(up.read()), "r") as z:
                for info in z.infolist():
                    if info.filename.lower().endswith(".txt"):
                        conteudo = z.open(info, "r").read().decode("utf-8", errors="replace")
                        _, itens = parse_sped_saida(info.filename, conteudo)
                        lista_itens.extend(itens)

        # -------- TXT -----------
        else:
            conteudo = up.read().decode("utf-8", errors="replace")
            _, itens = parse_sped_saida(nome, conteudo)
            lista_itens.extend(itens)

    # Se não houver itens de saída
    if not lista_itens:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_itens = pd.DataFrame(lista_itens)

    # --------------------------------------------------
    # 2) NORMALIZA O NCM
    # --------------------------------------------------
    df_itens["NCM_DIG"] = (
        df_itens["NCM"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(8)
    )

    # --------------------------------------------------
    # 3) CRUZAR COM A BASE PRICETAX – IVA 2026
    # --------------------------------------------------
    df_merged = df_itens.merge(
        df_tipi,
        how="left",
        left_on="NCM_DIG",
        right_on="NCM_DIG"
    )

    # Itens não encontrados
    df_erros = df_merged[df_merged["NCM_DESCRICAO"].isna()][[
        "NCM_DIG", "DESCRICAO", "CFOP", "VL_TOTAL_ITEM"
    ]].copy()

    # Remover colunas nulas para itens válidos
    df_validos = df_merged[df_merged["NCM_DESCRICAO"].notna()].copy()

    # --------------------------------------------------
    # 4) CÁLCULO CONSOLIDADO / RANKING
    # --------------------------------------------------
    df_ranking = (
        df_validos.groupby(
            ["NCM_DIG", "NCM_DESCRICAO", "CFOP",
             "REGIME_IVA_2026_FINAL",
             "FLAG_CESTA_BASICA", "FLAG_HORTIFRUTI_OVOS", "FLAG_RED_60"]
        )
        .agg(
            FATURAMENTO_TOTAL=("VL_TOTAL_ITEM", "sum"),
            QTD_TOTAL=("QTD", "sum"),
            NOTAS_QTD=("ID_NF", "nunique"),
        )
        .reset_index()
        .sort_values("FATURAMENTO_TOTAL", ascending=False)
    )

    # --------------------------------------------------
    # 5) ORDENAR E RETORNAR
    # --------------------------------------------------
    df_validos = df_validos.sort_values(["DT_EMISSAO", "ID_NF"])
    df_ranking = df_ranking.sort_values("FATURAMENTO_TOTAL", ascending=False)

    return df_validos, df_ranking, df_erros
# --------------------------------------------------
# CABEÇALHO DO APP
# --------------------------------------------------
st.markdown(
    """
    <div class="pricetax-title">PRICETAX • IBS/CBS 2026 & Ranking SPED</div>
    <div class="pricetax-subtitle">
        Consultas inteligentes para a Reforma Tributária 2026.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# --------------------------------------------------
# TABS DO SISTEMA
# --------------------------------------------------
tabs = st.tabs([
    "🔍 Consulta NCM → IBS/CBS 2026",
    "📁 SPED Saídas → Ranking 2026",
])


# ==================================================
# 🔍 TAB 1 — CONSULTA NCM
# ==================================================
with tabs[0]:

    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Consulta de Produtos</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Encontre o tratamento tributário IBS/CBS para 2026 baseado no NCM.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_tipi = load_tipi_base()

    colA, colB = st.columns([3, 1])
    with colA:
        ncm_input = st.text_input("Informe o NCM", placeholder="Ex.: 16023220 ou 16.02.32.20")
    with colB:
        st.write("")
        consultar = st.button("Consultar", type="primary")

    if consultar and ncm_input.strip():

        row = buscar_ncm(df_tipi, ncm_input)

        if row is None:
            st.error(f"NCM {ncm_input} não encontrado na base PRICETAX.")
        else:
            # Dados
            ncm_fmt = row["NCM_DIG"]
            desc = row["NCM_DESCRICAO"]

            regime = row["REGIME_IVA_2026_FINAL"]
            fonte = row["FONTE_LEGAL_FINAL"]

            cesta = row["FLAG_CESTA_BASICA"]
            hf = row["FLAG_HORTIFRUTI_OVOS"]
            red60 = row["FLAG_RED_60"]

            ibs_uf = to_float_br(row["IBS_UF_TESTE_2026_FINAL"])
            ibs_mun = to_float_br(row["IBS_MUN_TESTE_2026_FINAL"])
            cbs = to_float_br(row["CBS_TESTE_2026_FINAL"])

            total_iva = ibs_uf + ibs_mun + cbs

            badge = lambda x: "🔵 SIM" if str(x).upper() == "SIM" else "🔴 NÃO"

            # CARD PRINCIPAL
            st.markdown(
                f"""
                <div class="pricetax-card" style="margin-top:1rem;">
                    <div style="font-size:1.1rem;font-weight:600;color:{PRIMARY_YELLOW};">
                        NCM {ncm_fmt} – {desc}
                    </div>

                    <div style="margin-top:0.5rem;">
                        <span class="pill pill-regime">{regime}</span>
                        &nbsp; <span class="pill pill-tag">Cesta Básica: {badge(cesta)}</span>
                        &nbsp; <span class="pill pill-tag">Hortifrúti/Ovos: {badge(hf)}</span>
                        &nbsp; <span class="pill pill-tag">Redução 60%: {badge(red60)}</span>
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
                        <div style="font-size:2.4rem;color:{PRIMARY_YELLOW};">
                            {pct_str(ibs_uf + ibs_mun)}
                        </div>
                    </div>

                    <div>
                        <div class="pricetax-metric-label">CBS 2026</div>
                        <div style="font-size:2.4rem;color:{PRIMARY_YELLOW};">
                            {pct_str(cbs)}
                        </div>
                    </div>

                    <div>
                        <div class="pricetax-metric-label">TOTAL IVA 2026</div>
                        <div style="font-size:2.4rem;color:{PRIMARY_YELLOW};">
                            {pct_str(total_iva)}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("### Base legal", divider="gray")
            st.write(f"**{fonte}**")


# ==================================================
# 📁 TAB 2 — SPED → RANKING 2026
# ==================================================
with tabs[1]:

    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Análise de Saídas</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Leia os SPEDs (C100/C170), gere ranking por CFOP+NCM+Descrição e cruze automaticamente com o IVA 2026 PRICETAX.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Envie arquivos SPED (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True,
        key="sped_upload_rank",
    )

    if uploaded:
        if st.button("Processar SPED → Ranking 2026", type="primary"):

            with st.spinner("Lendo SPED, extraindo notas e cruzando com tributação 2026..."):
                df_itens, df_ranking, df_erros = processar_speds_vendas(uploaded, df_tipi)

            if df_itens.empty:
                st.error("Nenhuma nota de saída encontrada (C100/C170).")
            else:
                st.success("Processamento concluído!")
                st.markdown("---")

                # DOWNLOADS
                def to_excel(df):
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        df.to_excel(w, index=False)
                    buf.seek(0)
                    return buf

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "📥 Itens detalhados",
                        data=to_excel(df_itens),
                        file_name="PRICETAX_Itens_Detalhados_2026.xlsx"
                    )
                with col2:
                    st.download_button(
                        "📥 Ranking produtos",
                        data=to_excel(df_ranking),
                        file_name="PRICETAX_Ranking_Produtos_2026.xlsx"
                    )
                with col3:
                    st.download_button(
                        "📥 Erros de NCM",
                        data=to_excel(df_erros),
                        file_name="PRICETAX_Erros_NCM.xlsx"
                    )

                st.markdown("---")

                # TABELA RANKING
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

                # INSIGHT CARD
                total_fat = df_itens["VL_TOTAL_ITEM"].sum()
                total_notas = df_itens["ID_NF"].nunique()

                st.markdown(
                    f"""
                    <div class="pricetax-card-soft" style="margin-top:1rem;">
                        <div style="font-size:1rem;color:{PRIMARY_YELLOW};font-weight:600;">📊 Insight PRICETAX</div>
                        <div style="margin-top:0.4rem;font-size:0.9rem;color:#E0E0E0;">
                            • Faturamento total analisado: <b>R$ {total_fat:,.2f}</b><br>
                            • Total de notas fiscais na análise: <b>{total_notas}</b><br>
                            • Ranking baseado em CFOP + NCM + Descrição<br>
                            • Tratamento tributário 2026 aplicado automaticamente
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Envie arquivos SPED para iniciar a análise.")
