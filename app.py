import io
import re
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

# =========================
# Utils básicos
# =========================

def only_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")

def to_float_br(s) -> float:
    if s is None:
        return 0.0
    s = str(s).strip()
    if s == "":
        return 0.0
    # Caso "1.234,56"
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

def normalizar_ncm(ncm: str) -> str:
    """
    Normaliza NCM para 8 dígitos (somente números).
    Aceita formatos: '0101.21.00', '01012100', '1012100' etc.
    """
    dig = only_digits(ncm)
    if not dig:
        return ""
    return dig.zfill(8)

# =========================
# Banco TIPI → IBS/CBS
# =========================

TIPI_DB_DEFAULT_PATH = Path("TIPI_2022_ATUALIZADA_MAPEAMENTO_IBS_CBS_80porcento.xlsx")
TIPI_DB_SHEET = "TIPI_NCM_IBS_CBS"

@st.cache_data
def load_tipi_db_from_file_bytes(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=TIPI_DB_SHEET, dtype=str)
    df["NCM_DIGITOS"] = df["NCM"].astype(str).apply(normalizar_ncm)
    return df

@st.cache_data
def load_tipi_db_default() -> pd.DataFrame:
    if not TIPI_DB_DEFAULT_PATH.exists():
        return pd.DataFrame()
    df = pd.read_excel(TIPI_DB_DEFAULT_PATH, sheet_name=TIPI_DB_SHEET, dtype=str)
    df["NCM_DIGITOS"] = df["NCM"].astype(str).apply(normalizar_ncm)
    return df

def consultar_ibscbs_por_ncm(ncm: str, df_tipi: pd.DataFrame) -> dict:
    """
    Consulta na base TIPI → IBS/CBS um NCM específico.
    Retorna dict com campos principais.
    """
    ncm_norm = normalizar_ncm(ncm)
    if not ncm_norm:
        return {
            "encontrado": False,
            "mensagem": "NCM vazio ou inválido.",
            "NCM": ncm,
        }
    if df_tipi is None or df_tipi.empty:
        return {
            "encontrado": False,
            "mensagem": "Base TIPI/IBS-CBS não carregada. Verifique o arquivo no repositório ou faça upload na barra lateral.",
            "NCM": ncm,
        }
    linha = df_tipi[df_tipi["NCM_DIGITOS"] == ncm_norm].head(1)
    if linha.empty:
        return {
            "encontrado": False,
            "mensagem": "NCM não localizado na TIPI mapeada.",
            "NCM": ncm,
        }
    row = linha.iloc[0]
    def _get(col):
        return str(row.get(col, "")).strip()

    return {
        "encontrado": True,
        "mensagem": "",
        "NCM": _get("NCM"),
        "DESCRICAO_TIPI": _get("DESCRICAO_TIPI"),
        "ALIQUOTA_IPI": _get("ALIQUOTA_IPI"),
        "Capitulo_TIPI": _get("Capitulo_TIPI"),
        "Secao_TIPI": _get("Secao_TIPI"),
        "ID_Grupo": _get("ID_Grupo"),
        "Nome_Grupo": _get("Nome_Grupo"),
        "Tratamento_IBS_CBS_Geral": _get("Tratamento_IBS_CBS_Geral"),
        "Possivel_Imposto_Seletivo": _get("Possivel_Imposto_Seletivo"),
        "Observacoes_IBS_CBS": _get("Observacoes_IBS_CBS"),
    }

# =========================
# Cabeçalhos (PVA)
# =========================

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
M600_HEADERS = M200_HEADERS[:]  # mesma estrutura visual no PVA

# =========================
# Tabelas de códigos (sementes) + loaders de CSV (opcional)
# =========================

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
    "51": "Contribuição apurada – código 51 (ajuste conforme tabela interna/guia)",
}

NAT_REC_DESC = {
    "403": "Venda de óleo combustível, tipo bunker, MF – Marine Fuel (2710.19.22), "
           "óleo combustível, tipo bunker, MGO – Marine Gás Oil (2710.19.21) e "
           "óleo combustível, tipo bunker, ODM – Óleo Diesel Marítimo (2710.19.21), "
           "quando destinados à navegação de cabotagem e de apoio portuário e marítimo",
    "309": "ZFM – Zona Franca de Manaus",
    "401": "Exportação de mercadorias para o exterior",
    "405": "Desperdícios, resíduos ou aparas de plástico, de papel ou cartão, de vidro, "
           "de ferro ou aço, de cobre, de níquel, de alumínio, de chumbo, de zinco e de estanho, "
           "e demais desperdícios e resíduos metálicos do Capítulo 81 da Tipi",
    "908": "Vendas de mercadorias destinadas ao consumo",
    "911": "Receitas financeiras, inclusive variação cambial ativa tributável",
    "999": "Código genérico – Operações tributáveis à alíquota zero/isenção/suspensão (especificar)",
}

NAT_BC_CRED_DESC = {
    "01": "Aquisição de bens para revenda",
    "02": "Aquisição de bens e serviços utilizados como insumo",
    "03": "Energia elétrica e térmica, inclusive sob forma de vapor",
    "04": "Aluguéis de prédios",
    "05": "Aluguéis de máquinas e equipamentos",
    "06": "Armazenagem de mercadoria e frete na operação de venda",
    "07": "Contraprestações de arrendamento mercantil",
    "08": "Máquinas, equipamentos e outros bens incorporados ao ativo imobilizado (depreciação)",
    "09": "Edificações e benfeitorias em imóveis próprios ou de terceiros (depreciação/amortização)",
    "10": "Devolução de vendas sujeito à incidência não-cumulativa",
    "11": "Ativos intangíveis (amortização)",
    "12": "Encargos de depreciação, amortização e contraprestações de arrendamento no custo",
    "13": "Outras operações geradoras de crédito",
    "18": "Crédito presumido",
    "19": "Fretes na aquisição de insumos e bens para revenda",
    "20": "Armazenagem, seguros e vigilância na aquisição",
    "21": "Outros créditos vinculados à atividade",
}

def carregar_csv_mapa(csv_path: Path) -> dict:
    """Carrega CSV opcional com colunas: codigo,descricao."""
    try:
        df = pd.read_csv(csv_path, dtype=str, sep=",")
        df = df.rename(columns={c: c.strip().lower() for c in df.columns})
        if not {"codigo", "descricao"}.issubset(set(df.columns)):
            return {}
        df["codigo"] = df["codigo"].astype(str).str.strip()
        df["descricao"] = df["descricao"].astype(str).str.strip()
        return {row["codigo"]: row["descricao"] for _, row in df.iterrows() if row["codigo"]}
    except Exception:
        return {}

# Permite sobrescrever via arquivos externos (se existirem na pasta do app)
COD_CONT_DESC.update(carregar_csv_mapa(Path("map_cod_cont.csv")))
NAT_REC_DESC.update(carregar_csv_mapa(Path("map_nat_rec.csv")))
NAT_BC_CRED_DESC.update(carregar_csv_mapa(Path("map_nat_bc_cred.csv")))

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

# =========================
# Parser SPED (versão Streamlit, sem Path)
# =========================

def parse_sped_txt(nome_arquivo: str, linhas):
    """
    linhas: iterável de strings (cada linha do arquivo txt).
    """
    empresa_cnpj = ""; dt_ini = ""; dt_fin = ""; competencia = ""
    ap_pis = []; credito_pis = []; receitas_pis = []; rec_isentas_pis = []
    ap_cofins = []; credito_cofins = []; receitas_cofins = []; rec_isentas_cofins = []

    for raw in linhas:
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
            vals = campos[2:2+len(M200_HEADERS)]
            for titulo, val in zip(M200_HEADERS, vals):
                row[titulo] = to_float_br(val)
            ap_pis.append(row)

        elif reg == "M105":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            credito_pis.append({
                "ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                "NAT_BC_CRED": nat,
                "NAT_BC_CRED_DESC": desc_nat_bc(nat),
                "CST_PIS": (campos[3] if len(campos) > 3 else "").strip(),
                "VL_BC": to_float_br(campos[4] if len(campos) > 4 else 0),
                "ALIQ": to_float_br(campos[5] if len(campos) > 5 else 0),
                "VL_CRED": to_float_br(campos[6] if len(campos) > 6 else 0),
            })

        elif reg == "M210":
            cod = (campos[2] if len(campos) > 2 else "").strip()
            receitas_pis.append({
                "ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                "COD_CONT": cod,
                "DESCR_COD_CONT": desc_cod_cont(cod),
                "VL_REC_BRT": to_float_br(campos[3] if len(campos) > 3 else 0),
                "VL_BC_CONT": to_float_br(campos[4] if len(campos) > 4 else 0),
                "VL_BC_PIS": to_float_br(campos[7] if len(campos) > 7 else 0),
                "ALIQ_PIS": to_float_br(campos[8] if len(campos) > 8 else 0),
                "VL_CONT_APUR": to_float_br(campos[11] if len(campos) > 11 else 0),
                "VL_CONT_PER": to_float_br(campos[16] if len(campos) > 16 else 0),
            })

        elif reg == "M410":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            rec_isentas_pis.append({
                "ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                "CODIGO_DET": nat,
                "DESCR_CODIGO_DET": desc_nat_rec(nat),
                "VL_REC": to_float_br(campos[3] if len(campos) > 3 else 0),
            })

        elif reg == "M600":
            row = {"ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj}
            vals = campos[2:2+len(M600_HEADERS)]
            for titulo, val in zip(M600_HEADERS, vals):
                row[titulo] = to_float_br(val)
            ap_cofins.append(row)

        elif reg == "M505":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            credito_cofins.append({
                "ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                "NAT_BC_CRED": nat,
                "NAT_BC_CRED_DESC": desc_nat_bc(nat),
                "CST_COFINS": (campos[3] if len(campos) > 3 else "").strip(),
                "VL_BC": to_float_br(campos[4] if len(campos) > 4 else 0),
                "ALIQ": to_float_br(campos[5] if len(campos) > 5 else 0),
                "VL_CRED": to_float_br(campos[6] if len(campos) > 6 else 0),
            })

        elif reg == "M610":
            cod = (campos[2] if len(campos) > 2 else "").strip()
            receitas_cofins.append({
                "ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                "COD_CONT": cod,
                "DESCR_COD_CONT": desc_cod_cont(cod),
                "VL_REC_BRT": to_float_br(campos[3] if len(campos) > 3 else 0),
                "VL_BC_CONT": to_float_br(campos[4] if len(campos) > 4 else 0),
                "VL_BC_COFINS": to_float_br(campos[7] if len(campos) > 7 else 0),
                "ALIQ_COFINS": to_float_br(campos[8] if len(campos) > 8 else 0),
                "VL_CONT_APUR": to_float_br(campos[11] if len(campos) > 11 else 0),
                "VL_CONT_PER": to_float_br(campos[16] if len(campos) > 16 else 0),
            })

        elif reg == "M810":
            nat = (campos[2] if len(campos) > 2 else "").strip()
            rec_isentas_cofins.append({
                "ARQUIVO": nome_arquivo, "COMPETENCIA": competencia, "CNPJ_ARQUIVO": empresa_cnpj,
                "CODIGO_DET": nat,
                "DESCR_CODIGO_DET": desc_nat_rec(nat),
                "VL_REC": to_float_br(campos[3] if len(campos) > 3 else 0),
            })

    return {
        "ap_pis": ap_pis, "credito_pis": credito_pis, "receitas_pis": receitas_pis, "rec_isentas_pis": rec_isentas_pis,
        "ap_cofins": ap_cofins, "credito_cofins": credito_cofins, "receitas_cofins": receitas_cofins, "rec_isentas_cofins": rec_isentas_cofins
    }

def processar_speds_streamlit(uploaded_files):
    ap_pis_all, cred_pis_all, rec_pis_all, rec_is_pis_all = [], [], [], []
    ap_cof_all, cred_cof_all, rec_cof_all, rec_is_cof_all = [], [], [], []

    for up in uploaded_files:
        nome = up.name
        data = up.getvalue()

        if nome.lower().endswith(".txt"):
            texto = data.decode("utf-8", errors="replace")
            linhas = texto.splitlines()
            d = parse_sped_txt(nome, linhas)
        elif nome.lower().endswith(".zip"):
            d = {
                "ap_pis": [], "credito_pis": [], "receitas_pis": [], "rec_isentas_pis": [],
                "ap_cofins": [], "credito_cofins": [], "receitas_cofins": [], "rec_isentas_cofins": []
            }
            with zipfile.ZipFile(io.BytesIO(data), "r") as z:
                for info in z.infolist():
                    if not info.filename.lower().endswith(".txt"):
                        continue
                    txt_data = z.read(info.filename)
                    texto = txt_data.decode("utf-8", errors="replace")
                    linhas = texto.splitlines()
                    parcial = parse_sped_txt(info.filename, linhas)
                    for k in d.keys():
                        d[k].extend(parcial[k])
        else:
            continue

        ap_pis_all.extend(d["ap_pis"]);         cred_pis_all.extend(d["credito_pis"])
        rec_pis_all.extend(d["receitas_pis"]);  rec_is_pis_all.extend(d["rec_isentas_pis"])
        ap_cof_all.extend(d["ap_cofins"]);      cred_cof_all.extend(d["credito_cofins"])
        rec_cof_all.extend(d["receitas_cofins"]); rec_is_cof_all.extend(d["rec_isentas_cofins"])

    df_ap_pis   = pd.DataFrame(ap_pis_all)
    df_cred_pis = pd.DataFrame(cred_pis_all)
    df_rec_pis  = pd.DataFrame(rec_pis_all)
    df_ri_pis   = pd.DataFrame(rec_is_pis_all)

    df_ap_cof   = pd.DataFrame(ap_cof_all)
    df_cred_cof = pd.DataFrame(cred_cof_all)
    df_rec_cof  = pd.DataFrame(rec_cof_all)
    df_ri_cof   = pd.DataFrame(rec_is_cof_all)

    return df_ap_pis, df_cred_pis, df_rec_pis, df_ri_pis, df_ap_cof, df_cred_cof, df_rec_cof, df_ri_cof

# =========================
# STREAMLIT APP
# =========================

st.set_page_config(
    page_title="IBS/CBS + SPED PIS/COFINS — PriceTax/Lavoratory",
    layout="wide"
)

st.sidebar.title("⚙️ Configurações")

tipi_upload = st.sidebar.file_uploader(
    "TIPI mapeada (opcional — IBS/CBS)",
    type=["xlsx"],
    help="Se não enviar, o app tentará carregar o arquivo TIPI_2022_ATUALIZADA_MAPEAMENTO_IBS_CBS_80porcento.xlsx da pasta do app."
)

if tipi_upload is not None:
    df_tipi = load_tipi_db_from_file_bytes(tipi_upload.getvalue())
else:
    df_tipi = load_tipi_db_default()

if df_tipi is None or df_tipi.empty:
    st.sidebar.warning("Base TIPI/IBS-CBS não carregada. Upload recomendado.")

st.title("🧠 LAVO · IBS/CBS & SPED PIS/COFINS")
st.markdown(
    "App web da **Lavoratory / PriceTax** para:\n"
    "- Consultar **tratamento IBS/CBS** por NCM (TIPI)\n"
    "- Processar **SPED PIS/COFINS** (Bloco M) e exportar para Excel"
)

tab1, tab2 = st.tabs(["🔍 Consulta IBS/CBS por NCM", "📂 SPED PIS/COFINS → Excel"])

# -------------------------
# TAB 1: Consulta IBS/CBS por NCM
# -------------------------
with tab1:
    st.subheader("Consulta TIPI → IBS/CBS (macro 80%)")

    col_ncm, col_btn = st.columns([2, 1])

    with col_ncm:
        ncm_input = st.text_input(
            "Informe o NCM (com ou sem pontos)",
            value="",
            placeholder="Ex.: 1905.90.90 ou 19059090"
        )

    with col_btn:
        consultar = st.button("Consultar NCM")

    if consultar and ncm_input.strip():
        info = consultar_ibscbs_por_ncm(ncm_input, df_tipi)
        if not info.get("encontrado"):
            st.error(f"NCM: {info.get('NCM')}\n\n{info.get('mensagem')}")
        else:
            st.success(f"NCM encontrado: {info['NCM']}")
            st.write(f"**Descrição TIPI:** {info['DESCRICAO_TIPI']}")
            st.write(f"**Capítulo / Seção TIPI:** {info['Capitulo_TIPI']} / {info['Secao_TIPI']}")
            st.write(f"**Grupo IBS/CBS:** `{info['ID_Grupo']}` — {info['Nome_Grupo']}")
            st.write("**Tratamento IBS/CBS (geral):**")
            st.code(info["Tratamento_IBS_CBS_Geral"], language="text")
            st.write(f"**Possível Imposto Seletivo:** {info['Possivel_Imposto_Seletivo']}")
            if info["Observacoes_IBS_CBS"]:
                st.write("**Observações:**")
                st.info(info["Observacoes_IBS_CBS"])

    if df_tipi is not None and not df_tipi.empty:
        with st.expander("Ver amostra da base TIPI/IBS-CBS carregada"):
            st.dataframe(df_tipi.head(20))

# -------------------------
# TAB 2: SPED PIS/COFINS → Excel
# -------------------------
with tab2:
    st.subheader("Processar SPED PIS/COFINS (Bloco M)")

    uploaded_speds = st.file_uploader(
        "Selecione arquivos SPED (.txt ou .zip)",
        type=["txt", "zip"],
        accept_multiple_files=True
    )

    if uploaded_speds:
        if st.button("Processar SPEDs"):
            (
                df_ap_pis, df_cred_pis, df_rec_pis, df_ri_pis,
                df_ap_cof, df_cred_cof, df_rec_cof, df_ri_cof
            ) = processar_speds_streamlit(uploaded_speds)

            st.success("Processamento concluído. Visualize e baixe o Excel gerado.")

            # Mostrar pequenas amostras
            if not df_ap_pis.empty:
                st.write("**AP PIS (M200):**")
                st.dataframe(df_ap_pis.head(10))
            if not df_ap_cof.empty:
                st.write("**AP COFINS (M600):**")
                st.dataframe(df_ap_cof.head(10))

            # Montar Excel em memória para download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as w:
                if not df_ap_pis.empty:    df_ap_pis.to_excel(w, sheet_name="AP PIS", index=False)
                if not df_cred_pis.empty:  df_cred_pis.to_excel(w, sheet_name="CREDITO PIS", index=False)
                if not df_rec_pis.empty:   df_rec_pis.to_excel(w, sheet_name="RECEITAS PIS", index=False)
                if not df_ri_pis.empty:    df_ri_pis.to_excel(w, sheet_name="RECEITAS ISENTAS PIS", index=False)

                if not df_ap_cof.empty:    df_ap_cof.to_excel(w, sheet_name="AP COFINS", index=False)
                if not df_cred_cof.empty:  df_cred_cof.to_excel(w, sheet_name="CREDITO COFINS", index=False)
                if not df_rec_cof.empty:   df_rec_cof.to_excel(w, sheet_name="RECEITAS COFINS", index=False)
                if not df_ri_cof.empty:    df_ri_cof.to_excel(w, sheet_name="RECEITAS ISENTAS COFINS", index=False)

                # Índices auxiliares
                df_idx_cod_cont = pd.DataFrame(
                    [{"COD_CONT": k, "DESCRICAO": v} for k, v in sorted(COD_CONT_DESC.items(), key=lambda x: x[0])]
                )
                df_idx_nat_rec = pd.DataFrame(
                    [{"CODIGO_DET": k, "DESCRICAO": v} for k, v in sorted(NAT_REC_DESC.items(), key=lambda x: x[0])]
                )
                df_idx_nat_bc = pd.DataFrame(
                    [{"NAT_BC_CRED": k, "DESCRICAO": v} for k, v in sorted(NAT_BC_CRED_DESC.items(), key=lambda x: x[0])]
                )

                if not df_idx_cod_cont.empty:
                    df_idx_cod_cont.to_excel(w, sheet_name="ÍNDICE COD_CONT", index=False)
                if not df_idx_nat_rec.empty:
                    df_idx_nat_rec.to_excel(w, sheet_name="ÍNDICE NAT_REC", index=False)
                if not df_idx_nat_bc.empty:
                    df_idx_nat_bc.to_excel(w, sheet_name="ÍNDICE NAT_BC_CRED", index=False)

            output.seek(0)

            st.download_button(
                label="⬇️ Baixar Excel (SPED PIS/COFINS)",
                data=output,
                file_name="SPED_PIS_COFINS_BLOCO_M.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Envie um ou mais arquivos SPED (.txt ou .zip) para habilitar o processamento.")
