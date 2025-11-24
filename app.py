import io
import os
import tempfile

import pandas as pd
import streamlit as st

# Importa o motor que você já confia
# (o mesmo que gera a aba "Ranking Produtos" no Excel)
from unified_auditor import (
    parse_sped_file,
    aggregate_records,
)

# =========================================
# CONFIG STREAMLIT / VISUAL (PriceTax vibe)
# =========================================

st.set_page_config(
    page_title="Ranking Produtos SPED ICMS/IPI – PriceTax",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root {
    --bg-dark: #050608;
    --bg-card: #101219;
    --text-light: #F5F5F5;
    --muted: #9CA3AF;
    --accent: #FFC300;
    --accent-soft: #FFD54F;
    --border-soft: #20232F;
}
.stApp {
    background-color: var(--bg-dark);
    color: var(--text-light);
}
.block-container {
    padding-top: 1.2rem;
}
h1, h2, h3, h4, h5, h6 {
    color: var(--accent);
}
hr {
    border: none;
    border-top: 1px solid #252836;
    margin: 1rem 0;
}
.card {
    background-color: var(--bg-card);
    border-radius: 16px;
    border: 1px solid var(--border-soft);
    padding: 18px 20px;
    margin-bottom: 14px;
}
.metric-label {
    font-size: 0.8rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: .12em;
}
.metric-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent-soft);
}
.metric-sub {
    font-size: 0.8rem;
    color: var(--muted);
}
.stFileUploader label {
    color: var(--accent-soft) !important;
    font-weight: 600;
}
.stFileUploader div[data-baseweb="file-uploader"] {
    background-color: #050608;
    border-radius: 12px;
    border: 1px dashed #3F3F46;
}
.stButton > button {
    background-color: var(--accent);
    color: #050608;
    border: none;
    padding: 0.6rem 1.6rem;
    border-radius: 999px;
    font-weight: 700;
}
.stButton > button:hover {
    background-color: var(--accent-soft);
    color: #050608;
}
</style>
""", unsafe_allow_html=True)

# ==========================
# FUNÇÕES AUXILIARES
# ==========================

def salvar_sped_temporario(uploaded_file) -> str:
    """
    Salva o arquivo enviado pelo usuário em um arquivo temporário .txt
    e retorna o caminho. Isso é necessário porque o unified_auditor
    trabalha com caminho de arquivo, não com bytes em memória.
    """
    suffix = ".txt"
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # fechamos o descritor; vamos escrever com open()
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    return tmp_path


def gerar_excel_bytes(sheets: dict) -> bytes:
    """
    Versão em memória da write_excel do unified_auditor:
    escreve TODAS as abas de `sheets` em um Excel e devolve bytes.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        for sheet_name, df in sheets.items():
            # Excel só aceita até 31 caracteres no nome da aba
            name = str(sheet_name)[:31]
            df.to_excel(writer, sheet_name=name, index=False)
            worksheet = writer.sheets[name]
            # Congela cabeçalho
            worksheet.freeze_panes(1, 0)
            worksheet.set_zoom(90)
            # Auto-ajuste de largura de coluna (igual ao unified_auditor)
            for i, col in enumerate(df.columns):
                try:
                    max_len = max(
                        (len(str(x)) for x in [col] + df[col].astype(str).tolist()),
                        default=0,
                    )
                except Exception:
                    max_len = len(str(col))
                width = min(max(max_len + 2, 12), 60)
                worksheet.set_column(i, i, width)
    buf.seek(0)
    return buf.getvalue()


def processar_sped(uploaded_file):
    """
    1) Salva o SPED em arquivo temporário
    2) Usa parse_sped_file (unified_auditor) para ler
    3) Usa aggregate_records (unified_auditor) para montar TODOS os DataFrames
    4) Retorna (record, sheets)
    """
    tmp_path = salvar_sped_temporario(uploaded_file)

    # Não vamos usar TIPI nem XML aqui => mapas vazios
    tipi_map = {}
    xml_map = {}

    # Um arquivo → um SpedRecord
    rec = parse_sped_file(tmp_path, xml_map, tipi_map)

    # Aggregate_records espera lista de SpedRecord
    sheets = aggregate_records([rec])

    # Remove o arquivo temporário
    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return rec, sheets


# ==========================
# UI
# ==========================

st.markdown("### 🧾 Ranking de Produtos – SPED ICMS/IPI (motor unified_auditor)")

st.write(
    "Este app lê um **SPED ICMS/IPI (.txt)**, usa o mesmo motor do "
    "`unified_auditor.py` para gerar a aba **'Ranking Produtos'** e "
    "exporta um Excel completo para BI / TI."
)

uploaded = st.file_uploader(
    "Selecione o arquivo SPED ICMS/IPI (.txt)",
    type=["txt"],
    help="Arquivo texto gerado pela EFD ICMS/IPI (SPED Fiscal).",
)

if uploaded is not None:
    try:
        with st.spinner("Processando SPED com unified_auditor..."):
            rec, sheets = processar_sped(uploaded)

        # ---------------- CABEÇALHO EMPRESA ----------------
        md = rec.master_data or {}

        st.success("SPED processado com sucesso. Ranking montado com os MESMOS campos do unified_auditor.")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### 🏢 Dados do Arquivo / Empresa (SPED)")
            st.markdown(f"**Competência:** {md.get('competence', '')}")
            st.markdown(f"**Razão Social:** {md.get('company_name', '')}")
            st.markdown(f"**CNPJ:** {md.get('company_cnpj', '')}")
            st.markdown(f"**IE:** {md.get('company_ie', '')}")
            st.markdown(f"**Município (código):** {md.get('company_cod_mun', '')}")
            st.markdown(f"**Perfil:** {md.get('company_profile', '')}")

        with col2:
            st.markdown("#### 📊 Visão Rápida")
            df_items = sheets.get("Detalhes Itens")
            total_valor = 0.0
            q_itens = 0
            q_ncm = 0
            q_cfop = 0
            if df_items is not None and not df_items.empty:
                q_itens = len(df_items)
                if "NCM Item" in df_items.columns:
                    q_ncm = df_items["NCM Item"].nunique()
                if "CFOP" in df_items.columns:
                    q_cfop = df_items["CFOP"].nunique()
                if "Valor Total Item" in df_items.columns:
                    total_valor = float(
                        pd.to_numeric(df_items["Valor Total Item"], errors="coerce")
                        .fillna(0.0)
                        .sum()
                    )

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Base de itens (Entradas + Saídas)</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>R$ {total_valor:,.2f}</div>"
                .replace(",", "X").replace(".", ",").replace("X", "."),
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='metric-sub'>{q_itens} linhas • {q_ncm} NCMs • {q_cfop} CFOPs</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # ---------------- RANKING PRODUTOS ----------------
        df_ranking = sheets.get("Ranking Produtos")

        if df_ranking is None or df_ranking.empty:
            st.warning(
                "O unified_auditor não conseguiu gerar a aba **'Ranking Produtos'** "
                "(provavelmente não há itens C170 consistentes)."
            )
        else:
            st.markdown("#### 🧱 Ranking Produtos (igual ao unified_auditor)")
            st.caption(
                "Agrupado por: Competência, CNPJ, Razão Social, Descrição do Produto, "
                "NCM Item e CFOP, somando Valor Contábil, BC ICMS, ICMS e IPI."
            )
            st.dataframe(df_ranking.head(200), use_container_width=True)

        # ---------------- OUTRAS ABAS ÚTEIS (opcional, só exibir se existirem) ----------------
        st.markdown("---")
        st.markdown("#### 🔍 Outras abas geradas pelo unified_auditor (visualização rápida)")

        tabs_nomes = []
        dfs_para_tabs = []

        for nome in [
            "Resumo Itens por NCM-CFOP",
            "Resumo CFOP-NCM-CST",
            "Resumo Entradas por CFOP",
            "Resumo Entradas por NCM-CFOP",
            "Resumo Saídas por CFOP-CST",
        ]:
            df = sheets.get(nome)
            if df is not None and not df.empty:
                tabs_nomes.append(nome)
                dfs_para_tabs.append(df)

        if tabs_nomes:
            tabs = st.tabs(tabs_nomes)
            for t, df in zip(tabs, dfs_para_tabs):
                with t:
                    st.dataframe(df.head(200), use_container_width=True)
        else:
            st.info("Nenhuma aba adicional relevante encontrada (de acordo com os dados deste SPED).")

        # ---------------- DOWNLOAD EXCEL COMPLETO ----------------
        st.markdown("---")
        st.markdown("### 📥 Download do Excel (todas as abas do unified_auditor)")

        excel_bytes = gerar_excel_bytes(sheets)

        nome_base = uploaded.name.rsplit(".", 1)[0]
        nome_arquivo = f"Auditor_SPED_{nome_base}_RankingProdutos.xlsx"

        st.download_button(
            label="⬇️ Baixar Excel completo (inclui aba 'Ranking Produtos')",
            data=excel_bytes,
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

else:
    st.info("Faça o upload de um SPED ICMS/IPI (.txt) para gerar o Ranking de Produtos.")
