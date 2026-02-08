"""
PRICETAX - Módulo de Validações
================================

Funções para validar entradas de dados (NCM, CFOP, CNPJ, etc.)
com mensagens de erro claras e profissionais.

Autor: PRICETAX
Data: 08/02/2026
"""

import re
from typing import Tuple, Optional


def validar_ncm(ncm: str) -> Tuple[bool, str]:
    """
    Valida código NCM (Nomenclatura Comum do Mercosul).
    
    Args:
        ncm: Código NCM a ser validado
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if not ncm or not ncm.strip():
        return False, "NCM não pode ser vazio"
    
    ncm_limpo = ncm.strip().replace(".", "").replace("-", "")
    
    if not ncm_limpo.isdigit():
        return False, "NCM deve conter apenas números"
    
    if len(ncm_limpo) != 8:
        return False, f"NCM deve ter 8 dígitos (informado: {len(ncm_limpo)})"
    
    return True, ""


def validar_cfop(cfop: str) -> Tuple[bool, str]:
    """
    Valida código CFOP (Código Fiscal de Operações e Prestações).
    
    Args:
        cfop: Código CFOP a ser validado
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if not cfop or not cfop.strip():
        return True, ""  # CFOP é opcional
    
    cfop_limpo = cfop.strip().replace(".", "")
    
    if not cfop_limpo.isdigit():
        return False, "CFOP deve conter apenas números"
    
    if len(cfop_limpo) != 4:
        return False, f"CFOP deve ter 4 dígitos (informado: {len(cfop_limpo)})"
    
    # Validar primeiro dígito (1-7)
    primeiro_digito = int(cfop_limpo[0])
    if primeiro_digito < 1 or primeiro_digito > 7:
        return False, f"CFOP inválido: primeiro dígito deve ser entre 1 e 7"
    
    return True, ""


def validar_cnpj(cnpj: str) -> Tuple[bool, str]:
    """
    Valida CNPJ (Cadastro Nacional da Pessoa Jurídica).
    
    Args:
        cnpj: CNPJ a ser validado
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if not cnpj or not cnpj.strip():
        return False, "CNPJ não pode ser vazio"
    
    # Remover caracteres especiais
    cnpj_limpo = re.sub(r'[^0-9]', '', cnpj.strip())
    
    if len(cnpj_limpo) != 14:
        return False, f"CNPJ deve ter 14 dígitos (informado: {len(cnpj_limpo)})"
    
    # Verificar se todos os dígitos são iguais (CNPJ inválido)
    if cnpj_limpo == cnpj_limpo[0] * 14:
        return False, "CNPJ inválido: todos os dígitos são iguais"
    
    return True, ""


def validar_cclass_trib(cclass_trib: str) -> Tuple[bool, str]:
    """
    Valida código cClassTrib (Classificação Tributária IBS/CBS).
    
    Args:
        cclass_trib: Código cClassTrib a ser validado
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if not cclass_trib or not cclass_trib.strip():
        return False, "cClassTrib não pode ser vazio"
    
    cclass_limpo = cclass_trib.strip()
    
    # Formato esperado: XX.YY.ZZ (ex: 01.01.00)
    if not re.match(r'^\d{2}\.\d{2}\.\d{2}$', cclass_limpo):
        return False, "cClassTrib deve estar no formato XX.YY.ZZ (ex: 01.01.00)"
    
    return True, ""


def validar_aliquota(aliquota: str) -> Tuple[bool, str]:
    """
    Valida alíquota (percentual).
    
    Args:
        aliquota: Alíquota a ser validada
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if not aliquota or not aliquota.strip():
        return False, "Alíquota não pode ser vazia"
    
    try:
        valor = float(aliquota.strip().replace(",", "."))
        
        if valor < 0:
            return False, "Alíquota não pode ser negativa"
        
        if valor > 100:
            return False, "Alíquota não pode ser maior que 100%"
        
        return True, ""
    
    except ValueError:
        return False, "Alíquota deve ser um número válido"


def validar_valor_monetario(valor: str) -> Tuple[bool, str]:
    """
    Valida valor monetário.
    
    Args:
        valor: Valor monetário a ser validado
        
    Returns:
        Tupla (válido, mensagem_erro)
    """
    if not valor or not valor.strip():
        return False, "Valor não pode ser vazio"
    
    try:
        # Remover R$ e espaços
        valor_limpo = valor.strip().replace("R$", "").replace(" ", "")
        # Substituir vírgula por ponto
        valor_limpo = valor_limpo.replace(".", "").replace(",", ".")
        
        valor_float = float(valor_limpo)
        
        if valor_float < 0:
            return False, "Valor não pode ser negativo"
        
        return True, ""
    
    except ValueError:
        return False, "Valor monetário inválido"
