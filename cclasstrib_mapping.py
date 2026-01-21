# =============================================================================
# MAPEAMENTO AUTOMÁTICO: cClassTrib por Anexo e % de Redução
# =============================================================================
# Fonte: classificacao_tributaria.xlsx
# Gerado automaticamente a partir da fonte oficial
# Este arquivo é a FONTE DA VERDADE para mapeamento de cClassTrib
# =============================================================================

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
