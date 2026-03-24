"""
Arquivo de mapeamento de dados para o cClassTrib.

Contém o dicionário `CCLASSTRIB_MAP_BY_ANEXO` e a função `get_cclasstrib_by_anexo`
para mapear a combinação de Anexo da LC 214/2025 e percentual de redução
para o código cClassTrib correspondente.

Autor: RDI
Data: 17/03/2026
"""

"""
Mapeamento de cClassTrib baseado em:
1. % de Redução (IBS/CBS)
2. Anexo da LC 214/2025

Uso:
    from cclasstrib_mapping import get_cclasstrib_by_anexo
    
    code = get_cclasstrib_by_anexo(reducao=60, anexo="ANEXO_XI")
    # Retorna: 200043
"""

# =============================================================================
# MAPEAMENTO PRINCIPAL: (Redução%, Anexo) → cClassTrib
# =============================================================================

CCLASSTRIB_MAP_BY_ANEXO = {
    # Redução 100% (Alíquota Zero)
    (100, "ANEXO_I"): 200003,      # Cesta Básica Nacional
    (100, "ANEXO_XII"): 200004,    # Dispositivos Médicos (alíquota zero)
    (100, "ANEXO_IV"): 200005,     # Dispositivos Médicos (admin pública)
    (100, "ANEXO_XIII"): 200007,   # Acessibilidade
    (100, "ANEXO_V"): 200008,      # Acessibilidade (admin pública)
    (100, "ANEXO_XIV"): 200009,    # Medicamentos
    (100, "ANEXO_VI"): 200011,     # Nutrição enteral/parenteral (admin pública)
    (100, "ANEXO_XV"): 200014,     # Hortícolas, frutas e ovos
    
    # Redução 60%
    (60, "ANEXO_II"): 200028,      # Educação
    (60, "ANEXO_III"): 200029,     # Saúde humana
    (60, "ANEXO_IV"): 200030,      # Dispositivos Médicos (redução 60%)
    (60, "ANEXO_V"): 200031,       # Acessibilidade (redução 60%)
    (60, "ANEXO_VI"): 200033,      # Nutrição enteral/parenteral
    (60, "ANEXO_VII"): 200034,     # Alimentos (Cesta Estendida)
    (60, "ANEXO_VIII"): 200035,    # Higiene e limpeza
    (60, "ANEXO_IX"): 200038,      # Insumos agropecuários
    (60, "ANEXO_X"): 200039,       # Produções audiovisuais nacionais
    (60, "ANEXO_XI"): 200043,      # Soberania e Segurança Nacional
}

# =============================================================================
# MAPEAMENTO ESPECIAL: ANEXO XI tem 2 cClassTribs diferentes
# =============================================================================

ANEXO_XI_SPECIAL = {
    "soberania": 200043,                    # Bens/serviços relativos à soberania
    "segurança cibernética": 200044,        # Segurança da informação/cibernética
    "segurança da informação": 200044,      # Segurança da informação/cibernética
}

# =============================================================================
# FUNÇÕES DE MAPEAMENTO
# =============================================================================

def get_cclasstrib_by_anexo(reducao: int, anexo: str, descricao: str = "") -> tuple[str, str]:
    """
    Retorna cClassTrib baseado em redução e anexo.
    
    Args:
        reducao: % de redução (60, 100, etc)
        anexo: Anexo da LC 214/2025 (ex: "ANEXO_XI", "ANEXO_VII")
        descricao: Descrição do benefício (usado para casos especiais como ANEXO XI)
    
    Returns:
        tuple: (código_cClassTrib, mensagem_explicativa)
    
    Exemplos:
        >>> get_cclasstrib_by_anexo(60, "ANEXO_VII")
        ("200034", "Anexo VII - Alimentos (Cesta Estendida)")
        
        >>> get_cclasstrib_by_anexo(60, "ANEXO_XI", "soberania")
        ("200043", "Anexo XI - Soberania e Segurança Nacional")
        
        >>> get_cclasstrib_by_anexo(60, "ANEXO_XI", "segurança cibernética")
        ("200044", "Anexo XI - Segurança da Informação/Cibernética")
    """
    # Normalizar formato do anexo: "ANEXO IX" → "ANEXO_IX" (engine retorna com espaço)
    if anexo and ' ' in anexo:
        anexo = anexo.replace(' ', '_')

    # Caso especial: ANEXO XI tem 2 cClassTribs
    if anexo == "ANEXO_XI" and descricao:
        desc_lower = descricao.lower()
        for keyword, code in ANEXO_XI_SPECIAL.items():
            if keyword in desc_lower:
                if code == 200043:
                    return str(code), "Anexo XI - Soberania e Segurança Nacional"
                else:
                    return str(code), "Anexo XI - Segurança da Informação/Cibernética"
    
    # Mapeamento padrão
    key = (reducao, anexo)
    if key in CCLASSTRIB_MAP_BY_ANEXO:
        code = CCLASSTRIB_MAP_BY_ANEXO[key]
        
        # Mensagens específicas por anexo
        anexo_names = {
            "ANEXO_I": "Cesta Básica Nacional",
            "ANEXO_II": "Educação",
            "ANEXO_III": "Saúde Humana",
            "ANEXO_IV": "Dispositivos Médicos",
            "ANEXO_V": "Acessibilidade",
            "ANEXO_VI": "Nutrição Enteral/Parenteral",
            "ANEXO_VII": "Alimentos (Cesta Estendida)",
            "ANEXO_VIII": "Higiene e Limpeza",
            "ANEXO_IX": "Insumos Agropecuários",
            "ANEXO_X": "Produções Audiovisuais Nacionais",
            "ANEXO_XI": "Soberania e Segurança Nacional",
            "ANEXO_XII": "Dispositivos Médicos (Alíquota Zero)",
            "ANEXO_XIII": "Acessibilidade (Alíquota Zero)",
            "ANEXO_XIV": "Medicamentos",
            "ANEXO_XV": "Hortícolas, Frutas e Ovos",
        }
        
        anexo_name = anexo_names.get(anexo, anexo)
        msg = f"{anexo} - {anexo_name} (Redução {reducao}%)"
        
        return str(code), msg
    
    # Fallback: não encontrado
    return "", f"Mapeamento não encontrado para Redução {reducao}% + {anexo}"


# =============================================================================
# MAPEAMENTO POR NCM: NCMs com múltiplos cClassTribs possíveis
# Estrutura: NCM -> lista de opções, cada opção tem:
#   - code: código cClassTrib
#   - descricao: descrição do produto/situação
#   - base_legal: artigo da LC 214/2025
#   - ambiguo: True se o NCM tem múltiplos códigos possíveis
# =============================================================================

NCM_MULTI_CCLASSTRIB_MAP = {
    # -------------------------------------------------------------------------
    # NCM 27101259 - Gasolina e suas correntes / Misturas EAC
    # Monofásico - múltiplos cClassTribs dependendo da situação
    # -------------------------------------------------------------------------
    "27101259": [
        {
            "code": "620001",
            "descricao": "Gasolina e suas correntes",
            "situacao": "Tributação monofásica padrão sobre combustíveis",
            "base_legal": "Art. 172 e Art. 179, I da LC 214/2025",
            "regime": "MONOFASICO_COMBUSTIVEL",
        },
        {
            "code": "620004",
            "descricao": "Mistura de EAC com gasolina A em percentual SUPERIOR ao obrigatório",
            "situacao": "Percentual de álcool etílico anidro combustível (EAC) acima do mínimo legal",
            "base_legal": "Art. 179 da LC 214/2025",
            "regime": "MONOFASICO_COMBUSTIVEL",
        },
        {
            "code": "620005",
            "descricao": "Mistura de EAC com gasolina A em percentual INFERIOR ao obrigatório",
            "situacao": "Percentual de álcool etílico anidro combustível (EAC) abaixo do mínimo legal",
            "base_legal": "Art. 179 da LC 214/2025",
            "regime": "MONOFASICO_COMBUSTIVEL",
        },
        {
            "code": "620006",
            "descricao": "Tributação monofásica sobre combustíveis cobrada anteriormente",
            "situacao": "Operação downstream — tributo já recolhido na etapa anterior da cadeia",
            "base_legal": "Art. 180 da LC 214/2025",
            "regime": "MONOFASICO_COMBUSTIVEL",
        },
    ],

    # -------------------------------------------------------------------------
    # NCM 27101921 - Óleo diesel e suas correntes
    # Monofásico - 2 situações possíveis
    # -------------------------------------------------------------------------
    "27101921": [
        {
            "code": "620001",
            "descricao": "Óleo diesel e suas correntes",
            "situacao": "Tributação monofásica padrão sobre combustíveis",
            "base_legal": "Art. 172 e Art. 179, I da LC 214/2025",
            "regime": "MONOFASICO_COMBUSTIVEL",
        },
        {
            "code": "620006",
            "descricao": "Tributação monofásica sobre combustíveis cobrada anteriormente",
            "situacao": "Operação downstream — tributo já recolhido na etapa anterior da cadeia",
            "base_legal": "Art. 180 da LC 214/2025",
            "regime": "MONOFASICO_COMBUSTIVEL",
        },
    ],

    # -------------------------------------------------------------------------
    # NCM 84212990 - Filtros médicos (dispositivos do Anexo IV)
    # 2 cClassTribs dependendo do DESTINATÁRIO
    # -------------------------------------------------------------------------
    "84212990": [
        {
            "code": "200030",
            "descricao": "Dispositivos médicos do Anexo IV — venda para mercado geral",
            "situacao": "Destinatário é empresa privada ou pessoa física (mercado geral)",
            "base_legal": "Art. 131 da LC 214/2025 — Anexo IV",
            "regime": "RED_60_DISPOSITIVOS_MEDICOS",
            "produtos": [
                "Filtro de linha arterial e venoso",
                "Filtro de sangue arterial e venoso para recirculação",
                "Filtro para cardioplegia",
            ],
        },
        {
            "code": "200005",
            "descricao": "Dispositivos médicos do Anexo IV — venda para órgão público ou entidade imune",
            "situacao": "Destinatário é órgão da administração pública direta, autarquia, fundação pública ou entidade de saúde imune",
            "base_legal": "Art. 144 da LC 214/2025 — Anexo IV",
            "regime": "ALIQ_ZERO_DISPOSITIVOS_MEDICOS_PUBLICO",
            "produtos": [
                "Filtro de linha arterial e venoso",
                "Filtro de sangue arterial e venoso para recirculação",
                "Filtro para cardioplegia",
            ],
        },
    ],

    # -------------------------------------------------------------------------
    # NCM 31052000 - Fertilizantes (adubos) - Anexo IX / Diferimento
    # 2 cClassTribs: insumo agropecário (200038) ou diferimento (515001)
    # -------------------------------------------------------------------------
    "31052000": [
        {
            "code": "200038",
            "descricao": "Fertilizantes (adubos) — Insumo agropecário do Anexo IX",
            "situacao": "Fornecimento dos insumos agropecários e aquícolas relacionados no Anexo IX da LC 214/2025, em conformidade com as definições e demais requisitos da legislação específica",
            "base_legal": "LC 214/2025, Anexo IX — Art. 138",
            "regime": "INSUMO_AGROPECUARIO_ANEXO_IX",
        },
        {
            "code": "515001",
            "descricao": "Fertilizantes (adubos) — Diferimento (insumo agropecário)",
            "situacao": "Operações, sujeitas a diferimento, com insumos agropecários e aquícolas, observado o art. 138 da LC 214, de 2025",
            "base_legal": "LC 214/2025, Art. 138 — Diferimento",
            "regime": "DIFERIMENTO_INSUMO_AGROPECUARIO",
        },
    ],

    # -------------------------------------------------------------------------
    # NCMs com tributação integral padrão (000001) — sem ambiguidade
    # -------------------------------------------------------------------------
    "27101932": [
        {
            "code": "000001",
            "descricao": "Tributação integral pelo IBS e CBS",
            "situacao": "Operação tributada integralmente, sem benefício fiscal",
            "base_legal": "LC 214/2025 — alíquota padrão",
            "regime": "TRIBUTACAO_PADRAO",
        },
    ],
    "76169900": [
        {
            "code": "000001",
            "descricao": "Tributação integral pelo IBS e CBS",
            "situacao": "Operação tributada integralmente, sem benefício fiscal",
            "base_legal": "LC 214/2025 — alíquota padrão",
            "regime": "TRIBUTACAO_PADRAO",
        },
    ],
    "84138100": [
        {
            "code": "000001",
            "descricao": "Tributação integral pelo IBS e CBS",
            "situacao": "Operação tributada integralmente, sem benefício fiscal",
            "base_legal": "LC 214/2025 — alíquota padrão",
            "regime": "TRIBUTACAO_PADRAO",
        },
    ],
    "84212300": [
        {
            "code": "000001",
            "descricao": "Tributação integral pelo IBS e CBS",
            "situacao": "Operação tributada integralmente, sem benefício fiscal",
            "base_legal": "LC 214/2025 — alíquota padrão",
            "regime": "TRIBUTACAO_PADRAO",
        },
    ],
    "84219999": [
        {
            "code": "000001",
            "descricao": "Tributação integral pelo IBS e CBS",
            "situacao": "Operação tributada integralmente, sem benefício fiscal",
            "base_legal": "LC 214/2025 — alíquota padrão",
            "regime": "TRIBUTACAO_PADRAO",
        },
    ],
    "84818099": [
        {
            "code": "000001",
            "descricao": "Tributação integral pelo IBS e CBS",
            "situacao": "Operação tributada integralmente, sem benefício fiscal",
            "base_legal": "LC 214/2025 — alíquota padrão",
            "regime": "TRIBUTACAO_PADRAO",
        },
    ],
}


def get_opcoes_cclasstrib_por_ncm(ncm: str) -> list:
    """
    Retorna lista de opções de cClassTrib para um NCM.
    
    Se o NCM tiver múltiplas opções, retorna todas para o usuário escolher.
    Se tiver apenas uma opção, retorna lista com um elemento.
    Se não estiver mapeado, retorna lista vazia.
    
    Args:
        ncm: Código NCM (8 dígitos)
        
    Returns:
        Lista de dicts com code, descricao, situacao, base_legal, regime
    """
    import re
    ncm_clean = re.sub(r'\D+', '', str(ncm)).zfill(8)[:8]
    return NCM_MULTI_CCLASSTRIB_MAP.get(ncm_clean, [])


def ncm_tem_multiplos_cclasstrib(ncm: str) -> bool:
    """
    Verifica se um NCM tem múltiplos cClassTribs possíveis.
    
    Args:
        ncm: Código NCM (8 dígitos)
        
    Returns:
        True se houver mais de uma opção de cClassTrib para o NCM
    """
    opcoes = get_opcoes_cclasstrib_por_ncm(ncm)
    return len(opcoes) > 1


def get_cclasstrib_padrao_por_ncm(ncm: str) -> tuple:
    """
    Retorna o cClassTrib padrão (primeira opção) para um NCM.
    Usado no processamento em lote quando não há interação com o usuário.
    
    Args:
        ncm: Código NCM (8 dígitos)
        
    Returns:
        tuple: (code, descricao, base_legal, ambiguo)
        - ambiguo=True indica que o NCM tem múltiplas opções e requer revisão manual
    """
    opcoes = get_opcoes_cclasstrib_por_ncm(ncm)
    if not opcoes:
        return None, None, None, False
    
    primeira = opcoes[0]
    ambiguo = len(opcoes) > 1
    return (
        primeira['code'],
        primeira['descricao'],
        primeira['base_legal'],
        ambiguo
    )


def validate_cclasstrib(code: str, cclasstrib_index: dict) -> bool:
    """
    Valida se um cClassTrib existe no índice oficial.
    
    Args:
        code: Código cClassTrib a validar
        cclasstrib_index: Índice de cClassTribs do arquivo oficial
    
    Returns:
        bool: True se o código existe, False caso contrário
    """
    return str(code).strip() in cclasstrib_index
