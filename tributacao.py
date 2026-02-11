"""
PRICETAX - Lógica Tributária IBS/CBS
======================================

Módulo contendo as regras de classificação tributária conforme LC 214/2025.

Autor: PRICETAX
Versão: 4.0
Data: Dezembro 2024
"""

import re
from typing import Any, Optional, Dict


# =============================================================================
# MAPEAMENTO DE CFOPs PARA cClassTrib
# =============================================================================

# Lista de CFOPs que representam operações NÃO ONEROSAS (410999)
# Exemplos: brindes, doações, amostras grátis, remessas para demonstração
CFOP_NAO_ONEROSOS_410999 = [
    "5910", "6910", "7910",  # Remessa em bonificação, doação ou brinde
    "5911", "6911", "7911",  # Remessa de amostra grátis
    "5949", "6949", "7949",  # Outra saída não especificada
    "5917", "6917", "7917",  # Remessa de mercadoria em consignação mercantil ou industrial
]

# Mapeamento fixo: CFOP → cClassTrib
# CFOPs de venda padrão → 000001 (tributação regular)
# CFOPs não onerosos → 410999 (será preenchido automaticamente abaixo)
CFOP_CCLASSTRIB_MAP = {
    # Vendas padrão dentro do estado (tributação regular)
    "5101": "000001",  # Venda de produção do estabelecimento
    "5102": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros
    "5103": "000001",  # Venda de produção do estabelecimento, efetuada fora do estabelecimento
    "5104": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros, efetuada fora do estabelecimento
    "5105": "000001",  # Venda de produção do estabelecimento que não deva por ele transitar
    "5106": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros, que não deva por ele transitar
    "5109": "000001",  # Venda de produção do estabelecimento, destinada à Zona Franca de Manaus ou Áreas de Livre Comércio
    "5110": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros, destinada à Zona Franca de Manaus ou Áreas de Livre Comércio
    "5111": "000001",  # Venda de produção do estabelecimento remetida anteriormente em consignação industrial
    "5112": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros remetida anteriormente em consignação industrial
    "5113": "000001",  # Venda de produção do estabelecimento remetida anteriormente em consignação mercantil
    "5114": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros remetida anteriormente em consignação mercantil
    "5115": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros, recebida anteriormente em consignação mercantil
    "5116": "000001",  # Venda de produção do estabelecimento originada de encomenda para entrega futura
    "5117": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros, originada de encomenda para entrega futura
    "5118": "000001",  # Venda de produção do estabelecimento entregue ao destinatário por conta e ordem do adquirente originário, em venda à ordem
    "5119": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros entregue ao destinatário por conta e ordem do adquirente originário, em venda à ordem
    "5120": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros entregue ao destinatário pelo vendedor remetente, em venda à ordem
    "5122": "000001",  # Venda de produção do estabelecimento remetida para industrialização, por conta e ordem do adquirente, sem transitar pelo estabelecimento do adquirente
    "5123": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros remetida para industrialização, por conta e ordem do adquirente, sem transitar pelo estabelecimento do adquirente
    "5124": "000001",  # Industrialização efetuada para outra empresa
    "5125": "000001",  # Industrialização efetuada para outra empresa quando a mercadoria recebida para utilização no processo de industrialização não transitar pelo estabelecimento adquirente da mercadoria
    
    # Vendas com substituição tributária
    "5401": "000001",  # Venda de produção do estabelecimento em operação com produto sujeito ao regime de substituição tributária
    "5405": "000001",  # Venda de mercadoria adquirida ou recebida de terceiros em operação com mercadoria sujeita ao regime de substituição tributária
    
    # Vendas interestaduais (6xxx) - tributação regular
    "6101": "000001",
    "6102": "000001",
    "6103": "000001",
    "6104": "000001",
    "6105": "000001",
    "6106": "000001",
    "6107": "000001",
    "6108": "000001",
    "6109": "000001",
    "6110": "000001",
    "6111": "000001",
    "6112": "000001",
    "6113": "000001",
    "6114": "000001",
    "6115": "000001",
    "6116": "000001",
    "6117": "000001",
    "6118": "000001",
    "6119": "000001",
    "6120": "000001",
    "6122": "000001",
    "6123": "000001",
    "6124": "000001",
    "6125": "000001",
    "6401": "000001",
    "6403": "000001",
    "6404": "000001",
    "6408": "000001",
    "6409": "000001",
    "6410": "000001",
    "6411": "000001",
    "6412": "000001",
    "6413": "000001",
    "6501": "000001",
    "6502": "000001",
    "6503": "000001",
    "6504": "000001",
    "6505": "000001",
    "6551": "000001",
    "6552": "000001",
    "6553": "000001",
    "6554": "000001",
    "6555": "000001",
    "6556": "000001",
    "6557": "000001",
    "6653": "000001",
    "6654": "000001",
    "6655": "000001",
    "6656": "000001",
    "6657": "000001",
    "6658": "000001",
    "6659": "000001",
    "6660": "000001",
    "6661": "000001",
    "6662": "000001",
    "6663": "000001",
    "6664": "000001",
    "6665": "000001",
    "6666": "000001",
    "6667": "000001",
    "6901": "000001",
    "6902": "000001",
    "6903": "000001",
    "6904": "000001",
    "6905": "000001",
    "6906": "000001",
    "6907": "000001",
    "6908": "000001",
    "6909": "000001",
    "6910": "000001",
    "6911": "000001",
    "6912": "000001",
    "6913": "000001",
    "6914": "000001",
    "6915": "000001",
    "6916": "000001",
    "6917": "000001",
    "6918": "000001",
    "6919": "000001",
    "6920": "000001",
    "6921": "000001",
    "6922": "000001",
    
    # Vendas para exterior (7xxx) - tributação regular
    "7101": "000001",
    "7102": "000001",
    "7105": "000001",
    "7106": "000001",
    "7127": "000001",
}

# Preencher automaticamente CFOPs não onerosos com 410999
for _cfop in CFOP_NAO_ONEROSOS_410999:
    CFOP_CCLASSTRIB_MAP.setdefault(_cfop, "410999")


# =============================================================================
# FUNÇÃO PRINCIPAL: guess_cclasstrib
# =============================================================================

def guess_cclasstrib(cst: Any, cfop: Any, regime_iva: str) -> tuple[str, str]:
    """
    Sugere um código de Classificação Tributária (cClassTrib) para NFe conforme LC 214/2025.
    
    • REGRAS FUNDAMENTAIS (LC 214/2025):
    - cClassTrib NÃO depende do valor da alíquota, e sim da NATUREZA JURÍDICA da operação
    - Série 000xxx → tributação cheia (sem benefício)
    - Série 200xxx → operação onerosa com REDUÇÃO LEGAL
    - Série 410xxx → imunidade, isenção ou não incidência
    
    • ALIMENTOS - Classificação Correta:
    1. Cesta Básica Nacional (Anexo I) → 200003 (redução 100%, alíquota zero)
    2. Cesta Básica Estendida (Anexo VII) → 200034 (redução 60%)
    3. Alimentos sem benefício → 000001 (tributação padrão)
    
    A sugestão é baseada em:
    1. Regime IVA do produto (ALIQ_ZERO_CESTA_BASICA_NACIONAL, RED_60_*, etc)
    2. Mapeamento fixo de CFOPs específicos (via CFOP_CCLASSTRIB_MAP)
    3. Regras genéricas para saídas tributadas (CFOPs 5xxx/6xxx/7xxx + CST normal)
    4. Identificação de operações não onerosas (410999)
    
    Parâmetros:
        cst (Any): Código de Situação Tributária (CST) do produto
        cfop (Any): Código Fiscal de Operações e Prestações (CFOP)
        regime_iva (str): Regime de tributação IVA do produto (CRÍTICO para classificação correta)
    
    Retorna:
        tuple[str, str]: (código_cClassTrib, mensagem_explicativa)
    
    Exemplos:
        - Arroz (Anexo I) + CFOP 5102 → ("200003", "Cesta Básica Nacional - redução 100%")
        - Carne bovina (Anexo VII) + CFOP 5102 → ("200034", "Cesta Estendida - redução 60%")
        - Refrigerante + CFOP 5102 → ("000001", "tributação regular")
        - CFOP 5910 (brinde) → ("410999", "operação não onerosa")
    """
    # Limpar e normalizar entradas
    cst_clean = re.sub(r"\D+", "", str(cst or ""))
    cfop_clean = re.sub(r"\D+", "", str(cfop or ""))
    regime_iva_upper = str(regime_iva or "").upper().strip()

    if not cfop_clean:
        return "", "Informe o CFOP da operação de venda para sugerir o cClassTrib padrão."

    # =========================================================================
    # PRIORIDADE 1: REGIME IVA (baseado na natureza jurídica do produto)
    # =========================================================================
    # Esta é a regra MAIS IMPORTANTE segundo LC 214/2025
    # cClassTrib depende do FUNDAMENTO LEGAL, não da alíquota
    
    # 1.1) Cesta Básica Nacional (Anexo I) - Redução 100% (alíquota zero)
    if "ALIQ_ZERO_CESTA_BASICA_NACIONAL" in regime_iva_upper:
        # [ERRO] ERRO CRÍTICO: usar 000001 para cesta básica
        # [OK] CORRETO: usar 200003 (operação onerosa com redução legal)
        code = "200003"
        msg = (
            f"[OK] Cesta Básica Nacional (Anexo I LC 214/25) → cClassTrib {code}. "
            "Operação onerosa com redução de 100% (alíquota zero). "
            "Fundamento: LC 214/2025, Anexo I."
        )
        return code, msg
    
    # 1.2) Redução 60% (Cesta Estendida - Anexo VII ou Essencialidade)
    if "RED_60" in regime_iva_upper:
        # [ERRO] ERRO CRÍTICO: usar 000001 para produtos com redução 60%
        # [OK] CORRETO: usar 200034 (operação onerosa com redução de 60%)
        code = "200034"
        
        # Identificar se é alimento (Anexo VII) ou essencialidade (arts. 137-145)
        if "ALIMENTO" in regime_iva_upper:
            fundamento = "Anexo VII (Cesta Básica Estendida)"
        else:
            fundamento = "arts. 137 a 145 (essencialidade)"
        
        msg = (
            f"[OK] Redução 60% ({fundamento}) → cClassTrib {code}. "
            "Operação onerosa com redução de 60%. "
            f"Fundamento: LC 214/2025, {fundamento}."
        )
        return code, msg
    
    # 1.3) Outras reduções específicas (se houver)
    # Adicionar aqui se surgirem outros regimes com redução
    
    # =========================================================================
    # PRIORIDADE 2: CFOP específico (operações não onerosas)
    # =========================================================================
    # Regra fixa via mapa (brindes, doações, remessas especiais)
    if cfop_clean in CFOP_CCLASSTRIB_MAP:
        code = CFOP_CCLASSTRIB_MAP[cfop_clean]
        
        # Se for operação não onerosa (410999), explicar claramente
        if code == "410999":
            msg = (
                f"[ATENÇÃO] Operação não onerosa (CFOP {cfop_clean}) → cClassTrib {code}. "
                "Não gera débito de IBS/CBS. "
                "Exemplos: brindes, doações, amostras grátis."
            )
        else:
            msg = (
                f"Regra padrão PRICETAX: CFOP {cfop_clean} → "
                f"cClassTrib {code} (conforme matriz PRICETAX)."
            )
        return code, msg

    # =========================================================================
    # PRIORIDADE 3: Regra genérica para saídas tributadas
    # =========================================================================
    # Saída (5, 6 ou 7) com CST de tributação "normal" → 000001 (tributação padrão)
    if cfop_clean[0] in ("5", "6", "7") and cst_clean in {"000", "200", "201", "202", "900"}:
        code = "000001"
        msg = (
            f"Regra genérica: CFOP {cfop_clean} é saída tributada padrão "
            f"→ cClassTrib {code} (tributação regular sem benefício). "
            "Revise se for operação especial (doação, brinde, bonificação, remessa técnica etc.)."
        )
        return code, msg

    # =========================================================================
    # PRIORIDADE 4: Não conseguiu classificar
    # =========================================================================
    return "", (
        "Não foi possível localizar um cClassTrib padrão para o CFOP informado. "
        "Provável operação especial (devolução, bonificação, remessa, teste, garantia etc.) – revisar manualmente."
    )


# =============================================================================
# FUNÇÃO AUXILIAR: get_class_info_by_code
# =============================================================================

def get_class_info_by_code(code: str) -> Optional[Dict[str, str]]:
    """
    Obtém informações de classificação tributária por código.
    
    Esta função deve ser implementada para buscar detalhes completos
    do cClassTrib em uma base de dados externa (classificacao_tributaria.xlsx).
    
    Args:
        code: Código cClassTrib (ex: "200003", "000001")
    
    Returns:
        Dicionário com informações do código ou None se não encontrado
    """
    # Busca na base classificacao_tributaria.xlsx (implementado no módulo principal)
    return None
