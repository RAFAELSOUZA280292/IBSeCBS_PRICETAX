"""
Módulo de Cálculo de Tributação IBS/CBS
========================================

Centraliza toda a lógica de cálculo de tributação para evitar duplicação de código.
"""

from typing import Dict, Optional, Any


def calcular_tributacao_completa(
    ncm: str,
    cfop: str = "5102",
    beneficios_engine: Any = None,
    consulta_ncm_func: Any = None,
    guess_cclasstrib_func: Any = None,
    get_class_info_func: Any = None,
) -> Dict[str, Any]:
    """
    Calcula tributação completa de um NCM baseado em benefícios fiscais.
    
    Esta função centraliza TODA a lógica de cálculo que estava duplicada em 3 abas.
    
    Parâmetros:
        ncm: NCM do produto (8 dígitos)
        cfop: CFOP da operação (padrão: 5102 - venda)
        beneficios_engine: Engine de benefícios fiscais
        consulta_ncm_func: Função de consulta de benefícios
        guess_cclasstrib_func: Função de sugestão de cClassTrib
        get_class_info_func: Função de busca de info de cClassTrib
    
    Retorna:
        Dict com todos os dados calculados:
        {
            'ncm': str,
            'cfop': str,
            'regime': str,
            'ibs_uf': float,
            'ibs_mun': float,
            'cbs': float,
            'total_iva': float,
            'cst': str,
            'cclasstrib_code': str,
            'cclasstrib_desc': str,
            'cclasstrib_msg': str,
            'class_info': dict,
            'beneficios': dict | None,
            'fonte': str,
        }
    """
    # =============================================================================
    # PASSO 1: CONSULTAR BENEFÍCIOS FISCAIS (FONTE DA VERDADE)
    # =============================================================================
    beneficios_info = None
    regime = "TRIBUTACAO_PADRAO"  # Padrão
    ibs_uf = 0.10  # Padrão 2026 (ano teste)
    ibs_mun = 0.0  # Ano teste não tem municipal
    cbs = 0.90  # Padrão 2026 (ano teste)
    fonte = "LC 214/25, regra geral art. 10 e disposiçoes do ADCT art. 125 (ano teste)"
    cst = "000"  # CST padrão
    
    if beneficios_engine and consulta_ncm_func:
        try:
            beneficios_info = consulta_ncm_func(beneficios_engine, ncm)
            
            # APLICAR BENEFÍCIOS (SE HOUVER)
            if beneficios_info and beneficios_info.get('total_enquadramentos', 0) > 0:
                enq = beneficios_info['enquadramentos'][0]
                reducao_pct = enq['reducao_aliquota']
                anexo = enq['anexo']
                
                # Aplicar redução
                if reducao_pct == 100:
                    # Alíquota zero (Cesta Básica Nacional)
                    ibs_uf = 0.0
                    ibs_mun = 0.0
                    cbs = 0.0
                    regime = "ALIQ_ZERO_CESTA_BASICA_NACIONAL"
                    fonte = f"LC 214/25, {anexo}"
                elif reducao_pct == 60:
                    # Redução de 60% (Essencialidade)
                    ibs_uf = 0.04  # 40% de 0,10
                    ibs_mun = 0.0
                    cbs = 0.36  # 40% de 0,90
                    regime = "RED_60_ESSENCIALIDADE"
                    fonte = f"LC 214/25, {anexo}"
                else:
                    # Outras reduções
                    fator = (100 - reducao_pct) / 100
                    ibs_uf = 0.10 * fator
                    ibs_mun = 0.0
                    cbs = 0.90 * fator
                    regime = f"RED_{int(reducao_pct)}"
                    fonte = f"LC 214/25, {anexo}"
                
                print(f"✅ Benefício aplicado: {anexo} ({reducao_pct}% redução)")
            else:
                print(f"ℹ️ Nenhum benefício encontrado - Tributação padrão 1,00%")
                
        except Exception as e:
            print(f"⚠️ Erro ao consultar benefícios: {e}")
    
    # =============================================================================
    # PASSO 2: CALCULAR TOTAL IVA
    # =============================================================================
    total_iva = ibs_uf + ibs_mun + cbs
    
    # =============================================================================
    # PASSO 3: CALCULAR cClassTrib
    # =============================================================================
    cclasstrib_code = ""
    cclasstrib_msg = ""
    class_info = None
    
    if guess_cclasstrib_func:
        cclasstrib_code, cclasstrib_msg = guess_cclasstrib_func(
            cst=cst, cfop=cfop, regime_iva=regime
        )
        
        if get_class_info_func:
            class_info = get_class_info_func(cclasstrib_code)
            
            # Manter descrição original do cClassTrib (não sobrescrever)
            # A descrição oficial do cClassTrib vem do arquivo de classificação tributária
    
    # =============================================================================
    # PASSO 4: RETORNAR RESULTADO COMPLETO
    # =============================================================================
    return {
        'ncm': ncm,
        'cfop': cfop,
        'regime': regime,
        'ibs_uf': ibs_uf,
        'ibs_mun': ibs_mun,
        'cbs': cbs,
        'total_iva': total_iva,
        'cst': cst,
        'cclasstrib_code': cclasstrib_code,
        'cclasstrib_desc': class_info.get('DESC_CLASS', '') if class_info else '',
        'cclasstrib_msg': cclasstrib_msg,
        'class_info': class_info,
        'beneficios': beneficios_info,
        'fonte': fonte,
    }
