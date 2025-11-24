import streamlit as st
import requests
import re
import datetime
import time
from pathlib import Path
import io
import csv

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA (VISUAL PRICETAX)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Consulta CNPJ – PriceTax",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------------------------
# CSS – ESTILO OFICIAL PRICETAX (Site: pricetax.com.br)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
:root {
    --bg-dark: #1A1A1A;
    --text-light: #EEEEEE;
    --highlight: #FFC300;
    --input-bg: #333333;
    --input-border-active: #FFD700;
}
.stApp {
    background-color: var(--bg-dark);
    color: var(--text-light);
}
h1, h2, h3, h4, h5, h6 {
    color: var(--highlight);
}
.stTextInput label {
    color: var(--highlight);
}
.stTextInput div[data-baseweb="input"] > div {
    background-color: var(--input-bg);
    color: var(--text-light);
    border: 1px solid var(--highlight);
}
.stTextInput div[data-baseweb="input"] > div:focus-within {
    border-color: var(--input-border-active);
    box-shadow: 0 0 0 0.1rem rgba(255,195,0,.25);
}
.stButton > button {
    background-color: var(--highlight);
    color: var(--bg-dark);
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    font-weight: 700;
}
.stButton > button:hover {
    background-color: #FFD700;
    color: #000000;
}
.stExpander {
    background-color: var(--input-bg);
    border: 1px solid var(--highlight);
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 10px;
}
hr {
    border-top: 1px solid #444444;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# FUNÇÕES ÚTEIS
# ------------------------------------------------------------------------------
def only_digits(s: str) -> str:
    return re.sub(r'[^0-9]', '', s or "")

def format_cnpj_mask(cnpj: str) -> str:
    c = only_digits(cnpj)
    return f"{c[0:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}" if len(c) == 14 else cnpj

# Consultas – BrasilAPI e OpenCNPJA
URL_BRASILAPI_CNPJ = "https://brasilapi.com.br/api/cnpj/v1/"
URL_OPEN_CNPJA = "https://open.cnpja.com/office/"

@st.cache_data(ttl=3600)
def consulta_brasilapi_cnpj(cnpj):
    try:
        req = requests.get(f"{URL_BRASILAPI_CNPJ}{cnpj}", timeout=15)
        if req.status_code in (400, 404):
            return {"__error": "not_found"}
        req.raise_for_status()
        return req.json()
    except:
        return {"__error": "unavailable"}

@st.cache_data(ttl=3600)
def consulta_ie_open_cnpja(cnpj, max_retries=2):
    url = f"{URL_OPEN_CNPJA}{cnpj}"
    tentativas = 0
    while tentativas <= max_retries:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                data = r.json()
                regs = data.get("registrations", []) if isinstance(data, dict) else []
                ies = []
                for reg in regs:
                    ies.append({
                        "uf": (reg or {}).get("state"),
                        "numero": (reg or {}).get("number"),
                        "habilitada": (reg or {}).get("enabled"),
                        "status_texto": ((reg or {}).get("status") or {}).get("text"),
                        "tipo_texto": ((reg or {}).get("type") or {}).get("text"),
                    })
                return ies
            if r.status_code == 404:
                return []
            if r.status_code == 429:
                time.sleep(2)
                tentativas += 1
                continue
            return []
        except:
            return []

# Normaliza situação
def normalizar_situacao(s):
    if not s: return "N/A"
    s = s.upper()
    if "ATIV" in s: return "ATIVO"
    if "INAPT" in s: return "INAPTO"
    if "SUSP" in s: return "SUSPENSO"
    if "BAIX" in s: return "BAIXADO"
    return s

# ------------------------------------------------------------------------------
# INTERFACE
# ------------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center;'>🔎 Consulta de CNPJ – PriceTax</h1>", unsafe_allow_html=True)

cnpj_input = st.text_input("Digite o CNPJ:")

if st.button("Consultar"):
    if not cnpj_input:
        st.warning("Digite um CNPJ.")
        st.stop()

    cnpj_limpo = only_digits(cnpj_input)
    if len(cnpj_limpo) != 14:
        st.error("CNPJ inválido.")
        st.stop()

    with st.spinner(f"Consultando {format_cnpj_mask(cnpj_limpo)}..."):
        dados = consulta_brasilapi_cnpj(cnpj_limpo)

    if dados.get("__error") == "not_found":
        st.error("CNPJ não encontrado.")
        st.stop()

    if dados.get("__error") == "unavailable":
        st.error("Serviço indisponível.")
        st.stop()

    st.success("Dados encontrados!")
    st.markdown("---")

    razao = dados.get("razao_social", "N/A")
    sit = normalizar_situacao(dados.get("descricao_situacao_cadastral", ""))

    st.markdown(f"### **{razao}**")
    st.write(f"**CNPJ:** {format_cnpj_mask(dados.get('cnpj',''))}")
    st.write(f"**Situação Cadastral:** {sit}")

    st.write(f"**CNAE Fiscal:** {dados.get('cnae_fiscal','N/A')} – {dados.get('cnae_fiscal_descricao','N/A')}")

    st.write(f"**Data Abertura:** {dados.get('data_inicio_atividade','N/A')}")
    st.write(f"**Porte:** {dados.get('porte','N/A')}")
    st.write(f"**Telefone:** {dados.get('ddd_telefone_1')} {dados.get('telefone_1')}")

    st.markdown("---")
    st.subheader("📍 Endereço")
    st.write(
        f"{dados.get('descricao_tipo_de_logradouro','')} "
        f"{dados.get('logradouro','')}, {dados.get('numero','')} – "
        f"{dados.get('bairro','')}, {dados.get('municipio','')}/{dados.get('uf','')}"
    )

    st.write(f"**CEP:** {dados.get('cep','N/A')}")

    st.markdown("---")
    st.subheader("📜 CNAEs Secundários")
    if dados.get("cnaes_secundarios"):
        for c in dados["cnaes_secundarios"]:
            st.write(f"- {c['codigo']} – {c['descricao']}")
    else:
        st.info("Nenhum CNAE secundário encontrado.")

    st.markdown("---")
    st.subheader("🧾 Inscrições Estaduais")

    ies = consulta_ie_open_cnpja(cnpj_limpo)
    if ies:
        for ie in ies:
            st.write(f"• {ie['uf']} – IE: {ie['numero']} – Status: {ie['status_texto']}")
    else:
        st.info("Nenhuma IE encontrada.")
