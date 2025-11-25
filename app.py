import io
import os
import re
import zipfile
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

# ============================================================
#  Utils básicos
# ============================================================

def only_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")

def to_float_br(s) -> float:
    """
    Converte string BR (1.234,56) ou US (1234.56) em float.
    """
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    # caso típico brasileiro 1.234,56
    if s.count(",") == 1 and s.count(".") >= 1:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def competencia_from_dt(dt_ini: str, dt_fin: str) -> str:
    """
    Acha a competência (MM/AAAA) a partir das datas do registro 0000.
    """
    for raw in (dt_ini or "", dt_fin or ""):
        dig = only_digits(raw)
        if len(dig) == 8:
            return f"{dig[2:4]}/{dig[4:8]}"
    return ""

def format_currency_brl(v) -> str:
    """
    160526.76 -> '160.526,76'
    """
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return ""

def normalizar_ncm(s: str) -> str:
    """
    Remove tudo que não é dígito e devolve até 8 dígitos.
    """
    d = only_digits(str(s) if s is not None else "")
    if not d:
        return ""
    if len(d) >= 8:
        return d[:8]
    return d

# ============================================================
#  TIPI – carga opcional + heurística IBS/CBS
# ============================================================

@st.cache_data(show_spinner=False)
def carregar_tipi():
    """
    Tenta ler o arquivo 'tipi_ncm.csv' na mesma pasta do script.

    Estrutura esperada do CSV:
        NCM        -> código NCM (8 dígitos, com ou sem pontuação)
        DESCRICAO  -> descrição TIPI
        CAPITULO   -> número do capítulo (1..97)
        ALIQ_IPI   -> alíquota de IPI (ex: 0, 5, 10, 15)

    Esse arquivo você constrói a partir da TIPI oficial,
    e pode ir completando aos poucos (não precisa estar 100%).
    """
    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / "tipi_ncm.csv"

    if not csv_path.exists():
        return None

    df = pd.read_csv(csv_path, dtype=str, sep=",")
    df = df.rename(columns={c: c.upper().strip() for c in df.columns})

    if "NCM" not in df.columns:
        df["NCM"] = ""

    df["NCM_NORM"] = df["NCM"].astype(str).apply(normalizar_ncm)

    # capítulo
    if "CAPITULO" in df.columns:
        df["CAPITULO"] = pd.to_numeric(df["CAPITULO"], errors="coerce").astype("Int64")
    else:
        df["CAPITULO"] = pd.NA

    # alíquota IPI
    if "ALIQ_IPI" in df.columns:
        df["ALIQ_IPI"] = pd.to_numeric(df["ALIQ_IPI"], errors="coerce")
    else:
        df["ALIQ_IPI"] = pd.NA

    return df

def classificar_essencialidade(chap, ipi):
    """
    Heurística de Essencialidade usando CAPÍTULO TIPI + alíquota IPI.
    NÃO é classificação legal definitiva. É uma régua de priorização.

    Ajuste depois conforme a doutrina PriceTax.
    """
    if chap is None or pd.isna(chap):
        chap = -1
    if ipi is None or pd.isna(ipi):
        ipi = 0.0

    try:
        chap = int(chap)
    except Exception:
        chap = -1

    # Alimentos básicos, agro, etc. – capítulos 1-24
    if 1 <= chap <= 24:
        if ipi == 0:
            return "ALTA"
        return "MÉDIA"

    # Medicamentos e produtos médicos
    if chap in (30, 90):
        if ipi <= 5:
            return "ALTA"
        return "MÉDIA"

    # Bebidas alcoólicas, fumo, produtos muito taxados
    if chap in (22, 24) or ipi >= 10:
        return "BAIXA"

    # Máquinas, equipamentos, veículos – tende a ser investimento/bem de capital
    if chap in (84, 85, 87):
        if ipi == 0:
            return "MÉDIA"
        return "BAIXA"

    # Default
    return "MÉDIA"

def sugerir_perfil_ibs_cbs(essencialidade):
    """
    Traduz ESSENCIALIDADE em um rótulo de perfil IBS/CBS 2026.
    Isso é textual, para orientar classificação, não é parametrização final.
    """
    e = (essencialidade or "").upper()
    if e == "ALTA":
        return "Essencial / Cesta / Redução Potencial (ver anexos IBS/CBS)"
    if e == "BAIXA":
        return "Padrão / Supérfluo / Avaliar IS (Imposto Seletivo)"
    return "Padrão (sem indicativo especial pela TIPI)"

def mapear_tipi_e_ibs_cbs(df_ranking: pd.DataFrame, df_tipi: pd.DataFrame) -> pd.DataFrame:
    """
    Faz o join do ranking (CFOP+NCM+DESCR_ITEM+VL_TOTAL_ITEM+PART)
    com TIPI por NCM. Acrescenta:

      - DESCRICAO_TIPI
      - CAPITULO
      - ALIQ_IPI
      - ESSENCIALIDADE (heurística)
      - PERFIL_IBS_CBS_2026 (texto explicativo)
      - IBS_CBS_STATUS ('A CLASSIFICAR' por padrão)
      - colunas vazias para cClassTrib, Class_Trib_IBS, Class_Trib_CBS, etc.
    """
    if df_ranking is None or df_ranking.empty or df_tipi is None:
        # mesmo sem TIPI, já devolve com colunas “de estrutura”
        df = df_ranking.copy()
        if df is None or df.empty:
            return df

        df["ESSENCIALIDADE"] = ""
        df["PERFIL_IBS_CBS_2026"] = "A CLASSIFICAR (sem TIPI carregada)"
        df["IBS_CBS_STATUS"] = "A CLASSIFICAR"
        df["cClassTrib"] = ""
        df["Class_Trib_IBS"] = ""
        df["Class_Trib_CBS"] = ""
        df["OBS_IBS_CBS_2026"] = "Definir tratamento IBS/CBS com base em matriz interna e legislação vigente."
        return df

    df_rank = df_ranking.copy()
    df_rank["NCM_NORM"] = df_rank["NCM"].astype(str).apply(normalizar_ncm)

    df_merged = df_rank.merge(
        df_tipi[["NCM_NORM", "DESCRICAO", "CAPITULO", "ALIQ_IPI"]],
        on="NCM_NORM",
        how="left",
        suffixes=("", "_TIPI"),
    )

    df_merged["ESSENCIALIDADE"] = df_merged.apply(
        lambda row: classificar_essencialidade(row.get("CAPITULO"), row.get("ALIQ_IPI")),
        axis=1,
    )

    df_merged["PERFIL_IBS_CBS_2026"] = df_merged["ESSENCIALIDADE"].apply(sugerir_perfil_ibs_cbs)

    # Campos estruturais para IBS/CBS 2026 (para matriz PriceTax abastecer)
    df_merged["IBS_CBS_STATUS"] = "A CLASSIFICAR"
    df_merged["cClassTrib"] = ""
    df_merged["Class_Trib_IBS"] = ""
    df_merged["Class_Trib_CBS"] = ""
    df_merged["OBS_IBS_CBS_2026"] = (
        "Sugestão baseada na TIPI e essenc. heurística. "
        "Validar na matriz PriceTax e na legislação do IBS/CBS 2026."
    )

    # Valor em BRL formatado
    df_merged["VL_TOTAL_ITEM_BR"] = df_merged["VL_TOTAL_ITEM"].apply(format_currency_brl)

    return df_merged

# ============================================================
#  Parser EFD PIS/COFINS (0000, 0200, C100, C170)
# ============================================================

def parse_efd_piscofins_text(text: str, origem: str):
    """
    Lê o conteúdo de UM arquivo EFD PIS/COFINS (texto já decodificado)
    e retorna uma lista de itens de SAÍDA (CFOP 5/6/7) com:

      - competência, CNPJ
      - dados da NF (modelo, série, número, data, valor doc)
      - dados do item (CFOP, COD_ITEM, DESCR_ITEM, NCM, VL_ITEM, etc.)
    """
    itens_saida = []

    cod_item_map = {}  # 0200: cod_item -> {"descr_item": ..., "ncm": ...}
    competencia = ""
    cnpj = ""

    current_doc = {
        "IND_OPER": "",
        "IND_EMIT": "",
        "COD_PART": "",
        "COD_MOD": "",
        "COD_SIT": "",
        "SER": "",
        "NUM_DOC": "",
        "DT_DOC": "",
        "VL_DOC": 0.0,
    }

    for raw in text.splitlines():
        if not raw or raw == "|":
            continue
        campos = raw.rstrip("\n").split("|")
        if len(campos) < 2:
            continue

        reg = (campos[1] or "").upper()

        # 0000 – dados da escrituração
        if reg == "0000":
            # tenta detectar datas (8 dígitos) em qualquer posição
            datas = [c for c in campos if re.fullmatch(r"\d{8}", c or "")]
            if len(datas) >= 2:
                dt_ini, dt_fin = datas[0], datas[1]
            else:
                dt_ini = campos[4] if len(campos) > 4 else ""
                dt_fin = campos[5] if len(campos) > 5 else ""
            competencia = competencia_from_dt(dt_ini, dt_fin)

            # captura CNPJ (primeiro campo com 14 dígitos)
            for c in campos:
                d = only_digits(c)
                if len(d) == 14:
                    cnpj = d
                    break

        # 0200 – cadastro de itens
        elif reg == "0200":
            # |0200|COD_ITEM|DESCR_ITEM|COD_BARRA|COD_ANT_ITEM|UNID_INV|
            #        2        3           4         5            6
            # |TIPO_ITEM|COD_NCM|EX_IPI|COD_GEN|COD_LST|ALIQ_ICMS|
            #    7        8      9      10      11       12
            cod_item = (campos[2] if len(campos) > 2 else "").strip()
            descr_item = (campos[3] if len(campos) > 3 else "").strip()
            cod_ncm = (campos[8] if len(campos) > 8 else "").strip()
            if cod_item:
                cod_item_map[cod_item] = {
                    "descr_item": descr_item,
                    "ncm": cod_ncm,
                }

        # C100 – cabeçalho NF
        elif reg == "C100":
            # |C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|CHV_NFE|DT_DOC|DT_E_S|VL_DOC|...
            current_doc = {
                "IND_OPER": (campos[2] if len(campos) > 2 else "").strip(),
                "IND_EMIT": (campos[3] if len(campos) > 3 else "").strip(),
                "COD_PART": (campos[4] if len(campos) > 4 else "").strip(),
                "COD_MOD": (campos[5] if len(campos) > 5 else "").strip(),
                "COD_SIT": (campos[6] if len(campos) > 6 else "").strip(),
                "SER": (campos[7] if len(campos) > 7 else "").strip(),
                "NUM_DOC": (campos[8] if len(campos) > 8 else "").strip(),
                "DT_DOC": (campos[10] if len(campos) > 10 else "").strip(),
                "VL_DOC": to_float_br(campos[12] if len(campos) > 12 else 0),
            }

        # C170 – itens da NF
        elif reg == "C170":
            # |C170|NUM_ITEM|COD_ITEM|DESCR_COMPL|QTD|UNID|VL_ITEM|VL_DESC|IND_MOV|
            #        2        3         4          5    6     7       8       9
            # |CST_ICMS|CFOP|COD_NAT|VL_BC_ICMS|ALIQ_ICMS|VL_ICMS|VL_BC_ICMS_ST|ALIQ_ST|VL_ICMS_ST|
            #    10      11    12        13        14       15        16          17      18
            cod_item = (campos[3] if len(campos) > 3 else "").strip()
            descr_compl = (campos[4] if len(campos) > 4 else "").strip()
            qtd = to_float_br(campos[5] if len(campos) > 5 else 0)
            unid = (campos[6] if len(campos) > 6 else "").strip()
            vl_item = to_float_br(campos[7] if len(campos) > 7 else 0)
            vl_desc = to_float_br(campos[8] if len(campos) > 8 else 0)
            cfop = (campos[11] if len(campos) > 11 else "").strip()

            # queremos apenas saídas (5,6,7)
            if not cfop or cfop[0] not in ("5", "6", "7"):
                continue

            descr_item = ""
            ncm = ""
            if cod_item and cod_item in cod_item_map:
                descr_item = cod_item_map[cod_item]["descr_item"]
                ncm = cod_item_map[cod_item]["ncm"]

            row = {
                "ARQUIVO": origem,
                "COMPETENCIA": competencia,
                "CNPJ": cnpj,
                "IND_OPER": current_doc.get("IND_OPER", ""),
                "COD_MOD": current_doc.get("COD_MOD", ""),
                "SERIE": current_doc.get("SER", ""),
                "NUM_DOC": current_doc.get("NUM_DOC", ""),
                "DT_DOC": current_doc.get("DT_DOC", ""),
                "VL_DOC": current_doc.get("VL_DOC", 0.0),
                "CFOP": cfop,
                "COD_ITEM": cod_item,
                "DESCR_ITEM": descr_item,
                "NCM": ncm,
                "DESCR_COMPL": descr_compl,
                "QTD": qtd,
                "UNID": unid,
                "VL_ITEM": vl_item,
                "VL_DESC": vl_desc,
            }
            itens_saida.append(row)

    return itens_saida

def parse_efd_piscofins_files(file_paths):
    """
    Recebe lista de caminhos (txt/zip),
    devolve um DataFrame com TODOS os itens de saída.
    """
    todos_itens = []

    for path in file_paths:
        p = Path(path)
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p, "r") as z:
                for name in z.namelist():
                    if not name.lower().endswith(".txt"):
                        continue
                    with z.open(name, "r") as f:
                        text = f.read().decode("utf-8", errors="replace")
                    origem = f"{p.name}/{name}"
                    itens = parse_efd_piscofins_text(text, origem)
                    todos_itens.extend(itens)
        elif p.suffix.lower() == ".txt":
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            origem = p.name
            itens = parse_efd_piscofins_text(text, origem)
            todos_itens.extend(itens)

    df = pd.DataFrame(todos_itens)
    return df

def gerar_ranking(df_itens: pd.DataFrame) -> pd.DataFrame:
    """
    Ranking acumulado por:
      COMPETENCIA, CNPJ, CFOP, NCM, DESCR_ITEM

    Soma VL_ITEM e calcula % de participação no total.
    """
    if df_itens is None or df_itens.empty:
        return pd.DataFrame()

    df = df_itens.copy()
    df["VL_ITEM"] = pd.to_numeric(df["VL_ITEM"], errors="coerce").fillna(0.0)

    group_cols = ["COMPETENCIA", "CNPJ", "CFOP", "NCM", "DESCR_ITEM"]
    df_rank = (
        df.groupby(group_cols, as_index=False)["VL_ITEM"]
        .sum()
        .rename(columns={"VL_ITEM": "VL_TOTAL_ITEM"})
        .sort_values("VL_TOTAL_ITEM", ascending=False)
    )

    total = df_rank["VL_TOTAL_ITEM"].sum()
    if total > 0:
        df_rank["PARTICIPACAO_%"] = df_rank["VL_TOTAL_ITEM"] / total * 100
    else:
        df_rank["PARTICIPACAO_%"] = 0.0

    df_rank["VL_TOTAL_ITEM_BR"] = df_rank["VL_TOTAL_ITEM"].apply(format_currency_brl)
    df_rank["PARTICIPACAO_%"] = df_rank["PARTICIPACAO_%"].round(4)

    return df_rank

def gerar_excel_bytes(df_itens: pd.DataFrame, df_ranking: pd.DataFrame, df_ranking_ibs_cbs: pd.DataFrame) -> bytes:
    """
    Gera um Excel em memória com:
      - Itens de Saída (C170)
      - Ranking Produtos
      - Ranking + TIPI/IBS/CBS
      - Receita x Essencialidade
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        if df_itens is not None and not df_itens.empty:
            df_itens.to_excel(writer, sheet_name="Itens Saída (C170)", index=False)
        if df_ranking is not None and not df_ranking.empty:
            df_ranking.to_excel(writer, sheet_name="Ranking Produtos", index=False)
        if df_ranking_ibs_cbs is not None and not df_ranking_ibs_cbs.empty:
            df_ranking_ibs_cbs.to_excel(writer, sheet_name="Ranking IBS_CBS_2026", index=False)

            if "ESSENCIALIDADE" in df_ranking_ibs_cbs.columns:
                df_ess = (
                    df_ranking_ibs_cbs
                    .groupby("ESSENCIALIDADE", as_index=False)["VL_TOTAL_ITEM"]
                    .sum()
                    .sort_values("VL_TOTAL_ITEM", ascending=False)
                )
                df_ess.to_excel(writer, sheet_name="Receita x Essencialidade", index=False)

    buf.seek(0)
    return buf

# ============================================================
#  Streamlit App
# ============================================================

st.set_page_config(
    page_title="IBS/CBS 2026 – Ranking Produtos (EFD PIS/COFINS)",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilo PriceTax-like (verde água + escuro)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #020617;
        color: #e5e7eb;
    }
    h1, h2, h3, h4 {
        color: #0eb8b3;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("## 🧾 IBS/CBS 2026 – Ranking de Produtos a partir da EFD PIS/COFINS")
st.write(
    "Este app lê a **EFD PIS/COFINS**, identifica as **notas de saída** (CFOP 5/6/7), "
    "faz o ranking de **produtos por NCM/CFOP/Descrição** e, em seguida, "
    "estrutura uma visão de **IBS/CBS 2026** com campos prontos para classificação "
    "(cClassTrib, perfil de essencialidade, etc.)."
)

uploaded_files = st.file_uploader(
    "Selecione um ou mais arquivos EFD PIS/COFINS (.txt / .zip)",
    type=["txt", "zip"],
    accept_multiple_files=True,
)

def salvar_uploads_temp(files):
    paths = []
    for f in files:
        suffix = "." + f.name.split(".")[-1] if "." in f.name else ""
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        with open(temp_path, "wb") as out:
            out.write(f.getvalue())
        paths.append(temp_path)
    return paths

df_tipi = carregar_tipi()
if df_tipi is None:
    st.warning(
        "⚠️ Arquivo `tipi_ncm.csv` não encontrado na pasta do app. "
        "O cruzamento com a TIPI e a Essencialidade heurística funcionará "
        "apenas depois que você criar/importar esse CSV."
    )
else:
    st.success("TIPI carregada (tipi_ncm.csv). O ranking será enriquecido com CAPÍTULO/ALIQ_IPI/Essencialidade.")

if uploaded_files:
    if st.button("🚀 Processar EFD PIS/COFINS"):
        try:
            temp_paths = salvar_uploads_temp(uploaded_files)

            with st.spinner("Lendo arquivos e montando ranking de saídas..."):
                df_itens = parse_efd_piscofins_files(temp_paths)
                df_ranking = gerar_ranking(df_itens)
                df_ranking_ibs_cbs = mapear_tipi_e_ibs_cbs(df_ranking, df_tipi)

            for p in temp_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass

            if df_itens is None or df_itens.empty:
                st.warning("Nenhum item de saída (CFOP 5/6/7) foi encontrado nos arquivos enviados.")
            else:
                st.success("Processamento concluído com sucesso ✅")

                tab1, tab2, tab3, tab4 = st.tabs(
                    [
                        "🔍 Itens de Saída (C170)",
                        "🏆 Ranking Produtos (NCM/CFOP/Descrição)",
                        "🧱 Visão IBS/CBS 2026 (Estrutura)",
                        "📜 Regras Estruturais 2026 (Resumo)",
                    ]
                )

                # -----------------------------------------
                # Tab 1 – Itens
                # -----------------------------------------
                with tab1:
                    st.caption("Amostra das primeiras linhas dos itens de saída (C170 + 0200).")
                    st.dataframe(df_itens.head(500), use_container_width=True)

                # -----------------------------------------
                # Tab 2 – Ranking Produtos
                # -----------------------------------------
                with tab2:
                    if df_ranking is None or df_ranking.empty:
                        st.info("Sem dados suficientes para montar o ranking.")
                    else:
                        st.write("### Ranking de Produtos por NCM + CFOP + Descrição")
                        st.caption("Ordenado pelo valor total de saída (VL_TOTAL_ITEM).")
                        cols_show = [
                            "COMPETENCIA",
                            "CNPJ",
                            "CFOP",
                            "NCM",
                            "DESCR_ITEM",
                            "VL_TOTAL_ITEM_BR",
                            "PARTICIPACAO_%",
                        ]
                        cols_show = [c for c in cols_show if c in df_ranking.columns]
                        st.dataframe(df_ranking[cols_show].head(500), use_container_width=True)

                # -----------------------------------------
                # Tab 3 – Visão IBS/CBS 2026
                # -----------------------------------------
                with tab3:
                    if df_ranking_ibs_cbs is None or df_ranking_ibs_cbs.empty:
                        st.info("Sem dados suficientes para montar a visão IBS/CBS 2026.")
                    else:
                        st.write("### Estrutura para IBS/CBS 2026 por NCM/CFOP/Produto")
                        st.caption(
                            "Essas colunas estruturam a visão para 2026. "
                            "Os campos de classificação (cClassTrib, Class_Trib_IBS/CBS) "
                            "devem ser preenchidos pela matriz tributária (PriceTax/LavoraTax)."
                        )
                        cols_show = [
                            "COMPETENCIA",
                            "CNPJ",
                            "CFOP",
                            "NCM",
                            "DESCR_ITEM",
                            "VL_TOTAL_ITEM_BR",
                            "PARTICIPACAO_%",
                            "DESCRICAO",      # descrição TIPI
                            "CAPITULO",
                            "ALIQ_IPI",
                            "ESSENCIALIDADE",
                            "PERFIL_IBS_CBS_2026",
                            "IBS_CBS_STATUS",
                            "cClassTrib",
                            "Class_Trib_IBS",
                            "Class_Trib_CBS",
                            "OBS_IBS_CBS_2026",
                        ]
                        cols_show = [c for c in cols_show if c in df_ranking_ibs_cbs.columns]
                        st.dataframe(df_ranking_ibs_cbs[cols_show].head(500), use_container_width=True)

                        # Resumo por Essencialidade
                        if "ESSENCIALIDADE" in df_ranking_ibs_cbs.columns:
                            st.markdown("---")
                            st.write("### Receita Total por Essencialidade (Heurística TIPI)")
                            df_ess = (
                                df_ranking_ibs_cbs
                                .groupby("ESSENCIALIDADE", as_index=False)["VL_TOTAL_ITEM"]
                                .sum()
                                .sort_values("VL_TOTAL_ITEM", ascending=False)
                            )
                            df_ess["VL_TOTAL_ITEM_BR"] = df_ess["VL_TOTAL_ITEM"].apply(format_currency_brl)
                            st.dataframe(df_ess, use_container_width=True)

                            try:
                                st.bar_chart(data=df_ess.set_index("ESSENCIALIDADE")["VL_TOTAL_ITEM"])
                            except Exception:
                                pass

                # -----------------------------------------
                # Tab 4 – Regras Estruturais 2026
                # -----------------------------------------
                with tab4:
                    st.write("### Principais pontos para 2026 – IBS/CBS (Visão estrutural)")
                    st.markdown(
                        """
                        **1) Ano de teste / alíquotas-teste**  
                        - Haverá um período de transição em que IBS e CBS passam a ser **calculados e informados**,  
                          inicialmente com alíquotas reduzidas (fase de testes), convivendo com o sistema atual.  
                        - Mesmo que o efeito financeiro seja reduzido/informativo, **a obrigação de destacar IBS/CBS no documento fiscal é real**.

                        **2) Obrigatoriedade de destacar IBS/CBS na NF-e**  
                        - Campos novos no XML (NT específica) para identificar:  
                          - IBS (estadual/municipal)  
                          - CBS (federal)  
                          - Situação tributária (códigos próprios)  
                          - Base de cálculo e valores.  
                        - Sem esses campos preenchidos corretamente, a NF tende a ser **rejeitada** a partir do início da obrigatoriedade.

                        **3) cClassTrib e classificação da operação**  
                        - Assim como hoje existe CST/CSOSN, o novo modelo prevê códigos de situação tributária **específicos para IBS/CBS**,  
                          incluindo faixas como:  
                          - Operação tributada integralmente  
                          - Operação com redução de base/alíquota  
                          - Operação com alíquota zero/isenta/suspensa  
                          - Operações não onerosas (demonstração, garantia, bonificação sem preço, consumo interno etc.).  
                        - Essa classificação combina **CFOP + NCM + natureza da operação**, daí a importância do ranking.

                        **4) O que este app entrega para 2026**  
                        - Ranking consolidado por **NCM + CFOP + Descrição** com valor e participação.  
                        - Enriquecimento opcional com **TIPI** (capítulo, IPI) para montar uma régua de **Essencialidade**.  
                        - Estrutura de saída com campos prontos para:  
                          - `cClassTrib`  
                          - `Class_Trib_IBS`  
                          - `Class_Trib_CBS`  
                          - `Essencialidade`  
                          - `Perfil_IBS_CBS_2026` (texto)  
                          - `IBS_CBS_STATUS`  

                        **5) Como encaixar isso na prática (PriceTax / LavoraTax)**  
                        - Este app faz o papel de **motor de leitura do SPED** e geração do **mix de produtos/receitas**.  
                        - Sobre esse ranking, vocês aplicam a **matriz tributária (por NCM/segmento)** para definir:  
                          - Qual a situação IBS/CBS em 2026 (alíquota cheia/reduzida/zero)  
                          - Qual o `cClassTrib` correto (onerosa x não onerosa, regimes especiais)  
                          - Como cada produto entra na parametrização do ERP (IBS/CBS).

                        Em resumo: o Python aqui entrega **o mapa da mina** (receita por NCM/CFOP/Produto) e a
                        **estrutura de IBS/CBS 2026**, e a matriz tributária oficial entra completando os códigos
                        e alíquotas conforme a Reforma Tributária e a governança PriceTax.
                        """
                    )

                # -----------------------------------------
                # Download Excel
                # -----------------------------------------
                st.markdown("---")
                st.markdown("### 📥 Download do Excel completo")

                excel_bytes = gerar_excel_bytes(df_itens, df_ranking, df_ranking_ibs_cbs)
                st.download_button(
                    "⬇️ Baixar Excel (Itens + Ranking + IBS_CBS_2026)",
                    data=excel_bytes,
                    file_name="IBS_CBS_2026_Ranking_PIS_COFINS.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        except Exception as e:
            st.error(f"Erro ao processar arquivos: {e}")
else:
    st.info("Envie pelo menos um arquivo EFD PIS/COFINS (.txt ou .zip) para começar.")
