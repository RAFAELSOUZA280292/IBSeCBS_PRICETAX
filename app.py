import re
import io
import datetime

import pandas as pd
import requests
import streamlit as st

# ==========================
#   CONFIG STREAMLIT / TEMA
# ==========================

st.set_page_config(
    page_title="Diagnóstico SPED ICMS/IPI 2025-2026 – PriceTax",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS com paleta inspirada no site da PriceTax
st.markdown("""
<style>
:root {
    --bg-dark: #0B0B0B;
    --bg-card: #151515;
    --text-light: #F5F5F5;
    --muted: #9CA3AF;
    --highlight: #FFC300;
    --highlight-soft: #FFD54F;
    --border-soft: #2D2D2D;
}
.stApp {
    background-color: var(--bg-dark);
    color: var(--text-light);
}
h1, h2, h3, h4, h5, h6 {
    color: var(--highlight);
}
hr {
    border: none;
    border-top: 1px solid #2D2D2D;
    margin: 1rem 0;
}
.block-container {
    padding-top: 1.5rem;
}
.card {
    background-color: var(--bg-card);
    border-radius: 16px;
    border: 1px solid var(--border-soft);
    padding: 18px 20px;
    margin-bottom: 14px;
}
.metric-label {
    font-size: 0.9rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .08em;
}
.metric-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--highlight-soft);
}
.metric-sub {
    font-size: 0.8rem;
    color: var(--muted);
}
.stTextInput label, .stFileUploader label {
    color: var(--highlight-soft) !important;
    font-weight: 600;
}
.stFileUploader div[data-baseweb="file-uploader"] {
    background-color: #111111;
    border-radius: 12px;
    border: 1px dashed #525252;
}
.stButton > button {
    background-color: var(--highlight);
    color: #111111;
    border: none;
    padding: 0.6rem 1.4rem;
    border-radius: 999px;
    font-weight: 700;
}
.stButton > button:hover {
    background-color: var(--highlight-soft);
    color: #111111;
}
</style>
""", unsafe_allow_html=True)

# ==========================
#   CONFIG / URLs
# ==========================

URL_BRASILAPI_CNPJ = "https://brasilapi.com.br/api/cnpj/v1/"

# ==========================
#   FUNÇÕES AUXILIARES
# ==========================

def only_digits(s: str) -> str:
    return re.sub(r"[^0-9]", "", s or "")


def format_cnpj_mask(cnpj: str) -> str:
    c = only_digits(cnpj)
    if len(c) != 14:
        return cnpj
    return f"{c[0:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def normalizar_situacao_cadastral(txt: str) -> str:
    s = (txt or "").strip().upper()
    if not s:
        return "N/A"
    if "ATIV" in s:
        return "ATIVO"
    if "INAPT" in s:
        return "INAPTO"
    if "SUSP" in s:
        return "SUSPENSO"
    if "BAIX" in s:
        return "BAIXADO"
    return s


def classificar_tipo_operacao_por_cfop(cfop: str) -> str:
    """
    PRODUTO x SERVIÇO por CFOP:
      - grupo 3 ou 4 => SERVIÇO (transporte/comunicação)
      - demais => PRODUTO
    """
    cfop = (cfop or "").strip()
    if len(cfop) != 4 or not cfop.isdigit():
        return "DESCONHECIDO"
    grupo = cfop[1]
    if grupo in {"3", "4"}:
        return "SERVIÇO"
    return "PRODUTO"


def sugerir_cclasstrib_2026(cfop: str) -> str:
    """
    Sugestão de cClassTrib para NF-e/NF-s em 2026.
    Lógica simplificada:
      - CFOP de saída/prestação (5,6,7) grupos 1,3,4,5,6,7 => 000001 (onerosa)
      - Devoluções (grupo 2) => 000001
      - Grupo 9 => 410999 (não onerosa genérica: garantia, teste, brinde etc.)
    """
    cfop = (cfop or "").strip()
    if len(cfop) != 4 or not cfop.isdigit():
        return "000001"

    primeiro = cfop[0]
    grupo = cfop[1]

    if primeiro not in {"5", "6", "7"}:
        return "000001"

    # Entrega futura / remessa – ambas onerosas
    if cfop in {"5922", "6922", "7922", "5923", "6923", "7923"}:
        return "000001"
    if cfop in {"5116", "6116", "7116", "5117", "6117", "7117"}:
        return "000001"

    if grupo in {"1", "3", "4", "5", "6", "7"}:
        return "000001"
    if grupo == "2":
        return "000001"
    if grupo == "9":
        return "410999"

    return "000001"


def observacao_cclasstrib(cfop: str) -> str:
    cfop = (cfop or "").strip()
    if len(cfop) != 4 or not cfop.isdigit():
        return ""
    primeiro = cfop[0]
    grupo = cfop[1]

    if primeiro in {"5", "6", "7"} and grupo == "2":
        return "Devolução: ideal usar o mesmo cClassTrib da NF original."
    if primeiro in {"5", "6", "7"} and grupo == "9":
        return "Provável operação não onerosa (garantia/bonificação/teste). Revisar caso a caso."
    return ""


# ==========================
#   CONSULTA CNPJ / CNAE
# ==========================

@st.cache_data(ttl=3600, show_spinner=False)
def consulta_brasilapi_cnpj(cnpj_limpo: str) -> dict:
    try:
        r = requests.get(f"{URL_BRASILAPI_CNPJ}{cnpj_limpo}", timeout=15)
        if r.status_code in (400, 404):
            return {"__error": "not_found"}
        if r.status_code in (429, 500, 502, 503, 504):
            return {"__error": "unavailable"}
        r.raise_for_status()
        return r.json()
    except:
        return {"__error": "unavailable"}


def enriquecer_com_cnpj(cnpj_raw: str) -> dict:
    cnpj_limpo = only_digits(cnpj_raw)
    if len(cnpj_limpo) != 14:
        return {"CNPJ": cnpj_raw, "__error": "cnpj_invalido"}

    dados = consulta_brasilapi_cnpj(cnpj_limpo)
    if dados.get("__error"):
        return {"CNPJ": cnpj_limpo, "__error": dados["__error"]}

    sit = normalizar_situacao_cadastral(dados.get("descricao_situacao_cadastral", ""))

    perfil = {
        "CNPJ": format_cnpj_mask(dados.get("cnpj", cnpj_limpo)),
        "Razao_Social": dados.get("razao_social", ""),
        "Nome_Fantasia": dados.get("nome_fantasia", ""),
        "Situacao_Cadastral": sit,
        "Data_Inicio_Atividade": dados.get("data_inicio_atividade", ""),
        "CNAE_Fiscal_Codigo": dados.get("cnae_fiscal", ""),
        "CNAE_Fiscal_Descricao": dados.get("cnae_fiscal_descricao", ""),
        "Porte": dados.get("porte", ""),
        "Natureza_Juridica": dados.get("natureza_juridica", ""),
        "Email": dados.get("email", ""),
        "Municipio": dados.get("municipio", ""),
        "UF": dados.get("uf", ""),
        "CEP": dados.get("cep", ""),
        "Data_Consulta": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return perfil


# ==========================
#   PARSE DO SPED ICMS/IPI
# ==========================

def processar_sped_icms(conteudo: str):
    """
    Lê conteúdo de um SPED ICMS/IPI (.txt) como string.
    Extrai:
      - master_data (0000)
      - produtos_0200
      - itens C170 (quando houver)
      - consolidações C190 (sempre que houver)
    Se não houver C170, cria itens sintéticos a partir do C190.
    Retorna:
      master_data_enriquecido, df_itens, origem_itens ("C170" ou "C190")
    """
    master_data = {}
    produtos_0200 = {}
    itens = []
    c190_rows = []

    for linha in conteudo.splitlines():
        linha = linha.rstrip("\n")
        if not linha.startswith("|"):
            continue

        partes = linha.split("|")
        if len(partes) < 2:
            continue

        registro = partes[1]

        # 0000 - dados do contribuinte
        if registro == "0000":
            master_data["COD_VER"] = partes[2] if len(partes) > 2 else ""
            master_data["COD_FIN"] = partes[3] if len(partes) > 3 else ""
            master_data["DT_INI"] = partes[4] if len(partes) > 4 else ""
            master_data["DT_FIN"] = partes[5] if len(partes) > 5 else ""
            master_data["NOME"] = partes[6] if len(partes) > 6 else ""
            master_data["CNPJ"] = partes[7] if len(partes) > 7 else ""
            master_data["UF"] = partes[9] if len(partes) > 9 else ""
            master_data["IE"] = partes[10] if len(partes) > 10 else ""

        # 0200 - cadastro de produtos
        if registro == "0200":
            cod_item = partes[2] if len(partes) > 2 else ""
            descr_item = partes[3] if len(partes) > 3 else ""
            ncm = partes[6] if len(partes) > 6 else ""
            produtos_0200[cod_item] = {
                "COD_ITEM": cod_item,
                "DESCR_ITEM": descr_item,
                "NCM": ncm,
            }

        # C170 - itens de notas
        if registro == "C170":
            if len(partes) < 12:
                continue
            cod_item = partes[3]
            descr_compl = partes[4]
            try:
                vl_item = float((partes[6] or "0").replace(",", "."))
            except ValueError:
                vl_item = 0.0
            cfop = partes[11] if len(partes) > 11 else ""

            item = {
                "COD_ITEM": cod_item,
                "DESCR_COMPL": descr_compl,
                "VL_ITEM": vl_item,
                "CFOP": cfop,
            }

            if cod_item in produtos_0200:
                item["DESCR_ITEM"] = produtos_0200[cod_item]["DESCR_ITEM"]
                item["NCM"] = produtos_0200[cod_item]["NCM"]
            else:
                item["DESCR_ITEM"] = ""
                item["NCM"] = ""

            itens.append(item)

        # C190 - consolidação por CFOP/CST
        if registro == "C190":
            # |C190|CST_ICMS|CFOP|ALIQ_ICMS|VL_OPR|VL_BC_ICMS|...
            if len(partes) < 6:
                continue
            cfop = partes[3] if len(partes) > 3 else ""
            try:
                vl_opr = float((partes[5] or "0").replace(",", "."))
            except ValueError:
                vl_opr = 0.0

            c190_rows.append({"CFOP": cfop, "VL_OPR": vl_opr})

    origem_itens = "C170"
    if not itens:
        # Não há detalhe de item (C170), vamos usar C190 como base
        if not c190_rows:
            raise ValueError("Nenhum registro C170 ou C190 encontrado no arquivo SPED.")
        origem_itens = "C190"
        for row in c190_rows:
            cfop = row["CFOP"]
            vl = row["VL_OPR"]
            itens.append({
                "COD_ITEM": "",
                "DESCR_COMPL": "",
                "DESCR_ITEM": "",
                "NCM": "",
                "CFOP": cfop,
                "VL_ITEM": vl,
            })

    df_itens = pd.DataFrame(itens)

    # Classificações
    df_itens["TIPO_OPERACAO"] = df_itens["CFOP"].astype(str).apply(classificar_tipo_operacao_por_cfop)
    df_itens["cClassTrib_2026"] = df_itens["CFOP"].astype(str).apply(sugerir_cclasstrib_2026)
    df_itens["OBS_2026"] = df_itens["CFOP"].astype(str).apply(observacao_cclasstrib)

    # Enriquecimento com CNPJ
    cnpj_sped = master_data.get("CNPJ", "")
    perfil_cnpj = enriquecer_com_cnpj(cnpj_sped)

    master_data_enriquecido = {
        **master_data,
        **{
            "CNPJ_FORMATADO": perfil_cnpj.get("CNPJ", format_cnpj_mask(cnpj_sped)),
            "RAZAO_SOCIAL_CNPJ": perfil_cnpj.get("Razao_Social", ""),
            "NOME_FANTASIA_CNPJ": perfil_cnpj.get("Nome_Fantasia", ""),
            "SITUACAO_CADASTRAL_CNPJ": perfil_cnpj.get("Situacao_Cadastral", ""),
            "CNAE_FISCAL_CODIGO": perfil_cnpj.get("CNAE_Fiscal_Codigo", ""),
            "CNAE_FISCAL_DESCRICAO": perfil_cnpj.get("CNAE_Fiscal_Descricao", ""),
            "PORTE": perfil_cnpj.get("Porte", ""),
            "NATUREZA_JURIDICA": perfil_cnpj.get("Natureza_Juridica", ""),
            "DATA_INICIO_ATIVIDADE": perfil_cnpj.get("Data_Inicio_Atividade", ""),
        },
    }

    return master_data_enriquecido, df_itens, origem_itens


def gerar_dataframes_relatorios(master_data: dict, df_itens: pd.DataFrame):
    # Foco em CFOP de saída/prestação
    df_saidas = df_itens[df_itens["CFOP"].astype(str).str[0].isin(["5", "6", "7"])].copy()

    # Ranking produtos por NCM + CFOP
    df_rank_prod = (
        df_saidas.groupby(["NCM", "CFOP", "DESCR_ITEM"], dropna=False, as_index=False)["VL_ITEM"]
        .sum()
        .sort_values("VL_ITEM", ascending=False)
    )

    # Ranking CFOP
    df_rank_cfop = (
        df_saidas.groupby("CFOP", as_index=False)["VL_ITEM"]
        .sum()
        .sort_values("VL_ITEM", ascending=False)
    )

    # Perfil trib 2026
    df_perfil_2026 = (
        df_saidas.groupby(
            ["NCM", "CFOP", "DESCR_ITEM", "TIPO_OPERACAO", "cClassTrib_2026", "OBS_2026"],
            dropna=False,
            as_index=False,
        )["VL_ITEM"]
        .sum()
        .sort_values("VL_ITEM", ascending=False)
    )

    total_receita = df_perfil_2026["VL_ITEM"].sum()
    if total_receita == 0:
        total_receita = 1
    df_perfil_2026["PERCENTUAL_RECEITA"] = (df_perfil_2026["VL_ITEM"] / total_receita) * 100

    df_empresa = pd.DataFrame([master_data])

    return df_empresa, df_rank_prod, df_perfil_2026, df_rank_cfop


def gerar_excel_bytes(df_empresa, df_rank_prod, df_perfil_2026, df_rank_cfop) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_empresa.to_excel(writer, sheet_name="DADOS_EMPRESA_2025", index=False)
        df_rank_prod.to_excel(writer, sheet_name="RANKING_PRODUTOS_NCM_CFOP", index=False)
        df_perfil_2026.to_excel(writer, sheet_name="PERFIL_TRIB_2026", index=False)
        df_rank_cfop.to_excel(writer, sheet_name="RANKING_CFOP", index=False)
    buf.seek(0)
    return buf.getvalue()


# ==========================
#   UI STREAMLIT
# ==========================

st.markdown("### 🧾 Diagnóstico SPED ICMS/IPI 2025 → 2026 (PriceTax)")
st.write(
    "Faça o upload de um arquivo **SPED ICMS/IPI (.txt)**. "
    "O app vai montar o **ranking de produtos por NCM/CFOP** (quando houver C170), "
    "buscar o **CNPJ/CNAE** e sugerir o **cClassTrib para 2026**, com percentual da receita por operação."
)

uploaded_file = st.file_uploader(
    "Selecione o arquivo SPED ICMS/IPI (.txt)",
    type=["txt"],
    help="Arquivo gerado pelo PVA da EFD ICMS/IPI (formato texto, delimitado por |).",
)

if uploaded_file is not None:
    try:
        content = uploaded_file.read().decode("latin-1", errors="ignore")
        with st.spinner("Processando SPED, montando ranking e consultando CNPJ..."):
            master_data, df_itens, origem_itens = processar_sped_icms(content)
            df_empresa, df_rank_prod, df_perfil_2026, df_rank_cfop = gerar_dataframes_relatorios(
                master_data, df_itens
            )

        st.success("Processamento concluído com sucesso. Veja o diagnóstico abaixo.")

        # Aviso sobre origem dos dados de saída
        if origem_itens == "C190":
            st.warning(
                "Este SPED não possui detalhamento de itens (C170). "
                "Os valores de saída foram apurados a partir do C190 (consolidado por CFOP). "
                "Por isso, o ranking por NCM fica limitado."
            )
        else:
            st.info("Este SPED possui detalhamento de itens (C170). Ranking por NCM/CFOP baseado nos itens.")

        # ================== HEADER EMPRESA ==================
        st.markdown("----")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.markdown("#### 🏢 Dados da Empresa (SPED + BrasilAPI)")
            st.markdown(f"**Razão Social (SPED):** {master_data.get('NOME','')}")
            st.markdown(f"**CNPJ (SPED):** {format_cnpj_mask(master_data.get('CNPJ',''))}")
            st.markdown(f"**CNPJ (Consulta):** {master_data.get('CNPJ_FORMATADO','')}")
            st.markdown(f"**Período SPED:** {master_data.get('DT_INI','')} a {master_data.get('DT_FIN','')}")

            st.markdown(
                f"**CNAE Fiscal:** {master_data.get('CNAE_FISCAL_CODIGO','')} – "
                f"{master_data.get('CNAE_FISCAL_DESCRICAO','')}"
            )
            st.markdown(
                f"**Situação Cadastral (RFB):** {master_data.get('SITUACAO_CADASTRAL_CNPJ','')}"
            )

        with col_b:
            st.markdown("#### 📊 Resumo Rápido")

            total_receita = df_perfil_2026["VL_ITEM"].sum()
            qtd_itens = df_itens.shape[0]
            qtd_ncms = df_itens["NCM"].nunique()
            qtd_cfops = df_itens["CFOP"].nunique()

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Receita total CFOP 5/6/7</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>R$ {total_receita:,.2f}</div>".replace(",", "X").replace(".", ",").replace(
                    "X", "."
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='metric-sub'>{qtd_ncms} NCMs • {qtd_cfops} CFOPs • {qtd_itens} linhas base</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        # ================== TABELAS ==================
        st.markdown("----")
        st.markdown("#### 🧱 Ranking de Produtos por NCM x CFOP (Saídas 5/6/7)")
        st.dataframe(df_rank_prod.head(100), use_container_width=True)

        st.markdown("#### 🧩 Perfil Tributário 2026 – por NCM / CFOP / cClassTrib")
        st.dataframe(df_perfil_2026.head(200), use_container_width=True)

        st.markdown("#### 🔢 Ranking de CFOP (Receita 5/6/7)")
        st.dataframe(df_rank_cfop, use_container_width=True)

        # ================== DOWNLOAD EXCEL ==================
        st.markdown("----")
        st.markdown("### 📥 Download do Excel consolidado")

        excel_bytes = gerar_excel_bytes(df_empresa, df_rank_prod, df_perfil_2026, df_rank_cfop)

        nome_base = uploaded_file.name.rsplit(".", 1)[0]
        file_name = f"Diagnostico_Trib_2025_2026_{nome_base}.xlsx"

        st.download_button(
            label="⬇️ Baixar Excel (DADOS + RANKINGS + PERFIL 2026)",
            data=excel_bytes,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o SPED: {e}")
else:
    st.info("Faça o upload de um arquivo SPED ICMS/IPI para iniciar o diagnóstico.")
