import io
import re
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st

"""
PRICETAX application for IBS/CBS 2026 and SPED ranking.

This Streamlit app provides two main features:
1. Consultation of IBS/CBS treatment for a given NCM based on the PRICETAX refined TIPI table.
2. Extraction and ranking of sales items from SPED Contribuições files (C100/C170 records) and automatic
   cross‑mapping to the TIPI table to simulate the IBS/CBS treatment in 2026.

The app uses the refined TIPI table (PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx) located in the current working
directory or the same directory as the script. If the file is missing, the app will not be able to perform
consultations or ranking and will display an error message accordingly.
"""

# ------------------------------------------------------------------------------
# Theme configuration for PRICETAX
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="PRICETAX • IBS/CBS 2026 & Ranking SPED",
    page_icon="💡",
    layout="wide",
)

# Colour palette
PRIMARY_YELLOW = "#FFC300"
PRIMARY_BLACK = "#050608"
PRIMARY_CYAN = "#0EB8B3"

# Inject custom CSS for branding and layout
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


# ------------------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------------------
def only_digits(s: Optional[str]) -> str:
    """Remove all non-digit characters from a string."""
    return re.sub(r"\D+", "", s or "")


def to_float_br(s) -> float:
    """
    Convert a Brazilian formatted string to float.
    Handles numbers like "1.234,56" or "1234,56".
    Returns 0.0 for invalid inputs.
    """
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    # Case where thousands separator and decimal are present
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def normalize_cols_upper(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to uppercase and strip whitespace."""
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def pct_str(v: float) -> str:
    """Format a float as a percentage string with two decimals."""
    return f"{v:.2f}".replace(".", ",") + "%"


# ------------------------------------------------------------------------------
# Load PRICETAX refined TIPI table
# ------------------------------------------------------------------------------
TIPI_DEFAULT_NAME = "PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx"


@st.cache_data(show_spinner=False)
def load_tipi_base() -> pd.DataFrame:
    """
    Load the refined TIPI base (PRICETAX).

    The function searches for the Excel file in common locations:
    - Current working directory
    - Path relative to this script (if available)
    - Fallback to an empty DataFrame if not found
    """
    paths = [
        Path(TIPI_DEFAULT_NAME),
        Path.cwd() / TIPI_DEFAULT_NAME,
    ]
    try:
        paths.append(Path(__file__).parent / TIPI_DEFAULT_NAME)  # type: ignore
    except Exception:
        pass

    df = None
    for p in paths:
        if p.exists():
            try:
                df = pd.read_excel(p)
            except Exception:
                df = None
            break

    if df is None:
        return pd.DataFrame()

    # Normalize and ensure required columns
    df = normalize_cols_upper(df)
    required_cols = [
        "NCM", "NCM_DESCRICAO",
        "REGIME_IVA_2026_FINAL", "FONTE_LEGAL_FINAL",
        "FLAG_ALIMENTO", "FLAG_CESTA_BASICA",
        "FLAG_HORTIFRUTI_OVOS", "FLAG_RED_60",
        "FLAG_DEPENDE_DESTINACAO",
        "IBS_UF_TESTE_2026_FINAL", "IBS_MUN_TESTE_2026_FINAL",
        "CBS_TESTE_2026_FINAL",
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    # Create normalized NCM column for merging
    df["NCM"] = df["NCM"].astype(str).fillna("")
    df["NCM_DIG"] = df["NCM"].str.replace(r"\D", "", regex=True).str.zfill(8)

    return df


def buscar_ncm(df: pd.DataFrame, ncm_str: str):
    """Lookup a NCM row in the TIPI DataFrame by normalized NCM string."""
    norm = only_digits(ncm_str)
    if len(norm) != 8 or df.empty:
        return None
    row = df.loc[df["NCM_DIG"] == norm]
    return None if row.empty else row.iloc[0]


# ------------------------------------------------------------------------------
# Parser functions for SPED (C100/C170)
# ------------------------------------------------------------------------------
def parse_sped_saida(nome_arquivo: str, conteudo: str):
    """
    Parse SPED Contribuições file content, extracting only notes of exit (C100 IND_OPER=1)
    and their item details (C170).

    Returns lists of note dictionaries and item dictionaries.
    """
    notas = []
    itens = []
    current_nf = None

    for raw in conteudo.splitlines():
        if not raw or raw == "|":
            continue
        campos = raw.split("|")
        if len(campos) < 3:
            continue
        reg = (campos[1] or "").upper()

        # Nota fiscal header
        if reg == "C100":
            # Operação: 0=entrada, 1=saída
            ind_oper = campos[2] if len(campos) > 2 else ""
            if ind_oper != "1":
                current_nf = None
                continue

            # Extract core fields
            cod_mod = campos[6] if len(campos) > 6 else ""
            serie = campos[7] if len(campos) > 7 else ""
            numero = campos[8] if len(campos) > 8 else ""
            dt_doc = campos[9] if len(campos) > 9 else ""
            vl_doc = to_float_br(campos[12] if len(campos) > 12 else 0)
            cfop = campos[11] if len(campos) > 11 else ""
            cnpj_emit = campos[3] if len(campos) > 3 else ""

            # Create unique ID for the note
            current_nf = {
                "ID_NF": f"{nome_arquivo}_{cod_mod}_{serie}_{numero}",
                "ARQUIVO": nome_arquivo,
                "CNPJ_EMITENTE": cnpj_emit,
                "COD_MOD": cod_mod,
                "SERIE": serie,
                "NUMERO": numero,
                "CFOP": cfop,
                "DT_EMISSAO": dt_doc,
                "VL_DOC": vl_doc,
            }
            notas.append(current_nf)
        elif reg == "C170" and current_nf:
            # Item line: index per note not used, but we capture essential fields
            ncm = campos[11] if len(campos) > 11 else ""
            descr = campos[3] if len(campos) > 3 else ""
            qtd = campos[5] if len(campos) > 5 else ""
            vl_unit = campos[6] if len(campos) > 6 else ""
            vl_item = campos[7] if len(campos) > 7 else ""

            itens.append({
                "ID_NF": current_nf["ID_NF"],
                "CFOP": current_nf["CFOP"],
                "DT_EMISSAO": current_nf["DT_EMISSAO"],
                "NCM": ncm,
                "DESCRICAO": descr,
                "QTD": to_float_br(qtd),
                "VL_UNIT": to_float_br(vl_unit),
                "VL_TOTAL_ITEM": to_float_br(vl_item),
            })

    return notas, itens


def processar_speds_vendas(arquivos, df_tipi):
    """
    Process multiple SPED Contribuições files (.txt or .zip) to extract sales notes (C100) and items (C170),
    then merge with the PRICETAX TIPI table to produce:
      - df_itens: detailed item list with IBS/CBS 2026 fields
      - df_ranking: aggregated ranking by NCM + CFOP + treatment
      - df_erros: items not found in TIPI table
    """
    lista_itens = []

    # Iterate over files
    for up in arquivos:
        nome = up.name
        # ZIP handling
        if nome.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(up.read()), "r") as z:
                for info in z.infolist():
                    if info.filename.lower().endswith(".txt"):
                        conteudo = z.open(info, "r").read().decode("utf-8", errors="replace")
                        _, itens = parse_sped_saida(info.filename, conteudo)
                        lista_itens.extend(itens)
        else:
            # TXT file
            conteudo = up.read().decode("utf-8", errors="replace")
            _, itens = parse_sped_saida(nome, conteudo)
            lista_itens.extend(itens)

    # If no items collected
    if not lista_itens:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_itens = pd.DataFrame(lista_itens)

    # Normalize NCM and join
    df_itens["NCM_DIG"] = (
        df_itens["NCM"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(8)
    )

    # Merge with TIPI table to enrich with tax info
    df_merged = df_itens.merge(
        df_tipi,
        how="left",
        left_on="NCM_DIG",
        right_on="NCM_DIG"
    )

    # Identify errors (NCM not found)
    df_erros = df_merged[df_merged["NCM_DESCRICAO"].isna()][
        ["NCM_DIG", "DESCRICAO", "CFOP", "VL_TOTAL_ITEM"]
    ].copy()

    # Filter valid items
    df_validos = df_merged[df_merged["NCM_DESCRICAO"].notna()].copy()

    # Ranking by group
    df_ranking = (
        df_validos.groupby([
            "NCM_DIG", "NCM_DESCRICAO", "CFOP",
            "REGIME_IVA_2026_FINAL",
            "FLAG_CESTA_BASICA",
            "FLAG_HORTIFRUTI_OVOS",
            "FLAG_RED_60"
        ])
        .agg(
            FATURAMENTO_TOTAL=("VL_TOTAL_ITEM", "sum"),
            QTD_TOTAL=("QTD", "sum"),
            NOTAS_QTD=("ID_NF", "nunique"),
        )
        .reset_index()
        .sort_values("FATURAMENTO_TOTAL", ascending=False)
    )

    # Return in ascending date order for items
    df_validos = df_validos.sort_values(["DT_EMISSAO", "ID_NF"])

    return df_validos, df_ranking, df_erros


# ------------------------------------------------------------------------------
# Start of Streamlit interface
# ------------------------------------------------------------------------------
st.markdown(
    """
    <div class="pricetax-title">PRICETAX • IBS/CBS 2026 & Ranking SPED</div>
    <div class="pricetax-subtitle">
        Consultas inteligentes e ranking de produtos sob a ótica do IVA dual.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

tabs = st.tabs([
    "🔍 Consulta NCM → IBS/CBS 2026",
    "📁 SPED Saídas → Ranking 2026",
])


# ==================================================
# TAB 1 — CONSULTA NCM
# ==================================================
with tabs[0]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Consulta de Produtos</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Encontre o tratamento tributário IBS/CBS para o ano de teste 2026 baseado no NCM.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load TIPI once
    df_tipi = load_tipi_base()

    colA, colB = st.columns([3, 1])
    with colA:
        ncm_input = st.text_input(
            "Informe o NCM",
            placeholder="Ex.: 16023220 ou 16.02.32.20",
        )
    with colB:
        st.write("")
        consultar = st.button("Consultar NCM", type="primary")

    if consultar and ncm_input.strip():
        if df_tipi.empty:
            st.error(
                "Base PRICETAX não localizada. Verifique o arquivo 'PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx'."
            )
        else:
            row = buscar_ncm(df_tipi, ncm_input)
            if row is None:
                st.error(f"NCM {ncm_input} não encontrado na base PRICETAX.")
            else:
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

                def badge(v):
                    return "🔵 SIM" if str(v).upper() == "SIM" else "🔴 NÃO"

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

                # Metrics display
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
# TAB 2 — SPED Saídas → Ranking 2026
# ==================================================
with tabs[1]:
    st.markdown(
        """
        <div class="pricetax-card">
            <span class="pricetax-badge">Análise de Saídas</span>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:#DDDDDD;">
                Faça upload de SPED Contribuições (.txt ou .zip) para extrair itens de notas de saída (C100/C170), gerar um ranking de produtos
                por CFOP/NCM/Descrição e cruzar automaticamente com o IVA 2026 PRICETAX.
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

                # Helper to convert DataFrame to Excel bytes
                def to_excel(df):
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False)
                    buffer.seek(0)
                    return buffer

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "📥 Itens detalhados",
                        data=to_excel(df_itens),
                        file_name="PRICETAX_Itens_Detalhados_2026.xlsx",
                    )
                with col2:
                    st.download_button(
                        "📥 Ranking produtos",
                        data=to_excel(df_ranking),
                        file_name="PRICETAX_Ranking_Produtos_2026.xlsx",
                    )
                with col3:
                    st.download_button(
                        "📥 Erros de NCM",
                        data=to_excel(df_erros),
                        file_name="PRICETAX_Erros_NCM.xlsx",
                    )

                st.markdown("---")

                # Display top ranking
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

                # Insight summary
                total_fat = df_itens["VL_TOTAL_ITEM"].sum()
                total_notas = df_itens["ID_NF"].nunique()

                st.markdown(
                    f"""
                    <div class="pricetax-card-soft" style="margin-top:1rem;">
                        <div style="font-size:1rem;color:{PRIMARY_YELLOW};font-weight:600;">📊 Insight PRICETAX</div>
                        <div style="margin-top:0.4rem;font-size:0.9rem;color:#E0E0E0;">
                            • Faturamento total analisado: <b>R$ {total_fat:,.2f}</b><br>
                            • Total de notas fiscais de saída: <b>{total_notas}</b><br>
                            • Ranking baseado em CFOP + NCM + Descrição<br>
                            • Tratamento tributário 2026 aplicado automaticamente
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("Envie arquivos SPED para iniciar a análise.")
