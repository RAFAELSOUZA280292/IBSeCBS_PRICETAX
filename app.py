import io
import os
import re
import zipfile
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

# =========================
# Utils
# =========================

def only_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")

def to_float_br(s) -> float:
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    # trata "1.234,56" -> 1234.56
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

def format_currency_brl(v) -> str:
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return ""

def normalizar_ncm(s: str) -> str:
    d = only_digits(str(s) if s is not None else "")
    if not d:
        return ""
    # geralmente 8 dígitos; se vier maior, corta; se menor, mantém como está
    if len(d) >= 8:
        return d[:8]
    return d

# =========================
# Carregamento da tabela de classificação IBS/CBS
# =========================

@st.cache_data(show_spinner=False)
def carregar_classificacao_tributaria():
    """
    Lê a planilha classificacao_tributaria.xlsx na mesma pasta do script.
    Espera a aba 'Classificação Tributária'.
    """
    base_dir = Path(__file__).resolve().parent
    xlsx_path = base_dir / "classificacao_tributaria.xlsx"

    if not xlsx_path.exists():
        return None

    df = pd.read_excel(xlsx_path, sheet_name="Classificação Tributária")

    # Normaliza NCM para join
    if "NCM" in df.columns:
        df["NCM_NORM"] = df["NCM"].astype(str).apply(normalizar_ncm)
    else:
        df["NCM_NORM"] = ""

    # Seleciona colunas principais para IBS/CBS/cClassTrib/Essencialidade
    cols_interesse = [
        "NCM_NORM",
        "NCM",
        "Especificação",
        "Essencialidade",
        "Grupo Mercadoria",
        "Subgrupo Mercadoria",
        "Código da Situação Tributária",
        "Descrição da Situação Tributária",
        "Class Trib IBS",
        "Class Trib CBS",
        "Alíquota de Referência",
        "Alíquota de IBS",
        "Alíquota de CBS",
    ]
    cols_interesse = [c for c in cols_interesse if c in df.columns]

    df_class = df[cols_interesse].copy()

    # remove duplicatas por NCM_NORM (deixa a primeira)
    df_class = df_class.drop_duplicates(subset=["NCM_NORM"])

    return df_class

def mapear_ibs_cbs(df_ranking: pd.DataFrame, df_class: pd.DataFrame) -> pd.DataFrame:
    """
    Faz o join do ranking (CFOP+NCM+DESCR_ITEM+VL_TOTAL_ITEM) com a
    classificação IBS/CBS/cClassTrib por NCM.
    """
    if df_ranking is None or df_ranking.empty or df_class is None:
        return df_ranking

    df_rank = df_ranking.copy()
    df_rank["NCM_NORM"] = df_rank["NCM"].astype(str).apply(normalizar_ncm)

    df_merged = df_rank.merge(
        df_class,
        on="NCM_NORM",
        how="left",
        suffixes=("", "_class"),
    )

    # Formata valores BRL para exibição
    df_merged["VL_TOTAL_ITEM_BR"] = df_merged["VL_TOTAL_ITEM"].apply(format_currency_brl)
    if "Alíquota de IBS" in df_merged.columns:
        df_merged["Aliq_IBS_BR"] = df_merged["Alíquota de IBS"].apply(
            lambda v: f"{v:.2f}%" if pd.notnull(v) else ""
        )
    if "Alíquota de CBS" in df_merged.columns:
        df_merged["Aliq_CBS_BR"] = df_merged["Alíquota de CBS"].apply(
            lambda v: f"{v:.2f}%" if pd.notnull(v) else ""
        )

    return df_merged

# =========================
# Parser EFD PIS/COFINS
# =========================

def parse_efd_piscofins_text(text: str, origem: str):
    """
    Lê o conteúdo de UM arquivo EFD PIS/COFINS (texto já decodificado)
    e retorna uma lista de itens de SAÍDA (CFOP 5/6/7) com:
      - competência, cnpj
      - dados da NF (modelo, série, número, data, valor doc)
      - dados do item (CFOP, COD_ITEM, descrição, NCM, VL_ITEM, etc.)
    """
    itens_saida = []

    cod_item_map = {}  # 0200: cod_item -> {"descr_item": ..., "ncm": ...}
    competencia = ""
    cnpj = ""

    # header atual do C100 (nota em curso)
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

        # 0000 – dados básicos (versão corrigida)
        if reg == "0000":
            # tenta detectar datas (8 dígitos) em qualquer posição
            datas = [c for c in campos if re.fullmatch(r"\d{8}", c or "")]
            if len(datas) >= 2:
                dt_ini, dt_fin = datas[0], datas[1]
            else:
                # fallback caso não existam 2 datas explícitas
                dt_ini = campos[4] if len(campos) > 4 else ""
                dt_fin = campos[5] if len(campos) > 5 else ""

            # monta competência
            competencia = competencia_from_dt(dt_ini, dt_fin)

            # captura CNPJ (primeiro campo com 14 dígitos)
            for c in campos:
                d = only_digits(c)
                if len(d) == 14:
                    cnpj = d
                    break

        # 0200 – cadastro de itens
        elif reg == "0200":
            # layout EFD (igual ao Fiscal):
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

        # C100 – cabeçalho do documento
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

        # C170 – itens do documento
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

            # só queremos SAÍDAS: CFOP iniciados em 5, 6 ou 7
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
    devolve um DataFrame com TODOS os itens de saída (C170 + CFOP 5/6/7),
    já cruzados com 0200.
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
    Monta ranking por CFOP + NCM + DESCR_ITEM, somando VL_ITEM.
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

    return df_rank

def gerar_excel_bytes(df_itens: pd.DataFrame, df_ranking_mapeado: pd.DataFrame) -> bytes:
    """
    Gera um Excel em memória com:
      - Detalhe Itens Saída
      - Ranking Produtos Saída + IBS/CBS/cClassTrib
      - Receita por Essencialidade
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        if df_itens is not None and not df_itens.empty:
            df_itens.to_excel(writer, sheet_name="Detalhe Itens Saída", index=False)
        if df_ranking_mapeado is not None and not df_ranking_mapeado.empty:
            df_ranking_mapeado.to_excel(writer, sheet_name="Ranking IBS_CBS", index=False)

            # Também gera um resumo por Essencialidade
            if "Essencialidade" in df_ranking_mapeado.columns:
                df_ess = (
                    df_ranking_mapeado
                    .groupby("Essencialidade", as_index=False)["VL_TOTAL_ITEM"]
                    .sum()
                    .sort_values("VL_TOTAL_ITEM", ascending=False)
                )
                df_ess.to_excel(writer, sheet_name="Receita x Essencialidade", index=False)

    buf.seek(0)
    return buf

# =========================
# Streamlit App
# =========================

st.set_page_config(
    page_title="Ranking Produtos – EFD PIS/COFINS (Saídas)",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("## 🧾 Ranking de Produtos – EFD PIS/COFINS (Saídas) + IBS/CBS 2026")
st.write(
    "- Lê **0000, 0200, C100 e C170** da EFD Contribuições (PIS/COFINS);\n"
    "- Filtra apenas itens com **CFOP iniciados em 5, 6 ou 7** (saídas);\n"
    "- Cruza cada item com o **cadastro do 0200** (descrição e NCM);\n"
    "- Monta um **ranking de produtos por CFOP + NCM + descrição**, somando o valor do item;\n"
    "- Faz o **mapeamento automático IBS/CBS 2026 + cClassTrib** com base na planilha `classificacao_tributaria.xlsx`;\n"
    "- Monta um **dashboard de Receita x Essencialidade**."
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

df_class = carregar_classificacao_tributaria()
if df_class is None:
    st.warning(
        "⚠️ Arquivo `classificacao_tributaria.xlsx` não encontrado na pasta do app. "
        "O mapeamento IBS/CBS 2026 e cClassTrib ficará em branco até você subir essa planilha."
    )

if uploaded_files:
    if st.button("🚀 Processar EFD PIS/COFINS"):
        try:
            temp_paths = salvar_uploads_temp(uploaded_files)

            with st.spinner("Lendo arquivos e montando ranking de saídas..."):
                df_itens = parse_efd_piscofins_files(temp_paths)
                df_ranking = gerar_ranking(df_itens)
                df_ranking_mapeado = mapear_ibs_cbs(df_ranking, df_class)

            # limpa temporários
            for p in temp_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass

            if df_itens is None or df_itens.empty:
                st.warning("Nenhum item de saída (CFOP 5/6/7) foi encontrado nos arquivos enviados.")
            else:
                st.success("Processamento concluído com sucesso ✅")

                # Tabs: Detalhe, Ranking IBS/CBS, Essencialidade
                tab1, tab2, tab3 = st.tabs(
                    ["🔍 Detalhe Itens Saída", "🧱 Ranking + IBS/CBS/cClassTrib", "📊 Receita x Essencialidade"]
                )

                with tab1:
                    st.caption("Amostra das primeiras linhas (você pode baixar tudo em Excel abaixo).")
                    st.dataframe(df_itens.head(500), use_container_width=True)

                with tab2:
                    if df_ranking_mapeado is None or df_ranking_mapeado.empty:
                        st.info("Sem dados suficientes para montar o ranking.")
                    else:
                        # monta um DataFrame só para exibição, com colunas mais relevantes
                        cols_show = [
                            "COMPETENCIA", "CNPJ", "CFOP", "NCM", "DESCR_ITEM",
                            "VL_TOTAL_ITEM_BR",
                            "Essencialidade",
                            "Código da Situação Tributária",
                            "Class Trib IBS", "Class Trib CBS",
                            "Aliq_IBS_BR", "Aliq_CBS_BR",
                        ]
                        cols_show = [c for c in cols_show if c in df_ranking_mapeado.columns]
                        df_display = df_ranking_mapeado[cols_show].copy()

                        st.dataframe(df_display.head(500), use_container_width=True)

                with tab3:
                    if df_ranking_mapeado is None or df_ranking_mapeado.empty or "Essencialidade" not in df_ranking_mapeado.columns:
                        st.info("Não foi possível montar o dashboard por Essencialidade (verifique se a planilha de classificação tem a coluna 'Essencialidade').")
                    else:
                        df_ess = (
                            df_ranking_mapeado
                            .groupby("Essencialidade", as_index=False)["VL_TOTAL_ITEM"]
                            .sum()
                            .sort_values("VL_TOTAL_ITEM", ascending=False)
                        )
                        df_ess["VL_TOTAL_ITEM_BR"] = df_ess["VL_TOTAL_ITEM"].apply(format_currency_brl)

                        st.write("### Receita total por Essencialidade (R$)")
                        st.dataframe(df_ess, use_container_width=True)

                        # gráfico simples
                        try:
                            st.bar_chart(
                                data=df_ess.set_index("Essencialidade")["VL_TOTAL_ITEM"]
                            )
                        except Exception:
                            pass

                # Download Excel
                st.markdown("---")
                st.markdown("### 📥 Download do Excel")

                excel_bytes = gerar_excel_bytes(df_itens, df_ranking_mapeado)
                st.download_button(
                    "⬇️ Baixar Excel (Detalhe + Ranking IBS/CBS + Essencialidade)",
                    data=excel_bytes,
                    file_name="Ranking_PIS_COFINS_Saidas_IBS_CBS.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        except Exception as e:
            st.error(f"Erro ao processar arquivos: {e}")
else:
    st.info("Envie pelo menos um arquivo EFD PIS/COFINS (.txt ou .zip) para começar.")
