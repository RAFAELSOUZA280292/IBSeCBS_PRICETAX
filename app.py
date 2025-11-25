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

# ============================================================
#  MATRIZ CBN – treino IBS/CBS 2026 por NCM
# ============================================================

@st.cache_data(show_spinner=False)
def carregar_matriz_cbn():
    """
    Carrega o arquivo de treino da CBN:
        GRADE_Reforma_Tributaria_2026_CBN.xlsx

    Usa a aba 'VENDAS_2026' e gera um mapa por NCM:

      NCM_NORM, GRUPO_MACRO, SUBGRUPO, cClassTrib,
      ESSENCIALIDADE_IBS, ESSENCIALIDADE_CBS,
      CST_IBS_CBS_VENDA,
      ALIQ_IBS_UF_VENDA_2026, ALIQ_IBS_MUN_VENDA_2026,
      ALIQ_CBS_VENDA_2026,
      ALIQ_EFETIVA_IBS_VENDA_2026, ALIQ_EFETIVA_CBS_VENDA_2026

    OBS: é um "treino" – serve como semente para outros clientes.
    """
    base_dir = Path(__file__).resolve().parent
    xlsx_path = base_dir / "GRADE_Reforma_Tributaria_2026_CBN.xlsx"

    if not xlsx_path.exists():
        return None

    try:
        df_vendas = pd.read_excel(xlsx_path, sheet_name="VENDAS_2026")
    except Exception:
        return None

    df_vendas = df_vendas.rename(columns={c: c.strip() for c in df_vendas.columns})

    if "NCM" not in df_vendas.columns:
        return None

    df_vendas["NCM_NORM"] = df_vendas["NCM"].apply(normalizar_ncm)

    # elimina NCM em branco
    df_vendas = df_vendas[df_vendas["NCM_NORM"] != ""]

    cols_exist = df_vendas.columns

    def col(name):
        return name if name in cols_exist else None

    agg_dict = {}
    for c in [
        "GRUPO_MACRO",
        "SUBGRUPO",
        "cClassTrib",
        "ESSENCIALIDADE_IBS",
        "ESSENCIALIDADE_CBS",
        "CST_IBS_CBS_VENDA",
        "ALIQ_IBS_UF_VENDA_2026",
        "ALIQ_IBS_MUN_VENDA_2026",
        "ALIQ_CBS_VENDA_2026",
        "ALIQ_EFETIVA_IBS_VENDA_2026",
        "ALIQ_EFETIVA_CBS_VENDA_2026",
    ]:
        if col(c):
            agg_dict[c] = "first"

    if not agg_dict:
        return None

    df_map = (
        df_vendas.groupby("NCM_NORM", as_index=False)
        .agg(agg_dict)
    )

    return df_map

def enriquecer_com_tipi_e_cbn(df_ranking: pd.DataFrame,
                              df_tipi: pd.DataFrame,
                              df_cbn: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline de enriquecimento:

      1) TIPI (se houver): CAPITULO, ALIQ_IPI, DESCRICAO_TIPI,
         ESSENCIALIDADE (heurística), PERFIL_IBS_CBS_2026.
      2) MATRIZ CBN (se houver): força cClassTrib, essenc. IBS/CBS,
         CST_IBS_CBS, alíquotas 2026 etc. por NCM.

    Onde não houver match com CBN, os campos IBS/CBS ficam "A CLASSIFICAR".
    """
    if df_ranking is None or df_ranking.empty:
        return df_ranking

    df = df_ranking.copy()
    df["NCM_NORM"] = df["NCM"].astype(str).apply(normalizar_ncm)

    # 1) Join com TIPI (opcional)
    if df_tipi is not None and not df_tipi.empty:
        df = df.merge(
            df_tipi[["NCM_NORM", "DESCRICAO", "CAPITULO", "ALIQ_IPI"]],
            on="NCM_NORM",
            how="left",
            suffixes=("", "_TIPI"),
        )
        df["ESSENCIALIDADE"] = df.apply(
            lambda row: classificar_essencialidade(row.get("CAPITULO"), row.get("ALIQ_IPI")),
            axis=1,
        )
        df["PERFIL_IBS_CBS_2026"] = df["ESSENCIALIDADE"].apply(sugerir_perfil_ibs_cbs)
    else:
        df["DESCRICAO"] = ""
        df["CAPITULO"] = pd.NA
        df["ALIQ_IPI"] = pd.NA
        df["ESSENCIALIDADE"] = ""
        df["PERFIL_IBS_CBS_2026"] = "A CLASSIFICAR (sem TIPI carregada)"

    # Campos IBS/CBS default
    df["IBS_CBS_STATUS"] = "A CLASSIFICAR"
    df["cClassTrib"] = ""
    df["Class_Trib_IBS"] = ""
    df["Class_Trib_CBS"] = ""
    df["GRUPO_MACRO"] = ""
    df["SUBGRUPO"] = ""
    df["ESSENCIALIDADE_IBS"] = ""
    df["ESSENCIALIDADE_CBS"] = ""
    df["CST_IBS_CBS_VENDA"] = pd.NA
    df["ALIQ_IBS_UF_VENDA_2026"] = pd.NA
    df["ALIQ_IBS_MUN_VENDA_2026"] = pd.NA
    df["ALIQ_CBS_VENDA_2026"] = pd.NA
    df["ALIQ_EFETIVA_IBS_VENDA_2026"] = pd.NA
    df["ALIQ_EFETIVA_CBS_VENDA_2026"] = pd.NA

    # 2) Join com MATRIZ CBN (treino) – por NCM_NORM
    if df_cbn is not None and not df_cbn.empty:
        df = df.merge(
            df_cbn.add_prefix("CBN_"),
            left_on="NCM_NORM",
            right_on="CBN_NCM_NORM",
            how="left",
        )

        # Para NCM com treino CBN, preencher campos IBS/CBS
        mascaracbn = df["CBN_NCM_NORM"].notna()

        # grupo/subgrupo
        for col_ranking, col_cbn in [
            ("GRUPO_MACRO", "CBN_GRUPO_MACRO"),
            ("SUBGRUPO", "CBN_SUBGRUPO"),
            ("cClassTrib", "CBN_cClassTrib"),
            ("ESSENCIALIDADE_IBS", "CBN_ESSENCIALIDADE_IBS"),
            ("ESSENCIALIDADE_CBS", "CBN_ESSENCIALIDADE_CBS"),
        ]:
            if col_cbn in df.columns:
                df.loc[mascaracbn, col_ranking] = df.loc[mascaracbn, col_cbn]

        # CST / alíquotas IBS/CBS 2026
        for col_ranking, col_cbn in [
            ("CST_IBS_CBS_VENDA", "CBN_CST_IBS_CBS_VENDA"),
            ("ALIQ_IBS_UF_VENDA_2026", "CBN_ALIQ_IBS_UF_VENDA_2026"),
            ("ALIQ_IBS_MUN_VENDA_2026", "CBN_ALIQ_IBS_MUN_VENDA_2026"),
            ("ALIQ_CBS_VENDA_2026", "CBN_ALIQ_CBS_VENDA_2026"),
            ("ALIQ_EFETIVA_IBS_VENDA_2026", "CBN_ALIQ_EFETIVA_IBS_VENDA_2026"),
            ("ALIQ_EFETIVA_CBS_VENDA_2026", "CBN_ALIQ_EFETIVA_CBS_VENDA_2026"),
        ]:
            if col_cbn in df.columns:
                df.loc[mascaracbn, col_ranking] = df.loc[mascaracbn, col_cbn]

        # Para NCM com treino CBN, considera que já há um "rótulo" IBS/CBS
        df.loc[mascaracbn, "IBS_CBS_STATUS"] = "CLASSIFICADO_POR_TREINO_CBN"

        # Poderíamos, se quiser, usar CST como Class_Trib_IBS/CBS inicial:
        df.loc[mascaracbn, "Class_Trib_IBS"] = df.loc[mascaracbn, "CST_IBS_CBS_VENDA"].astype(str)
        df.loc[mascaracbn, "Class_Trib_CBS"] = df.loc[mascaracbn, "CST_IBS_CBS_VENDA"].astype(str)

    # Valor em BRL formatado
    df["VL_TOTAL_ITEM_BR"] = df["VL_TOTAL_ITEM"].apply(format_currency_brl)

    # Observação padrão
    df["OBS_IBS_CBS_2026"] = (
        "Sugestão estruturada a partir da TIPI e do treino CBN quando disponível. "
        "Validar na matriz PriceTax/LavoraTax e na legislação do IBS/CBS 2026."
    )

    # limpa colunas auxiliares de merge CBN
    df = df[[c for c in df.columns if not c.startswith("CBN_")]]

    return df

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
            # |0200|COD_ITEM|DESCR_ITEM|...|TIPO_ITEM|COD_NCM|...
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
            # |C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|...|DT_DOC|DT_E_S|VL_DOC|...
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
            # |C170|NUM_ITEM|COD_ITEM|DESCR_COMPL|QTD|UNID|VL_ITEM|VL_DESC|IND_MOV|...|CST_ICMS|CFOP|...
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

def gerar_excel_bytes(df_itens: pd.DataFrame,
                      df_ranking: pd.DataFrame,
                      df_ranking_ibs_cbs: pd.DataFrame) -> bytes:
    """
    Gera um Excel em memória com:
      - Itens de Saída (C170)
      - Ranking Produtos
      - Ranking + TIPI/IBS/CBS (com treino CBN)
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

# Estilo PriceTax-like
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
    "enriquece com **TIPI** e com o **treino da CBN** (GRADE_Reforma_Tributaria_2026_CBN.xlsx) "
    "para estruturar a visão de IBS/CBS 2026 (cClassTrib, essenc., alíquotas)."
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
        "A Essencialidade heurística baseada na TIPI funcionará somente depois "
        "que você criar/importar esse CSV."
    )
else:
    st.success("TIPI carregada (tipi_ncm.csv). O ranking será enriquecido com CAPÍTULO/ALIQ_IPI/Essencialidade.")

df_cbn = carregar_matriz_cbn()
if df_cbn is None:
    st.warning(
        "⚠️ Arquivo `GRADE_Reforma_Tributaria_2026_CBN.xlsx` não encontrado ou sem aba VENDAS_2026. "
        "O treino IBS/CBS 2026 da CBN só será aplicado quando esse arquivo estiver na pasta do app."
    )
else:
    st.success("Matriz CBN carregada. NCMs contemplados serão marcados como `CLASSIFICADO_POR_TREINO_CBN`.")

if uploaded_files:
    if st.button("🚀 Processar EFD PIS/COFINS"):
        try:
            temp_paths = salvar_uploads_temp(uploaded_files)

            with st.spinner("Lendo arquivos e montando ranking de saídas..."):
                df_itens = parse_efd_piscofins_files(temp_paths)
                df_ranking = gerar_ranking(df_itens)
                df_ranking_ibs_cbs = enriquecer_com_tipi_e_cbn(df_ranking, df_tipi, df_cbn)

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
                        "🧱 Visão IBS/CBS 2026 (com treino CBN)",
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
                # Tab 3 – Visão IBS/CBS 2026 (treino CBN)
                # -----------------------------------------
                with tab3:
                    if df_ranking_ibs_cbs is None or df_ranking_ibs_cbs.empty:
                        st.info("Sem dados suficientes para montar a visão IBS/CBS 2026.")
                    else:
                        st.write("### Estrutura para IBS/CBS 2026 por NCM/CFOP/Produto")
                        st.caption(
                            "Campos IBS/CBS 2026 preenchidos automaticamente quando o NCM foi treinado na CBN "
                            "(IBS_CBS_STATUS = CLASSIFICADO_POR_TREINO_CBN). "
                            "Demais NCMs permanecem 'A CLASSIFICAR'."
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
                            "GRUPO_MACRO",
                            "SUBGRUPO",
                            "ESSENCIALIDADE_IBS",
                            "ESSENCIALIDADE_CBS",
                            "PERFIL_IBS_CBS_2026",
                            "IBS_CBS_STATUS",
                            "cClassTrib",
                            "CST_IBS_CBS_VENDA",
                            "ALIQ_IBS_UF_VENDA_2026",
                            "ALIQ_IBS_MUN_VENDA_2026",
                            "ALIQ_CBS_VENDA_2026",
                            "ALIQ_EFETIVA_IBS_VENDA_2026",
                            "ALIQ_EFETIVA_CBS_VENDA_2026",
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
                        - IBS e CBS passam a ser calculados e informados, inicialmente com alíquotas reduzidas, "
                        "convivendo com o sistema atual.  
                        - Mesmo que o efeito financeiro seja reduzido/informativo, a obrigação de destacar IBS/CBS "
                        "no documento fiscal é real.

                        **2) Obrigatoriedade de destacar IBS/CBS na NF-e**  
                        - Novos campos no XML (NT específica) para IBS e CBS: identificação, base, valor e "
                        "códigos de situação tributária.  
                        - Sem esses campos preenchidos corretamente, a NF tende a ser rejeitada a partir da "
                        "data de obrigatoriedade.

                        **3) cClassTrib e classificação da operação**  
                        - Haverá códigos específicos para IBS/CBS, combinando:  
                          - Operação onerosa x não onerosa;  
                          - Redução, isenção, suspensão;  
                          - Cadeias específicas, regimes especiais.  
                        - A combinação **CFOP + NCM + natureza da operação** é o núcleo dessa decisão – e é isso "
                        "que o ranking entrega.

                        **4) O que este app entrega para 2026**  
                        - Ranking consolidado por **NCM + CFOP + Descrição**.  
                        - Essencialidade heurística por TIPI (quando carregada).  
                        - Enriquecimento automático com o treino da CBN para os NCM já classificados:  
                          - `cClassTrib`, essenc. IBS/CBS, alíquotas IBS/CBS 2026, CST etc.  
                        - Estrutura pronta para plugar a Matriz PriceTax e gerar a grade final de parametrização de ERP.

                        **5) Como evoluir a partir daqui**  
                        - Você pode replicar o modelo da CBN para outros clientes:  
                          - Consolidar uma **Matriz PriceTax por NCM**, independente do cliente.  
                          - Usar este app como motor de leitura de SPED, e a matriz como "oráculo" de IBS/CBS.  
                        - Sempre com validação jurídica em cima das Leis Complementares e normas do IBS/CBS.
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
