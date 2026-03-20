"""
xclass_engine.py
================
Motor central de classificação tributária da plataforma PRICETAX.

Responsabilidades:
    - Determinar o cClassTrib correto para qualquer combinação NCM + CFOP
    - Calcular alíquotas efetivas de IBS (UF + Municipal) e CBS
    - Retornar base legal fundamentada na LC 214/2025
    - Ser reutilizado pelos 3 modos da ferramenta XClass:
        1. Busca manual por NCM
        2. Upload de XMLs NFe em lote
        3. Upload de SPED PIS/COFINS

Autor: PRICETAX — Inteligência Tributária para a Reforma
Atualizado: 2026-03
"""

from __future__ import annotations
from typing import Optional


# =============================================================================
# CONSTANTES — Alíquotas de referência (ano-teste 2026, LC 214/2025, Art. 120)
# =============================================================================
IBS_UF_REF   = 0.10    # 0,10% IBS Estadual
IBS_MUN_REF  = 0.025   # 0,025% IBS Municipal
CBS_REF      = 0.90    # 0,90% CBS


# =============================================================================
# MAPEAMENTO REGIME → BASE LEGAL (LC 214/2025)
# =============================================================================
BASE_LEGAL_MAP: dict[str, str] = {
    "ALIQ_ZERO_CESTA_BASICA_NACIONAL" : "LC 214/2025, Anexo I — Cesta Básica Nacional (alíquota zero, Art. 21 § 3º)",
    "RED_60_ESSENCIALIDADE"           : "LC 214/2025, Art. 21, § 1º — Redução de 60% (saúde, educação, essenciais)",
    "RED_60"                          : "LC 214/2025, Art. 21, § 1º — Redução de 60%",
    "RED_30"                          : "LC 214/2025, Art. 21, § 2º — Redução de 30% (Cesta Estendida)",
    "TRIBUTACAO_PADRAO"               : "LC 214/2025, Art. 20 — Tributação integral (alíquota cheia)",
    "MONOFASICO"                      : "LC 214/2025, Art. 42 a 57 — Regime Monofásico",
    "REGIME_ESPECIAL"                 : "LC 214/2025, Art. 165 a 185 — Regimes Especiais",
    "ISENCAO"                         : "LC 214/2025, Art. 21, § 3º — Isenção / Não Incidência",
    "EXPORTACAO"                      : "LC 214/2025, Art. 18 — Exportações (alíquota zero)",
    "DIFERIMENTO"                     : "LC 214/2025, Art. 58 a 62 — Diferimento",
    "IMUNIDADE"                       : "CF/1988, Art. 150, VI + LC 214/2025, Art. 21, § 4º — Imunidade",
}

# Prefixos para fallback quando o regime contém sufixo de anexo
_BASE_LEGAL_PREFIXOS: dict[str, str] = {
    "ALIQ_ZERO"   : "LC 214/2025, Anexo I — Cesta Básica Nacional (alíquota zero)",
    "RED_60"      : "LC 214/2025, Art. 21, § 1º — Redução de 60%",
    "RED_30"      : "LC 214/2025, Art. 21, § 2º — Redução de 30%",
    "RED_100"     : "LC 214/2025, Anexo I — Alíquota zero (Cesta Básica Nacional)",
    "MONOFASICO"  : "LC 214/2025, Art. 42 a 57 — Regime Monofásico",
    "EXPORTACAO"  : "LC 214/2025, Art. 18 — Exportações (alíquota zero)",
    "DIFERIMENTO" : "LC 214/2025, Art. 58 a 62 — Diferimento",
    "ISENCAO"     : "LC 214/2025, Art. 21, § 3º — Isenção / Não Incidência",
    "IMUNIDADE"   : "CF/1988, Art. 150, VI — Imunidade",
}


def _resolver_base_legal(regime: str, anexo: str = "") -> str:
    """Resolve a base legal a partir do regime e do anexo do benefício."""
    base = BASE_LEGAL_MAP.get(regime)
    if base:
        if anexo and "Anexo" not in base:
            base = f"{base} ({anexo})"
        return base

    # Fallback por prefixo
    for prefixo, texto in _BASE_LEGAL_PREFIXOS.items():
        if regime.startswith(prefixo):
            if anexo and "Anexo" not in texto:
                texto = f"{texto} ({anexo})"
            return texto

    return "LC 214/2025 — Consulte o regime específico para fundamentação legal"


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================
def classificar_item(
    ncm: str,
    cfop: str = "",
    beneficios_engine=None,
    guess_cclasstrib_fn=None,
    consulta_ncm_fn=None,
) -> dict:
    """
    Classifica um item fiscal retornando cClassTrib, alíquotas IBS/CBS e base legal.

    Parâmetros
    ----------
    ncm : str
        Código NCM do produto (8 dígitos).
    cfop : str, optional
        Código CFOP da operação. Quando informado, aplica a lógica de priorização:
        CFOP de remessa tem precedência sobre a classificação pelo NCM.
    beneficios_engine : SQLAlchemy Engine, optional
        Engine de conexão com a base BDBENEF (benefícios fiscais LC 214/2025).
    guess_cclasstrib_fn : callable, optional
        Função `guess_cclasstrib(cst, cfop, regime_iva)` do módulo cclasstrib_mapping.
    consulta_ncm_fn : callable, optional
        Função `consulta_ncm(engine, ncm)` do módulo beneficios_fiscais.

    Retorna
    -------
    dict com as chaves:
        ncm, cfop, cclasstrib, regime_iva, reducao_pct,
        ibs_uf_pct, ibs_mun_pct, total_ibs_pct,
        cbs_pct, total_iva_pct,
        anexo_beneficio, descricao_beneficio, base_legal,
        origem_classificacao
    """
    ncm_dig = str(ncm).strip().replace(".", "").replace("-", "").zfill(8)[:8]
    cfop_str = str(cfop).strip() if cfop else ""

    # Valores padrão — tributação integral
    regime          = "TRIBUTACAO_PADRAO"
    ibs_uf          = IBS_UF_REF
    ibs_mun         = IBS_MUN_REF
    cbs             = CBS_REF
    reducao_pct     = 0
    anexo_beneficio = ""
    descr_beneficio = "Tributação integral — sem benefício fiscal identificado"
    origem          = "padrão"

    # ── 1. Consultar base de benefícios fiscais (BDBENEF) ──────────────────
    if beneficios_engine and consulta_ncm_fn and ncm_dig:
        try:
            resultado = consulta_ncm_fn(beneficios_engine, ncm_dig)
            if resultado.get("total_enquadramentos", 0) > 0:
                enq             = resultado["enquadramentos"][0]
                reducao         = int(enq.get("reducao_aliquota", 0))
                anexo_beneficio = enq.get("anexo", "")
                descr_beneficio = enq.get("descricao_anexo", "")
                reducao_pct     = reducao
                origem          = "BDBENEF"

                fator   = (100 - reducao) / 100
                ibs_uf  = round(IBS_UF_REF  * fator, 6)
                ibs_mun = round(IBS_MUN_REF * fator, 6)
                cbs     = round(CBS_REF     * fator, 6)

                if reducao == 100:
                    regime = "ALIQ_ZERO_CESTA_BASICA_NACIONAL"
                elif reducao == 60:
                    regime = f"RED_60_{anexo_beneficio}" if anexo_beneficio else "RED_60_ESSENCIALIDADE"
                else:
                    regime = f"RED_{reducao}"
        except Exception:
            pass

    # ── 2. Determinar cClassTrib (prioridade: CFOP remessa > NCM) ──────────
    cclasstrib = "000000"
    if guess_cclasstrib_fn:
        try:
            code, _ = guess_cclasstrib_fn(cst="", cfop=cfop_str, regime_iva=regime)
            cclasstrib = code
        except Exception:
            pass

    # ── 3. Resolver base legal ─────────────────────────────────────────────
    base_legal = _resolver_base_legal(regime, anexo_beneficio)

    # ── 4. Totais ──────────────────────────────────────────────────────────
    total_ibs = round(ibs_uf + ibs_mun, 6)
    total_iva = round(total_ibs + cbs, 6)

    return {
        "ncm"                : ncm_dig,
        "cfop"               : cfop_str,
        "cclasstrib"         : cclasstrib,
        "regime_iva"         : regime,
        "reducao_pct"        : reducao_pct,
        "ibs_uf_pct"         : ibs_uf,
        "ibs_mun_pct"        : ibs_mun,
        "total_ibs_pct"      : total_ibs,
        "cbs_pct"            : cbs,
        "total_iva_pct"      : total_iva,
        "anexo_beneficio"    : anexo_beneficio,
        "descricao_beneficio": descr_beneficio,
        "base_legal"         : base_legal,
        "origem_classificacao": origem,
    }


def classificar_dataframe(df, beneficios_engine, guess_cclasstrib_fn, consulta_ncm_fn,
                          col_ncm: str = "NCM_DIG", col_cfop: str = "CFOP"):
    """
    Aplica `classificar_item` a cada linha de um DataFrame e retorna o DataFrame enriquecido.

    Parâmetros
    ----------
    df : pd.DataFrame
        DataFrame com pelo menos as colunas `col_ncm` e `col_cfop`.
    col_ncm : str
        Nome da coluna com o NCM (8 dígitos).
    col_cfop : str
        Nome da coluna com o CFOP.

    Retorna
    -------
    pd.DataFrame com colunas adicionais de classificação tributária.
    """
    import pandas as pd

    cols_resultado = [
        "cclasstrib", "regime_iva", "reducao_pct",
        "ibs_uf_pct", "ibs_mun_pct", "total_ibs_pct",
        "cbs_pct", "total_iva_pct",
        "anexo_beneficio", "descricao_beneficio", "base_legal",
        "origem_classificacao",
    ]

    def _linha(row):
        ncm  = row.get(col_ncm, "")
        cfop = row.get(col_cfop, "")
        res  = classificar_item(
            ncm=ncm, cfop=cfop,
            beneficios_engine=beneficios_engine,
            guess_cclasstrib_fn=guess_cclasstrib_fn,
            consulta_ncm_fn=consulta_ncm_fn,
        )
        return pd.Series({c: res[c] for c in cols_resultado})

    df[cols_resultado] = df.apply(_linha, axis=1)
    return df
