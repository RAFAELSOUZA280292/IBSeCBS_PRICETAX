import io
import os
import tempfile

import pandas as pd
import streamlit as st

# Importa o motor original que você enviou
from unified_auditor import (
    parse_sped_file,
    aggregate_records,
)

# ==========================
# CONFIG VISUAL (PriceTax)
# ==========================

st.set_page_config(
    page_title="Ranking Produtos – SPED ICMS/IPI | PriceTax",
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
.stApp { background-color: var(--bg-dark); color: var(--text-light); }
h1, h2, h3, h4 { color: var(--accent); }
.stButton > button {
    background-color: var(--accent);
    color: #050608;
    border: none;
    padding: 0.5rem 1.6rem;
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
# UTILITÁRIOS
# ==========================

def salvar_temp(uploaded_file):
    """Salva o arquivo de upload num temporário .txt e retorna o caminho."""
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(uploaded_file.getvalue())
    return path


def gerar_excel_bytes(sheets: dict) -> bytes:
    """Gera um Excel em memória (sem escrever em disco)."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        for sheet_name, df in sheets.items():
            safe_name = sheet_name[:31]  # limite Excel
            df.to_excel(writer, sheet_name=safe_name, index=False)
            worksheet = writer.sheets[safe_name]
            worksheet.freeze_panes(1, 0)
    buf.seek(0)
    return buf.getvalue()


# ==========================
# UI
# ==========================

st.markdown("## 🧾 Ranking de Produtos – SPED ICMS/IPI<br><small>Motor PriceTax (unified_auditor)</small>", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Selecione o SPED ICMS/IPI (.txt)",
    type=["txt"],
    help="Arquivo texto gerado pelo PVA da EFD ICMS/IPI."
)

if uploaded:
    try:
        with st.spinner("Lendo arquivo e gerando ranking..."):
            # 1. salva temp
            temp_path = salvar_temp(uploaded)

            # 2. utiliza o motor original
            record = parse_sped_file(temp_path, {}, {})
            sheets = aggregate_records([record])

            # remove temporário
            try: os.remove(temp_path)
            except: pass

        st.success("SPED processado com sucesso 🎉")

        # CABEÇALHO EMPRESA
        md = record.master_data or {}
        st.markdown("### 🏢 Dados da Empresa")
        st.write(f"**Comp:** {md.get('competence','')}")
        st.write(f"**Razão Social:** {md.get('company_name','')}")
        st.write(f"**CNPJ:** {md.get('company_cnpj','')}")

        st.markdown("---")

        # RANKING PRODUTOS
        df_rank = sheets.get("Ranking Produtos")

        if df_rank is None or df_rank.empty:
            st.error("Nenhum item encontrado para montar o Ranking Produtos.")
        else:
            st.markdown("### 🧱 Ranking de Produtos")
            st.dataframe(df_rank, use_container_width=True)

        # DOWNLOAD EXCEL
        st.markdown("---")
        st.markdown("### 📥 Download Excel (todas as abas)")

        excel_bytes = gerar_excel_bytes(sheets)
        nome_base = uploaded.name.replace(".txt", "")
        filename = f"Auditor_SPED_{nome_base}.xlsx"

        st.download_button(
            "⬇️ Baixar Excel completo",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("Envie um arquivo SPED ICMS/IPI para montar o Ranking de Produtos.")
