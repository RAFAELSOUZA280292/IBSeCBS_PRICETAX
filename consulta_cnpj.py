"""
Módulo de Consulta CNPJ - PRICETAX
Autor: Manus AI
Data: 21 de Janeiro de 2026

Este módulo fornece funções para consulta de dados cadastrais de CNPJ
através de APIs públicas (BrasilAPI e Open CNPJA).

Funcionalidades:
- Consulta de dados cadastrais (Razão Social, CNAE, Endereço, QSA)
- Consulta de Inscrições Estaduais
- Determinação de Regime Tributário
- Validação e formatação de CNPJ
- Cálculo de dígitos verificadores
"""

import requests
import re
import time
import datetime
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONSTANTES
# ============================================================================

URL_BRASILAPI_CNPJ = "https://brasilapi.com.br/api/cnpj/v1/"
URL_OPEN_CNPJA = "https://open.cnpja.com/office/"

# ============================================================================
# UTILITÁRIOS DE FORMATAÇÃO
# ============================================================================

def only_digits(s: str) -> str:
    """
    Remove todos os caracteres não numéricos de uma string.
    
    Args:
        s: String de entrada
        
    Returns:
        String contendo apenas dígitos
        
    Exemplo:
        >>> only_digits("21.746.980/0001-46")
        '21746980000146'
    """
    return re.sub(r'[^0-9]', '', s or "")


def format_cnpj_mask(cnpj: str) -> str:
    """
    Formata CNPJ com máscara padrão (00.000.000/0000-00).
    
    Args:
        cnpj: CNPJ sem formatação (14 dígitos)
        
    Returns:
        CNPJ formatado ou string original se inválido
        
    Exemplo:
        >>> format_cnpj_mask("21746980000146")
        '21.746.980/0001-46'
    """
    c = only_digits(cnpj)
    if len(c) == 14:
        return f"{c[0:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"
    return cnpj


def format_currency_brl(v) -> str:
    """
    Formata valor numérico como moeda brasileira (R$ 0.000,00).
    
    Args:
        v: Valor numérico
        
    Returns:
        String formatada ou "N/A" se inválido
    """
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "N/A"


def format_phone(ddd: str, num: str) -> str:
    """
    Formata telefone no padrão (DDD) Número.
    
    Args:
        ddd: Código DDD
        num: Número do telefone
        
    Returns:
        Telefone formatado ou "N/A" se inválido
    """
    return f"({ddd}) {num}" if ddd and num else "N/A"


# ============================================================================
# VALIDAÇÃO E CÁLCULO DE DÍGITOS VERIFICADORES
# ============================================================================

def calcular_digitos_verificadores_cnpj(cnpj_base_12_digitos: str) -> str:
    """
    Calcula os 2 dígitos verificadores de um CNPJ (13º e 14º dígitos).
    
    Implementa o algoritmo oficial da Receita Federal para validação de CNPJ.
    
    Args:
        cnpj_base_12_digitos: Primeiros 12 dígitos do CNPJ (raiz + ordem + filial)
        
    Returns:
        String com os 2 dígitos verificadores (ex: "46")
        
    Exemplo:
        >>> calcular_digitos_verificadores_cnpj("217469800001")
        '46'
    """
    pesos_12 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos_13 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    def calcular_dv(base: str, pesos: List[int]) -> str:
        soma = sum(int(base[i]) * pesos[i] for i in range(len(base)))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)
    
    # Calcula 13º dígito
    d13 = calcular_dv(cnpj_base_12_digitos[:12], pesos_12)
    
    # Calcula 14º dígito
    d14 = calcular_dv(cnpj_base_12_digitos[:12] + d13, pesos_13)
    
    return d13 + d14


def to_matriz_if_filial(cnpj_clean: str) -> str:
    """
    Converte CNPJ de filial para CNPJ da matriz.
    
    Se o CNPJ for de uma filial (ordem != 0001), calcula o CNPJ da matriz
    mantendo a raiz (8 primeiros dígitos) e substituindo ordem por 0001.
    
    Args:
        cnpj_clean: CNPJ sem formatação (14 dígitos)
        
    Returns:
        CNPJ da matriz se for filial, ou CNPJ original se já for matriz
        
    Exemplo:
        >>> to_matriz_if_filial("21746980000246")  # Filial 0002
        '21746980000146'  # Matriz 0001
    """
    if len(cnpj_clean) != 14:
        return cnpj_clean
    
    # Verifica se já é matriz (ordem = 0001)
    if cnpj_clean[8:12] == "0001":
        return cnpj_clean
    
    # Extrai raiz (8 primeiros dígitos) e monta CNPJ da matriz
    raiz = cnpj_clean[:8]
    base12 = raiz + "0001"
    dvs = calcular_digitos_verificadores_cnpj(base12)
    
    return base12 + dvs


# ============================================================================
# CONSULTAS A APIS EXTERNAS
# ============================================================================

def consulta_brasilapi_cnpj(cnpj_limpo: str) -> Dict:
    """
    Consulta dados cadastrais de CNPJ na BrasilAPI.
    
    Retorna dados completos incluindo: razão social, CNAE, endereço, QSA,
    regime tributário, situação cadastral, etc.
    
    Args:
        cnpj_limpo: CNPJ sem formatação (14 dígitos)
        
    Returns:
        Dicionário com dados do CNPJ ou dict com "__error" em caso de falha
        
    Possíveis erros:
        - {"__error": "not_found"}: CNPJ inválido ou não encontrado
        - {"__error": "unavailable"}: Serviço temporariamente indisponível
        
    Exemplo:
        >>> dados = consulta_brasilapi_cnpj("21746980000146")
        >>> dados["razao_social"]
        'EMPRESA EXEMPLO LTDA'
    """
    try:
        response = requests.get(
            f"{URL_BRASILAPI_CNPJ}{cnpj_limpo}",
            timeout=15
        )
        
        # CNPJ não encontrado ou inválido
        if response.status_code in (400, 404):
            return {"__error": "not_found"}
        
        # Serviço indisponível (rate limit, erro do servidor)
        if response.status_code in (429, 500, 502, 503, 504):
            return {"__error": "unavailable"}
        
        response.raise_for_status()
        return response.json()
        
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        return {"__error": "unavailable"}
    except requests.exceptions.HTTPError:
        return {"__error": "unavailable"}
    except Exception:
        return {"__error": "unavailable"}


def consulta_ie_open_cnpja(cnpj_limpo: str, max_retries: int = 2) -> Optional[List[Dict]]:
    """
    Consulta Inscrições Estaduais de um CNPJ na Open CNPJA.
    
    Args:
        cnpj_limpo: CNPJ sem formatação (14 dígitos)
        max_retries: Número máximo de tentativas em caso de rate limit (429)
        
    Returns:
        Lista de dicionários com IEs ou None em caso de erro
        Lista vazia [] se não houver IEs cadastradas
        
    Estrutura de cada IE:
        {
            "uf": "SP",
            "numero": "123456789",
            "habilitada": True,
            "status_texto": "Ativo",
            "tipo_texto": "Normal"
        }
    """
    url = f"{URL_OPEN_CNPJA}{cnpj_limpo}"
    attempt = 0
    
    while True:
        try:
            resp = requests.get(url, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                regs = data.get("registrations", []) if isinstance(data, dict) else []
                
                ies = []
                for reg in regs:
                    ies.append({
                        "uf": (reg or {}).get("state"),
                        "numero": (reg or {}).get("number"),
                        "habilitada": (reg or {}).get("enabled"),
                        "status_texto": ((reg or {}).get("status") or {}).get("text"),
                        "tipo_texto": ((reg or {}).get("type") or {}).get("text"),
                    })
                return ies
            
            # CNPJ não encontrado
            if resp.status_code == 404:
                return []
            
            # Rate limit - tenta novamente com backoff exponencial
            if resp.status_code == 429 and attempt < max_retries:
                time.sleep(2 * (attempt + 1))
                attempt += 1
                continue
            
            return None
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return None
        except Exception:
            return None


# ============================================================================
# DETERMINAÇÃO DE REGIME TRIBUTÁRIO
# ============================================================================

def determinar_regime_unificado(dados_cnpj: Dict) -> str:
    """
    Determina o regime tributário de um CNPJ baseado nos dados da Receita.
    
    Lógica de priorização:
    1. MEI (se opcao_pelo_mei = True)
    2. Simples Nacional (se opcao_pelo_simples = True)
    3. Regime Tributário do ano corrente ou mais recente disponível
    
    Args:
        dados_cnpj: Dicionário com dados do CNPJ (retorno da BrasilAPI)
        
    Returns:
        String com o regime tributário:
        - "MEI"
        - "SIMPLES NACIONAL"
        - "LUCRO REAL"
        - "LUCRO PRESUMIDO"
        - "N/A" (se não houver informação)
    """
    # Verifica se é MEI
    is_mei = dados_cnpj.get("opcao_pelo_mei")
    if is_mei:
        return "MEI"
    
    # Verifica se é Simples Nacional
    is_simples = dados_cnpj.get("opcao_pelo_simples")
    if is_simples:
        return "SIMPLES NACIONAL"
    
    # Busca regime tributário no histórico
    regimes = dados_cnpj.get("regime_tributario") or []
    if not regimes:
        return "N/A"
    
    # Tenta encontrar regime do ano corrente ou mais recente
    current_year = datetime.date.today().year
    anos = [r.get("ano") for r in regimes if isinstance(r.get("ano"), int)]
    
    if anos:
        # Filtra anos <= ano corrente
        candidatos = [a for a in anos if a <= current_year]
        
        # Pega o ano mais recente disponível
        alvo = max(candidatos) if candidatos else max(anos)
        
        # Busca regime desse ano (pega o último registro do ano)
        regime_alvo = next(
            (r for r in reversed(regimes) if r.get("ano") == alvo),
            regimes[-1]
        )
        
        forma = (regime_alvo or {}).get("forma_de_tributacao", "N/A")
        return str(forma).upper()
    
    # Fallback: pega o último regime disponível
    forma = (regimes[-1] or {}).get("forma_de_tributacao", "N/A")
    return str(forma).upper()


# ============================================================================
# NORMALIZAÇÃO DE SITUAÇÃO CADASTRAL
# ============================================================================

def normalizar_situacao_cadastral(txt: str) -> str:
    """
    Normaliza a descrição da situação cadastral para valores padronizados.
    
    Args:
        txt: Descrição da situação cadastral (ex: "ATIVA", "INAPTA", etc)
        
    Returns:
        Situação normalizada:
        - "ATIVO"
        - "INAPTO"
        - "SUSPENSO"
        - "BAIXADO"
        - Texto original (se não reconhecido)
        - "N/A" (se vazio)
    """
    s = (txt or "").strip().upper()
    
    if not s:
        return "N/A"
    
    if "ATIV" in s:
        return "ATIVO"
    if "INAPT" in s:
        return "INAPTO"
    if "SUSP" in s:
        return "SUSPENSO"
    if "BAIX" in s:
        return "BAIXADO"
    
    return s


# ============================================================================
# CORES DE BADGES (UI)
# ============================================================================

def badge_cor_regime(regime: str) -> Tuple[str, str]:
    """
    Retorna cores (background, foreground) para badge de regime tributário.
    
    Args:
        regime: Regime tributário (ex: "MEI", "SIMPLES NACIONAL", etc)
        
    Returns:
        Tupla (cor_fundo, cor_texto) em formato hexadecimal
        
    Exemplo:
        >>> badge_cor_regime("MEI")
        ('#FB923C', '#111111')  # Laranja com texto preto
    """
    r = (regime or "").upper()
    
    if "MEI" in r:
        return "#FB923C", "#111111"  # Laranja
    if "SIMPLES" in r:
        return "#FACC15", "#111111"  # Amarelo
    if "LUCRO REAL" in r:
        return "#3B82F6", "#FFFFFF"  # Azul
    if "LUCRO PRESUMIDO" in r:
        return "#22C55E", "#111111"  # Verde
    
    return "#EF4444", "#FFFFFF"  # Vermelho (padrão)


def cor_situacao_cadastral(situacao: str) -> Tuple[str, str]:
    """
    Retorna cor e ícone para situação cadastral.
    
    Args:
        situacao: Situação normalizada (ATIVO, INAPTO, SUSPENSO, BAIXADO)
        
    Returns:
        Tupla (cor_hex, label_texto)
        
    Exemplo:
        >>> cor_situacao_cadastral("ATIVO")
        ('#10B981', 'Ativo')
    """
    s = (situacao or "N/A").upper()
    
    if s == "ATIVO":
        return "#10B981", "Ativo"  # Verde
    elif s == "INAPTO":
        return "#FACC15", "Inapto"  # Amarelo
    elif s == "SUSPENSO":
        return "#FB923C", "Suspenso"  # Laranja
    elif s == "BAIXADO":
        return "#EF4444", "Baixado"  # Vermelho
    else:
        return "#6B7280", situacao.title() if situacao else "N/A"  # Cinza


# ============================================================================
# EXPORTAÇÃO CSV
# ============================================================================

def join_ies_for_csv(ies_list: Optional[List[Dict]]) -> str:
    """
    Concatena lista de IEs em uma string formatada para CSV.
    
    Args:
        ies_list: Lista de dicionários com IEs
        
    Returns:
        String com todas as IEs separadas por " || "
        
    Exemplo:
        >>> ies = [{"uf": "SP", "numero": "123", "habilitada": True, ...}]
        >>> join_ies_for_csv(ies)
        'UF: SP | IE: 123 | Habilitada: Sim | ...'
    """
    if not ies_list:
        return ""
    
    blocks = []
    for ie in ies_list:
        uf = ie.get("uf") or ""
        numero = ie.get("numero") or ""
        habil = "Sim" if ie.get("habilitada") else "Não"
        status_txt = ie.get("status_texto") or ""
        tipo_txt = ie.get("tipo_texto") or ""
        
        blocks.append(
            f"UF: {uf} | IE: {numero} | Habilitada: {habil} | "
            f"Status: {status_txt} | Tipo: {tipo_txt}"
        )
    
    return " || ".join(blocks)
