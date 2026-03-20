"""
aba_xclass.py
=============
Ferramenta XClass — Hub Central de Classificação Tributária PRICETAX.

Modos disponíveis:
    1. Busca Manual por NCM — digita NCM (+ CFOP opcional) e obtém resultado completo
    2. Upload XML NFe em Lote — processa XMLs e retorna cClassTrib por item
    3. Upload SPED — processa arquivo EFD e retorna cClassTrib por linha

Todos os modos retornam:
    - cClassTrib correto (com lógica de priorização CFOP remessa > NCM)
    - Alíquotas IBS UF, IBS Municipal, CBS e Total IVA (%)
    - Base legal fundamentada na LC 214/2025
    - Regime IVA e percentual de redução aplicado
    - Exportação Excel com abas estruturadas

Autor: PRICETAX — Inteligência Tributária para a Reforma
Atualizado: 2026-03
"""

import io
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from xclass_engine import classificar_item, classificar_dataframe, IBS_UF_REF, IBS_MUN_REF, CBS_REF


# =============================================================================
# PALETA DE CORES (consistente com o restante da plataforma)
# =============================================================================
COLOR_GOLD       = "#FFDD00"
COLOR_BLACK      = "#0D0D0D"
COLOR_CARD_BG    = "#1A1A1A"
COLOR_BORDER     = "rgba(255,221,0,0.15)"
COLOR_TEXT_MAIN  = "#E5E7EB"
COLOR_TEXT_MUTED = "#9CA3AF"
COLOR_WHITE      = "#FFFFFF"
COLOR_GREEN      = "#22C55E"
COLOR_RED        = "#EF4444"


# =============================================================================
# HELPERS DE FORMATAÇÃO
# =============================================================================
def _fmt_pct(v: float) -> str:
    """Formata alíquota percentual com 4 casas decimais."""
    return f"{v:.4f}%".replace(".", ",")


def _fmt_brl(v: float) -> str:
    """Formata valor em BRL."""
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _card_resultado(res: dict, ncm_descricao: str = "") -> str:
    """Gera HTML do card de resultado de classificação."""
    cor_regime = COLOR_GOLD if res["reducao_pct"] == 0 else COLOR_GREEN
    badge_reducao = ""
    if res["reducao_pct"] > 0:
        badge_reducao = (
            f'<span style="background:{COLOR_GREEN};color:#000;padding:2px 8px;'
            f'border-radius:12px;font-size:0.8rem;font-weight:700;margin-left:8px;">'
            f'Redução {res["reducao_pct"]}%</span>'
        )

    return f"""
    <div style="background:{COLOR_CARD_BG};border:1px solid {COLOR_BORDER};
                border-radius:10px;padding:1.5rem;margin:1rem 0;">
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
            <div style="background:{COLOR_GOLD};color:#000;font-size:1.4rem;font-weight:900;
                        padding:0.5rem 1rem;border-radius:8px;letter-spacing:1px;">
                {res['cclasstrib']}
            </div>
            <div>
                <div style="color:{COLOR_TEXT_MUTED};font-size:0.8rem;">cClassTrib</div>
                <div style="color:{COLOR_WHITE};font-weight:700;">Código de Classificação Tributária</div>
            </div>
            {badge_reducao}
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;margin-bottom:1rem;">
            <div style="background:#111;border-radius:8px;padding:0.75rem;text-align:center;">
                <div style="color:{COLOR_TEXT_MUTED};font-size:0.75rem;">IBS UF</div>
                <div style="color:{COLOR_GOLD};font-weight:700;font-size:1.1rem;">{_fmt_pct(res['ibs_uf_pct'])}</div>
            </div>
            <div style="background:#111;border-radius:8px;padding:0.75rem;text-align:center;">
                <div style="color:{COLOR_TEXT_MUTED};font-size:0.75rem;">IBS Municipal</div>
                <div style="color:{COLOR_GOLD};font-weight:700;font-size:1.1rem;">{_fmt_pct(res['ibs_mun_pct'])}</div>
            </div>
            <div style="background:#111;border-radius:8px;padding:0.75rem;text-align:center;">
                <div style="color:{COLOR_TEXT_MUTED};font-size:0.75rem;">CBS</div>
                <div style="color:{COLOR_GOLD};font-weight:700;font-size:1.1rem;">{_fmt_pct(res['cbs_pct'])}</div>
            </div>
            <div style="background:{COLOR_GOLD};border-radius:8px;padding:0.75rem;text-align:center;">
                <div style="color:#000;font-size:0.75rem;font-weight:700;">Total IVA</div>
                <div style="color:#000;font-weight:900;font-size:1.1rem;">{_fmt_pct(res['total_iva_pct'])}</div>
            </div>
        </div>
        <div style="border-top:1px solid {COLOR_BORDER};padding-top:0.75rem;">
            <div style="color:{COLOR_TEXT_MUTED};font-size:0.8rem;margin-bottom:0.25rem;">Regime IVA</div>
            <div style="color:{cor_regime};font-weight:600;">{res['regime_iva']}</div>
        </div>
        {"<div style='border-top:1px solid " + COLOR_BORDER + ";padding-top:0.75rem;margin-top:0.75rem;'><div style='color:" + COLOR_TEXT_MUTED + ";font-size:0.8rem;margin-bottom:0.25rem;'>Benefício Fiscal</div><div style='color:" + COLOR_GREEN + ";font-weight:600;'>" + res['descricao_beneficio'] + "</div></div>" if res['reducao_pct'] > 0 else ""}
        <div style="border-top:1px solid {COLOR_BORDER};padding-top:0.75rem;margin-top:0.75rem;">
            <div style="color:{COLOR_TEXT_MUTED};font-size:0.8rem;margin-bottom:0.25rem;">Base Legal</div>
            <div style="color:{COLOR_WHITE};font-size:0.9rem;">{res['base_legal']}</div>
        </div>
        {"<div style='border-top:1px solid " + COLOR_BORDER + ";padding-top:0.75rem;margin-top:0.75rem;'><div style='color:" + COLOR_TEXT_MUTED + ";font-size:0.8rem;margin-bottom:0.25rem;'>Descrição NCM</div><div style='color:" + COLOR_WHITE + ";'>" + ncm_descricao + "</div></div>" if ncm_descricao else ""}
    </div>
    """


def _excel_classificacao(df: pd.DataFrame, sheet_name: str = "XClass") -> bytes:
    """Gera bytes de um arquivo Excel com os dados de classificação."""
    buffer = io.BytesIO()
    rename_map = {
        "ncm"                : "NCM",
        "cfop"               : "CFOP",
        "cclasstrib"         : "cClassTrib",
        "regime_iva"         : "Regime IVA",
        "reducao_pct"        : "Redução (%)",
        "ibs_uf_pct"         : "IBS UF (%)",
        "ibs_mun_pct"        : "IBS Municipal (%)",
        "total_ibs_pct"      : "Total IBS (%)",
        "cbs_pct"            : "CBS (%)",
        "total_iva_pct"      : "Total IVA (%)",
        "anexo_beneficio"    : "Anexo LC 214/2025",
        "descricao_beneficio": "Descrição do Benefício",
        "base_legal"         : "Base Legal",
        "origem_classificacao": "Origem",
    }
    df_exp = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_exp.to_excel(writer, index=False, sheet_name=sheet_name)
        # Aba de resumo por regime
        cols_regime = [c for c in ["Regime IVA", "cClassTrib", "Base Legal"] if c in df_exp.columns]
        if cols_regime and "Regime IVA" in df_exp.columns:
            df_resumo = (
                df_exp.groupby(cols_regime, dropna=False)
                .size()
                .reset_index(name="Qtd Itens")
                .sort_values("Qtd Itens", ascending=False)
            )
            df_resumo.to_excel(writer, index=False, sheet_name="Resumo por Regime")
    buffer.seek(0)
    return buffer.read()


# =============================================================================
# MODO 1 — BUSCA MANUAL POR NCM
# =============================================================================
def _render_busca_manual(beneficios_engine, guess_cclasstrib_fn, consulta_ncm_fn, buscar_ncm_fn):
    """Renderiza o modo de busca manual por NCM."""
    st.markdown(
        f"""
        <div style="background:{COLOR_CARD_BG};border:1px solid {COLOR_BORDER};
                    border-radius:10px;padding:1.25rem;margin-bottom:1.5rem;">
            <div style="color:{COLOR_GOLD};font-weight:700;font-size:1rem;margin-bottom:0.5rem;">
                Busca Manual por NCM
            </div>
            <div style="color:{COLOR_TEXT_MUTED};font-size:0.9rem;">
                Digite o NCM do produto e, opcionalmente, o CFOP da operação.
                O sistema retorna o <strong style="color:{COLOR_WHITE};">cClassTrib correto</strong>,
                as alíquotas de <strong style="color:{COLOR_GOLD};">IBS e CBS</strong> e a
                <strong style="color:{COLOR_WHITE};">base legal</strong> fundamentada na LC 214/2025.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ncm, col_cfop, col_btn = st.columns([2, 2, 1])
    with col_ncm:
        ncm_input = st.text_input(
            "NCM (8 dígitos)",
            placeholder="Ex: 04011000",
            key="xclass_ncm_input",
            max_chars=10,
        )
    with col_cfop:
        cfop_input = st.text_input(
            "CFOP (opcional)",
            placeholder="Ex: 5102, 6108, 7101",
            key="xclass_cfop_input",
            max_chars=6,
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        buscar = st.button("Classificar", type="primary", use_container_width=True, key="xclass_buscar")

    if buscar and ncm_input:
        ncm_clean = re.sub(r"\D", "", ncm_input).zfill(8)[:8]
        with st.spinner("Classificando..."):
            res = classificar_item(
                ncm=ncm_clean,
                cfop=cfop_input.strip(),
                beneficios_engine=beneficios_engine,
                guess_cclasstrib_fn=guess_cclasstrib_fn,
                consulta_ncm_fn=consulta_ncm_fn,
            )

        # Buscar descrição NCM
        ncm_descricao = ""
        if buscar_ncm_fn:
            try:
                row = buscar_ncm_fn(ncm_clean)
                if row is not None and not row.empty:
                    ncm_descricao = str(row.get("NCM_DESCRICAO", "")).strip()
            except Exception:
                pass

        st.markdown(_card_resultado(res, ncm_descricao), unsafe_allow_html=True)

        # Exportar resultado único como Excel
        df_single = pd.DataFrame([{**res, "ncm_descricao": ncm_descricao}])
        excel_bytes = _excel_classificacao(df_single, "XClass-NCM")
        st.download_button(
            label="📥 Download Excel",
            data=excel_bytes,
            file_name=f"xclass_ncm_{ncm_clean}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    elif buscar:
        st.warning("Informe o NCM para realizar a classificação.")


# =============================================================================
# MODO 2 — UPLOAD XML NFe EM LOTE
# =============================================================================
def _render_upload_xml(beneficios_engine, guess_cclasstrib_fn, consulta_ncm_fn):
    """Renderiza o modo de upload de XMLs NFe em lote."""
    st.markdown(
        f"""
        <div style="background:{COLOR_CARD_BG};border:1px solid {COLOR_BORDER};
                    border-radius:10px;padding:1.25rem;margin-bottom:1.5rem;">
            <div style="color:{COLOR_GOLD};font-weight:700;font-size:1rem;margin-bottom:0.5rem;">
                Upload XML NFe em Lote
            </div>
            <div style="color:{COLOR_TEXT_MUTED};font-size:0.9rem;">
                Suba um ou mais XMLs de NFe (ou um ZIP com vários).
                O sistema processa cada item, determina o
                <strong style="color:{COLOR_WHITE};">cClassTrib</strong> correto e retorna
                as alíquotas de <strong style="color:{COLOR_GOLD};">IBS e CBS</strong>
                com a <strong style="color:{COLOR_WHITE};">base legal</strong> por item.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Selecione XMLs ou um arquivo ZIP",
        type=["xml", "zip"],
        accept_multiple_files=True,
        key="xclass_xml_upload",
    )

    if not uploaded:
        return

    if st.button("Processar XMLs", type="primary", key="xclass_xml_processar"):
        temp_dir = tempfile.mkdtemp()
        try:
            # Extrair arquivos
            xml_paths = []
            for f in uploaded:
                dest = os.path.join(temp_dir, f.name)
                with open(dest, "wb") as fh:
                    fh.write(f.read())
                if f.name.lower().endswith(".zip"):
                    with zipfile.ZipFile(dest, "r") as zf:
                        zf.extractall(temp_dir)
                    xml_paths += [
                        os.path.join(temp_dir, n)
                        for n in zf.namelist()
                        if n.lower().endswith(".xml")
                    ]
                else:
                    xml_paths.append(dest)

            if not xml_paths:
                st.warning("Nenhum arquivo XML encontrado.")
                return

            # Parsear XMLs
            try:
                from xml_parser import parse_nfe_xml
            except ImportError:
                st.error("Módulo xml_parser não encontrado.")
                return

            linhas = []
            progress = st.progress(0, text="Processando XMLs...")
            total = len(xml_paths)

            for i, path in enumerate(xml_paths):
                progress.progress((i + 1) / total, text=f"Processando {os.path.basename(path)}...")
                try:
                    resultado = parse_nfe_xml(path)
                    nfe_num = resultado.get("numero_nfe", os.path.basename(path))
                    emitente = resultado.get("emitente_nome", "")
                    for item in resultado.get("itens", []):
                        ncm  = re.sub(r"\D", "", str(item.get("ncm", ""))).zfill(8)[:8]
                        cfop = str(item.get("cfop", "")).strip()
                        res  = classificar_item(
                            ncm=ncm, cfop=cfop,
                            beneficios_engine=beneficios_engine,
                            guess_cclasstrib_fn=guess_cclasstrib_fn,
                            consulta_ncm_fn=consulta_ncm_fn,
                        )
                        linhas.append({
                            "NFe"                : nfe_num,
                            "Emitente"           : emitente,
                            "Item"               : item.get("item", ""),
                            "Descrição"          : str(item.get("descricao", ""))[:80],
                            "NCM"                : ncm,
                            "CFOP"               : cfop,
                            "Valor (R$)"         : item.get("valor", 0.0),
                            **{k: res[k] for k in [
                                "cclasstrib", "regime_iva", "reducao_pct",
                                "ibs_uf_pct", "ibs_mun_pct", "total_ibs_pct",
                                "cbs_pct", "total_iva_pct",
                                "anexo_beneficio", "descricao_beneficio", "base_legal",
                            ]},
                        })
                except Exception as e:
                    st.warning(f"Erro ao processar {os.path.basename(path)}: {str(e)[:80]}")

            progress.empty()

            if not linhas:
                st.warning("Nenhum item extraído dos XMLs.")
                return

            df = pd.DataFrame(linhas)

            # KPIs
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total de Itens", len(df))
            k2.metric("Com Benefício Fiscal", int((df["reducao_pct"] > 0).sum()))
            k3.metric("Alíquota Zero", int((df["reducao_pct"] == 100).sum()))
            k4.metric("Redução 60%", int((df["reducao_pct"] == 60).sum()))

            # Tabela
            st.markdown("### Resultado por Item")
            st.dataframe(
                df,
                use_container_width=True,
                height=500,
                column_config={
                    "cclasstrib"         : st.column_config.TextColumn("cClassTrib", width="small"),
                    "regime_iva"         : st.column_config.TextColumn("Regime IVA"),
                    "reducao_pct"        : st.column_config.NumberColumn("Redução (%)", format="%d%%"),
                    "ibs_uf_pct"         : st.column_config.NumberColumn("IBS UF (%)", format="%.4f%%"),
                    "ibs_mun_pct"        : st.column_config.NumberColumn("IBS Mun (%)", format="%.4f%%"),
                    "total_ibs_pct"      : st.column_config.NumberColumn("Total IBS (%)", format="%.4f%%"),
                    "cbs_pct"            : st.column_config.NumberColumn("CBS (%)", format="%.4f%%"),
                    "total_iva_pct"      : st.column_config.NumberColumn("Total IVA (%)", format="%.4f%%"),
                    "base_legal"         : st.column_config.TextColumn("Base Legal", width="large"),
                    "descricao_beneficio": st.column_config.TextColumn("Benefício Fiscal"),
                },
            )

            # Download Excel
            excel_bytes = _excel_classificacao(df, "XClass-XML")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Download Excel — cClassTrib por Item",
                data=excel_bytes,
                file_name=f"xclass_xml_{ts}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# MODO 3 — UPLOAD SPED
# =============================================================================
def _render_upload_sped(beneficios_engine, guess_cclasstrib_fn, consulta_ncm_fn, process_sped_fn):
    """Renderiza o modo de upload de arquivo SPED EFD."""
    st.markdown(
        f"""
        <div style="background:{COLOR_CARD_BG};border:1px solid {COLOR_BORDER};
                    border-radius:10px;padding:1.25rem;margin-bottom:1.5rem;">
            <div style="color:{COLOR_GOLD};font-weight:700;font-size:1rem;margin-bottom:0.5rem;">
                Upload SPED (EFD PIS/COFINS)
            </div>
            <div style="color:{COLOR_TEXT_MUTED};font-size:0.9rem;">
                Suba o arquivo EFD PIS/COFINS (.txt).
                O sistema extrai todos os itens, determina o
                <strong style="color:{COLOR_WHITE};">cClassTrib</strong> correto por linha e retorna
                as alíquotas de <strong style="color:{COLOR_GOLD};">IBS e CBS</strong>
                com a <strong style="color:{COLOR_WHITE};">base legal</strong> fundamentada na LC 214/2025.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sped_file = st.file_uploader(
        "Selecione o arquivo SPED (.txt)",
        type=["txt"],
        key="xclass_sped_upload",
    )

    if not sped_file:
        return

    if st.button("Processar SPED", type="primary", key="xclass_sped_processar"):
        with st.spinner("Lendo e processando o arquivo SPED..."):
            try:
                content = sped_file.read().decode("latin-1", errors="replace")
                df_sped = process_sped_fn(content)
            except Exception as e:
                st.error(f"Erro ao processar o SPED: {str(e)[:200]}")
                return

        if df_sped.empty:
            st.warning("Nenhum dado extraído do arquivo SPED.")
            return

        # Normalizar coluna NCM
        if "NCM" in df_sped.columns and "NCM_DIG" not in df_sped.columns:
            df_sped["NCM_DIG"] = (
                df_sped["NCM"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)
            )

        with st.spinner("Classificando itens..."):
            df_sped = classificar_dataframe(
                df_sped,
                beneficios_engine=beneficios_engine,
                guess_cclasstrib_fn=guess_cclasstrib_fn,
                consulta_ncm_fn=consulta_ncm_fn,
                col_ncm="NCM_DIG",
                col_cfop="CFOP",
            )

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total de Linhas", len(df_sped))
        k2.metric("Com Benefício Fiscal", int((df_sped["reducao_pct"] > 0).sum()))
        k3.metric("Alíquota Zero", int((df_sped["reducao_pct"] == 100).sum()))
        k4.metric("Redução 60%", int((df_sped["reducao_pct"] == 60).sum()))

        # Colunas para exibição
        cols_tela = [c for c in [
            "NCM", "DESCRICAO", "CFOP", "VALOR_TOTAL_VENDAS",
            "cclasstrib", "regime_iva", "reducao_pct",
            "ibs_uf_pct", "ibs_mun_pct", "total_ibs_pct",
            "cbs_pct", "total_iva_pct",
            "descricao_beneficio", "base_legal",
        ] if c in df_sped.columns]

        st.markdown("### Resultado por Linha SPED")
        st.dataframe(
            df_sped[cols_tela],
            use_container_width=True,
            height=500,
            column_config={
                "cclasstrib"         : st.column_config.TextColumn("cClassTrib", width="small"),
                "regime_iva"         : st.column_config.TextColumn("Regime IVA"),
                "reducao_pct"        : st.column_config.NumberColumn("Redução (%)", format="%d%%"),
                "ibs_uf_pct"         : st.column_config.NumberColumn("IBS UF (%)", format="%.4f%%"),
                "ibs_mun_pct"        : st.column_config.NumberColumn("IBS Mun (%)", format="%.4f%%"),
                "total_ibs_pct"      : st.column_config.NumberColumn("Total IBS (%)", format="%.4f%%"),
                "cbs_pct"            : st.column_config.NumberColumn("CBS (%)", format="%.4f%%"),
                "total_iva_pct"      : st.column_config.NumberColumn("Total IVA (%)", format="%.4f%%"),
                "base_legal"         : st.column_config.TextColumn("Base Legal", width="large"),
                "descricao_beneficio": st.column_config.TextColumn("Benefício Fiscal"),
            },
        )

        # Download Excel
        excel_bytes = _excel_classificacao(df_sped, "XClass-SPED")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 Download Excel — cClassTrib por Linha SPED",
            data=excel_bytes,
            file_name=f"xclass_sped_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# =============================================================================
# FUNÇÃO PRINCIPAL — render_aba_xclass
# =============================================================================
def render_aba_xclass(
    beneficios_engine=None,
    guess_cclasstrib_fn=None,
    consulta_ncm_fn=None,
    buscar_ncm_fn=None,
    process_sped_fn=None,
):
    """
    Renderiza a ferramenta XClass completa com os 3 modos de classificação.

    Parâmetros
    ----------
    beneficios_engine : SQLAlchemy Engine
        Engine para consulta na base BDBENEF.
    guess_cclasstrib_fn : callable
        Função guess_cclasstrib do módulo cclasstrib_mapping.
    consulta_ncm_fn : callable
        Função consulta_ncm do módulo beneficios_fiscais.
    buscar_ncm_fn : callable
        Função que busca descrição de um NCM na base TIPI.
    process_sped_fn : callable
        Função process_sped_file do app.py.
    """

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#1A1200,#0D0D0D);
                    border:1px solid {COLOR_GOLD};border-radius:12px;
                    padding:1.5rem 2rem;margin-bottom:1.5rem;">
            <div style="display:flex;align-items:center;gap:1rem;">
                <div style="font-size:2rem;">⚡</div>
                <div>
                    <div style="color:{COLOR_GOLD};font-size:1.4rem;font-weight:900;
                                font-family:'Poppins',sans-serif;letter-spacing:1px;">
                        XClass — Classificador Tributário
                    </div>
                    <div style="color:{COLOR_TEXT_MUTED};font-size:0.9rem;margin-top:0.25rem;">
                        Hub central de classificação IBS/CBS · cClassTrib · Base Legal LC 214/2025
                    </div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;margin-top:1.25rem;">
                <div style="background:rgba(255,221,0,0.08);border-radius:8px;padding:0.75rem;text-align:center;">
                    <div style="color:{COLOR_GOLD};font-size:1.2rem;">🔍</div>
                    <div style="color:{COLOR_WHITE};font-size:0.85rem;font-weight:600;">Busca por NCM</div>
                    <div style="color:{COLOR_TEXT_MUTED};font-size:0.75rem;">Classificação instantânea</div>
                </div>
                <div style="background:rgba(255,221,0,0.08);border-radius:8px;padding:0.75rem;text-align:center;">
                    <div style="color:{COLOR_GOLD};font-size:1.2rem;">📄</div>
                    <div style="color:{COLOR_WHITE};font-size:0.85rem;font-weight:600;">Upload XML NFe</div>
                    <div style="color:{COLOR_TEXT_MUTED};font-size:0.75rem;">Lote de notas fiscais</div>
                </div>
                <div style="background:rgba(255,221,0,0.08);border-radius:8px;padding:0.75rem;text-align:center;">
                    <div style="color:{COLOR_GOLD};font-size:1.2rem;">📊</div>
                    <div style="color:{COLOR_WHITE};font-size:0.85rem;font-weight:600;">Upload SPED</div>
                    <div style="color:{COLOR_TEXT_MUTED};font-size:0.75rem;">EFD PIS/COFINS</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Alíquotas de referência ──────────────────────────────────────────────
    with st.expander("ℹ️ Alíquotas de referência — Ano-teste 2026 (LC 214/2025, Art. 120)"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("IBS Estadual", f"{IBS_UF_REF:.3f}%")
        c2.metric("IBS Municipal", f"{IBS_MUN_REF:.4f}%")
        c3.metric("CBS", f"{CBS_REF:.2f}%")
        c4.metric("Total IVA", f"{IBS_UF_REF + IBS_MUN_REF + CBS_REF:.4f}%")
        st.caption(
            "As alíquotas do período de teste são reduzidas. "
            "As alíquotas plenas entram em vigor progressivamente de 2027 a 2033."
        )

    # ── Tabs dos 3 modos ────────────────────────────────────────────────────
    tab_ncm, tab_xml, tab_sped = st.tabs([
        "🔍 Busca por NCM",
        "📄 Upload XML NFe",
        "📊 Upload SPED",
    ])

    with tab_ncm:
        _render_busca_manual(beneficios_engine, guess_cclasstrib_fn, consulta_ncm_fn, buscar_ncm_fn)

    with tab_xml:
        _render_upload_xml(beneficios_engine, guess_cclasstrib_fn, consulta_ncm_fn)

    with tab_sped:
        _render_upload_sped(beneficios_engine, guess_cclasstrib_fn, consulta_ncm_fn, process_sped_fn)
