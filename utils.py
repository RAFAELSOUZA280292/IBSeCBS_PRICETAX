"""
PRICETAX - Funções Utilitárias
================================

Módulo contendo funções auxiliares para formatação, conversão e manipulação de dados.

Autor: PRICETAX
Versão: 4.0
Data: Dezembro 2024
"""

from typing import Optional
import re


def only_digits(s: Optional[str]) -> str:
    """
    Remove todos os caracteres não numéricos de uma string.
    
    Útil para limpar NCMs, CFOPs, CNPJs, etc que podem vir formatados.
    
    Args:
        s: String de entrada (pode ser None)
    
    Returns:
        String contendo apenas dígitos (0-9)
    
    Exemplos:
        >>> only_digits("1234.56.78")
        '12345678'
        >>> only_digits("NCM: 0201.10.00")
        '02011000'
        >>> only_digits(None)
        ''
    """
    return re.sub(r"\D+", "", s or "")


def to_float_br(s) -> float:
    """
    Converte string no formato brasileiro para float.
    
    Aceita formatos como:
    - "1.234,56" → 1234.56
    - "1234,56" → 1234.56
    - "1234.56" → 1234.56
    - "12%" → 0.12
    
    Args:
        s: Valor a ser convertido (string, int, float)
    
    Returns:
        Valor convertido para float (0.0 em caso de erro)
    
    Exemplos:
        >>> to_float_br("1.234,56")
        1234.56
        >>> to_float_br("12%")
        0.12
        >>> to_float_br("abc")
        0.0
    """
    if isinstance(s, (int, float)):
        return float(s)
    
    s_clean = str(s or "").strip()
    
    # Remover símbolo de percentual e converter
    if "%" in s_clean:
        s_clean = s_clean.replace("%", "")
        try:
            return float(s_clean.replace(",", ".")) / 100.0
        except ValueError:
            return 0.0
    
    # Formato brasileiro: 1.234,56 → 1234.56
    if "," in s_clean and "." in s_clean:
        s_clean = s_clean.replace(".", "").replace(",", ".")
    # Apenas vírgula: 1234,56 → 1234.56
    elif "," in s_clean:
        s_clean = s_clean.replace(",", ".")
    
    try:
        return float(s_clean)
    except ValueError:
        return 0.0


def pct_str(v: float) -> str:
    """
    Formata um número como percentual no padrão brasileiro.
    
    Args:
        v: Valor decimal (ex: 0.12 para 12%)
    
    Returns:
        String formatada como percentual (ex: "12,00%")
    
    Exemplos:
        >>> pct_str(0.12)
        '12,00%'
        >>> pct_str(0.6)
        '60,00%'
        >>> pct_str(1.0)
        '100,00%'
    """
    return f"{v * 100:.2f}%".replace(".", ",")


def competencia_from_dt(dt_ini: str, dt_fin: str) -> str:
    """
    Extrai competência (MM/AAAA) a partir das datas do registro 0000 do SPED.
    
    Args:
        dt_ini: Data inicial no formato DDMMAAAA
        dt_fin: Data final no formato DDMMAAAA
    
    Returns:
        Competência no formato "MM/AAAA" ou string vazia se inválido
    
    Exemplos:
        >>> competencia_from_dt("01012024", "31012024")
        '01/2024'
        >>> competencia_from_dt("01122023", "31122023")
        '12/2023'
    """
    if len(dt_ini) == 8:
        return f"{dt_ini[2:4]}/{dt_ini[4:8]}"
    return ""


def format_flag(value: str) -> str:
    """
    Formata flags SIM/NÃO de forma profissional.
    
    Args:
        value: Valor da flag ("SIM", "NAO", "NÃO", etc)
    
    Returns:
        String formatada com emoji (✅ ou ➖)
    
    Exemplos:
        >>> format_flag("SIM")
        '✅ Sim'
        >>> format_flag("NAO")
        '➖ Não'
    """
    v_upper = str(value).upper().strip()
    if v_upper == "SIM":
        return "✅ Sim"
    elif v_upper in ("NAO", "NÃO"):
        return "➖ Não"
    return str(value)


def regime_label(regime: str) -> str:
    """
    Retorna o label formatado do regime tributário.
    
    Args:
        regime: Código do regime (ex: "TRIBUTACAO_PADRAO", "RED_60_ESSENCIALIDADE")
    
    Returns:
        Label formatado e legível
    
    Exemplos:
        >>> regime_label("TRIBUTACAO_PADRAO")
        'Tributação Padrão'
        >>> regime_label("RED_60_ESSENCIALIDADE")
        'Redução 60% (Essencialidade)'
        >>> regime_label("ALIQ_ZERO_CESTA_BASICA_NACIONAL")
        'Alíquota Zero (Cesta Básica Nacional)'
    """
    regime_upper = str(regime).upper().strip()
    
    # Mapeamento de regimes conhecidos
    regime_map = {
        "TRIBUTACAO_PADRAO": "Tributação Padrão",
        "RED_60_ESSENCIALIDADE": "Redução 60% (Essencialidade)",
        "RED_60_ALIMENTOS": "Redução 60% (Alimentos)",
        "ALIQ_ZERO_CESTA_BASICA_NACIONAL": "Alíquota Zero (Cesta Básica Nacional)",
    }
    
    return regime_map.get(regime_upper, regime)


def map_tipo_aliquota(codigo: str) -> str:
    """
    Mapeia código de tipo de alíquota para descrição legível.
    
    Args:
        codigo: Código do tipo de alíquota
    
    Returns:
        Descrição do tipo de alíquota
    
    Exemplos:
        >>> map_tipo_aliquota("01")
        'Alíquota padrão'
        >>> map_tipo_aliquota("02")
        'Alíquota específica por unidade de medida'
    """
    tipo_map = {
        "01": "Alíquota padrão",
        "02": "Alíquota específica por unidade de medida",
        "03": "Alíquota reduzida",
        "04": "Alíquota zero",
        "05": "Imunidade",
        "06": "Isenção",
        "07": "Não incidência",
        "08": "Suspensão",
    }
    return tipo_map.get(str(codigo).strip(), f"Tipo {codigo}")
