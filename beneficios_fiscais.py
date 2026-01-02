"""
Módulo de Benefícios Fiscais IBS/CBS 2026
==========================================

Sistema completo de matching de NCM vs benefícios fiscais baseado na LC 214/2025.
Suporta múltiplos enquadramentos, normalização de padrões complexos, e integração
com todas as funcionalidades do PRICETAX.

Autor: PRICETAX
Data: Janeiro 2026
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import pandas as pd


# =============================================================================
# TIPOS E ESTRUTURAS DE DADOS
# =============================================================================

class TipoPattern(Enum):
    """Tipos de padrões encontrados na coluna NCM/IBS."""
    CAPITULO_1_DIGITO = "capitulo_1"      # Ex: "2" → "02"
    CAPITULO_2_DIGITOS = "capitulo_2"     # Ex: "31" → "31"
    POSICAO_3_DIGITOS = "posicao_3"       # Ex: "102" → "0102", "103" → "0103"
    PREFIXO_3_DIGITOS = "prefixo_3"       # Ex: "811" → "0811"
    PREFIXO_4_DIGITOS = "prefixo_4"       # Ex: "1051" → "01051"
    PREFIXO_5_DIGITOS = "prefixo_5"       # Ex: "85171"
    PREFIXO_6_DIGITOS = "prefixo_6"       # Ex: "100620"
    PREFIXO_7_DIGITOS = "prefixo_7"       # Ex: "1069000"
    NCM_EXATO_8_DIGITOS = "ncm_exato"     # Ex: "02068000"
    NBS_9_DIGITOS = "nbs_9"               # Ex: "101057000" (IGNORAR por enquanto)
    INVALIDO = "invalido"                 # Padrão não reconhecido


@dataclass
class Pattern:
    """Representa um padrão normalizado da coluna NCM/IBS."""
    tipo: TipoPattern
    valor_original: str
    prefixo_normalizado: str
    ncm_exato: Optional[str] = None
    
    def matches(self, ncm: str) -> bool:
        """Verifica se um NCM casa com este padrão."""
        if self.tipo == TipoPattern.NCM_EXATO_8_DIGITOS:
            return ncm == self.ncm_exato
        elif self.tipo == TipoPattern.NBS_9_DIGITOS:
            return False  # Ignorar NBS por enquanto
        elif self.tipo == TipoPattern.INVALIDO:
            return False
        else:
            # Match por prefixo
            return ncm.startswith(self.prefixo_normalizado)


@dataclass
class Enquadramento:
    """Representa um enquadramento fiscal de um NCM."""
    ncm: str
    anexo: str
    descricao_anexo: str
    reducao_percentual: float  # 0.6 para 60%, 1.0 para 100%
    pattern_aplicado: str
    tipo_match: str  # "exato" ou "prefixo"
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            "ncm": self.ncm,
            "anexo": self.anexo,
            "descricao_anexo": self.descricao_anexo,
            "reducao_percentual": self.reducao_percentual,
            "reducao_aliquota": int(self.reducao_percentual * 100),  # 60 ou 100
            "pattern_aplicado": self.pattern_aplicado,
            "tipo_match": self.tipo_match,
        }


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def normalize_ncm(input_str: str) -> Optional[str]:
    """
    Normaliza um NCM para formato padrão de 8 dígitos numéricos.
    
    Args:
        input_str: String de entrada (pode conter pontos, espaços, etc)
        
    Returns:
        String de 8 dígitos ou None se inválido
        
    Exemplos:
        "84.71.90.14" → "84719014"
        "8471.90.14" → "84719014"
        "84719014" → "84719014"
        "847190" → "00847190" (zfill)
        "123" → "00000123" (zfill)
        "123456789" → None (mais de 8 dígitos)
    """
    if not input_str:
        return None
    
    # Remover pontos, espaços, hífens
    cleaned = re.sub(r'[.\s\-]', '', str(input_str).strip())
    
    # Remover caracteres não numéricos
    numeric_only = re.sub(r'\D', '', cleaned)
    
    if not numeric_only:
        return None
    
    # Se tem mais de 8 dígitos, é inválido para NCM
    if len(numeric_only) > 8:
        return None
    
    # Preencher com zeros à esquerda até 8 dígitos
    return numeric_only.zfill(8)


def is_nbs(value_str: str) -> bool:
    """
    Verifica se um valor é NBS (Nomenclatura Brasileira de Serviços).
    
    Args:
        value_str: String a verificar
        
    Returns:
        True se for NBS, False caso contrário
        
    Heurística simples:
        - 9 dígitos numéricos
        - Ou padrão fora da regra de NCM
    """
    if not value_str:
        return False
    
    # Remover pontuação
    cleaned = re.sub(r'[.\s\-]', '', str(value_str).strip())
    numeric_only = re.sub(r'\D', '', cleaned)
    
    # Se tem 9 dígitos, é NBS
    if len(numeric_only) == 9:
        return True
    
    return False


def normalize_pattern(value_from_col_a: str) -> Pattern:
    """
    Normaliza um valor da coluna A (NCM/IBS) para um objeto Pattern.
    
    Args:
        value_from_col_a: Valor original da coluna A
        
    Returns:
        Objeto Pattern com tipo e prefixo normalizado
        
    Regras de normalização:
        1 dígito: "2" → "02" (capítulo)
        2 dígitos: "31" → "31" (capítulo)
        3 dígitos especiais: "102" → "0102", "103" → "0103", "104" → "0104"
        3 dígitos especiais: "811" → "0811", "901" → "0901", "903" → "0903"
        4 dígitos: "1051" → "01051" (prefixo)
        5 dígitos: "85171" → "85171" (prefixo)
        6 dígitos: "100620" → "100620" (prefixo)
        7 dígitos: "1069000" → "1069000" (prefixo)
        8 dígitos: "02068000" → NCM exato
        9 dígitos: NBS (ignorar)
    """
    if not value_from_col_a:
        return Pattern(TipoPattern.INVALIDO, "", "")
    
    # Converter para string e limpar
    value_str = str(value_from_col_a).strip()
    
    # Remover pontuação
    cleaned = re.sub(r'[.\s\-]', '', value_str)
    
    # Extrair apenas dígitos
    numeric_only = re.sub(r'\D', '', cleaned)
    
    if not numeric_only:
        return Pattern(TipoPattern.INVALIDO, value_str, "")
    
    length = len(numeric_only)
    
    # 9 dígitos → NBS (ignorar)
    if length == 9:
        return Pattern(TipoPattern.NBS_9_DIGITOS, value_str, "", None)
    
    # 1 dígito → capítulo (ex: "2" → "02")
    if length == 1:
        prefixo = numeric_only.zfill(2)
        return Pattern(TipoPattern.CAPITULO_1_DIGITO, value_str, prefixo)
    
    # 2 dígitos → capítulo (ex: "31" → "31")
    if length == 2:
        return Pattern(TipoPattern.CAPITULO_2_DIGITOS, value_str, numeric_only)
    
    # 3 dígitos → casos especiais
    if length == 3:
        # Posições especiais: 102, 103, 104 → 0102, 0103, 0104
        if numeric_only in {"102", "103", "104"}:
            prefixo = "01" + numeric_only[1:]
            return Pattern(TipoPattern.POSICAO_3_DIGITOS, value_str, prefixo)
        
        # Prefixos especiais: 811, 901, 903 → 0811, 0901, 0903
        if numeric_only in {"811", "901", "903"}:
            prefixo = numeric_only.zfill(4)
            return Pattern(TipoPattern.PREFIXO_3_DIGITOS, value_str, prefixo)
        
        # Outros 3 dígitos → tratar como capítulo + 1 dígito
        # Ex: "201" → "0201"
        prefixo = "0" + numeric_only
        return Pattern(TipoPattern.POSICAO_3_DIGITOS, value_str, prefixo)
    
    # 4 dígitos → prefixo direto (ex: "1508" → "1508", "1051" → "1051")
    if length == 4:
        # Usar o valor direto, sem adicionar zeros
        return Pattern(TipoPattern.PREFIXO_4_DIGITOS, value_str, numeric_only)
    
    # 5 dígitos → prefixo direto
    if length == 5:
        return Pattern(TipoPattern.PREFIXO_5_DIGITOS, value_str, numeric_only)
    
    # 6 dígitos → prefixo direto
    if length == 6:
        return Pattern(TipoPattern.PREFIXO_6_DIGITOS, value_str, numeric_only)
    
    # 7 dígitos → prefixo direto
    if length == 7:
        return Pattern(TipoPattern.PREFIXO_7_DIGITOS, value_str, numeric_only)
    
    # 8 dígitos → NCM exato
    if length == 8:
        return Pattern(TipoPattern.NCM_EXATO_8_DIGITOS, value_str, numeric_only, numeric_only)
    
    # Mais de 9 dígitos ou outros casos → inválido
    return Pattern(TipoPattern.INVALIDO, value_str, "")


# =============================================================================
# MOTOR DE MATCHING
# =============================================================================

class BeneficiosFiscaisEngine:
    """Motor de matching de NCM vs benefícios fiscais."""
    
    def __init__(self, planilha_path: str):
        """
        Inicializa o motor carregando a planilha de benefícios.
        
        Args:
            planilha_path: Caminho para BDBENEFÍCIOS_PRICETAX_2026.xlsx
        """
        self.planilha_path = planilha_path
        self.df: Optional[pd.DataFrame] = None
        self.patterns: List[Tuple[Pattern, Dict]] = []
        self._load_data()
    
    def _load_data(self):
        """Carrega e pré-processa a planilha de benefícios."""
        try:
            self.df = pd.read_excel(self.planilha_path)
            
            # Validar colunas
            required_cols = ["NCM/IBS", "ANEXO", "DESCRIÇÃO ANEXO", "REDUÇÃO BASE"]
            for col in required_cols:
                if col not in self.df.columns:
                    raise ValueError(f"Coluna obrigatória '{col}' não encontrada")
            
            # Pré-processar patterns
            for idx, row in self.df.iterrows():
                pattern = normalize_pattern(row["NCM/IBS"])
                
                # Ignorar NBS e inválidos
                if pattern.tipo in {TipoPattern.NBS_9_DIGITOS, TipoPattern.INVALIDO}:
                    continue
                
                dados = {
                    "anexo": str(row["ANEXO"]).strip(),
                    "descricao": str(row["DESCRIÇÃO ANEXO"]).strip(),
                    "reducao": float(row["REDUÇÃO BASE"]),
                }
                
                self.patterns.append((pattern, dados))
            
            print(f"✅ Carregados {len(self.patterns)} patterns válidos de {len(self.df)} linhas")
            
        except Exception as e:
            print(f"❌ Erro ao carregar planilha: {e}")
            raise
    
    def get_matches(self, ncm: str) -> List[Enquadramento]:
        """
        Busca todos os enquadramentos possíveis para um NCM.
        
        Args:
            ncm: NCM a buscar (pode vir com pontos, será normalizado)
            
        Returns:
            Lista de Enquadramento (vazia se não houver match)
            
        Nota: Retorna APENAS o pattern mais específico (maior tamanho de prefixo).
        Se houver múltiplos patterns do mesmo tamanho, retorna todos.
        """
        # Normalizar NCM
        ncm_normalizado = normalize_ncm(ncm)
        
        if not ncm_normalizado:
            return []
        
        matches_temp: List[Tuple[int, Enquadramento]] = []  # (tamanho_prefixo, enquadramento)
        
        # Buscar em todos os patterns
        for pattern, dados in self.patterns:
            if pattern.matches(ncm_normalizado):
                tipo_match = "exato" if pattern.tipo == TipoPattern.NCM_EXATO_8_DIGITOS else "prefixo"
                
                # Calcular tamanho do prefixo (quanto mais específico, maior prioridade)
                if pattern.tipo == TipoPattern.NCM_EXATO_8_DIGITOS:
                    tamanho = 8
                else:
                    tamanho = len(pattern.prefixo_normalizado)
                
                enquadramento = Enquadramento(
                    ncm=ncm_normalizado,
                    anexo=dados["anexo"],
                    descricao_anexo=dados["descricao"],
                    reducao_percentual=dados["reducao"],
                    pattern_aplicado=pattern.valor_original,
                    tipo_match=tipo_match,
                )
                
                matches_temp.append((tamanho, enquadramento))
        
        if not matches_temp:
            return []
        
        # Retornar APENAS os patterns mais específicos (maior tamanho)
        max_tamanho = max(t for t, _ in matches_temp)
        matches = [enq for t, enq in matches_temp if t == max_tamanho]
        
        return matches
    
    def get_anexos_envolvidos(self, ncms: List[str]) -> Dict:
        """
        Identifica anexos envolvidos em um conjunto de NCMs.
        
        Args:
            ncms: Lista de NCMs
            
        Returns:
            Dict com anexos encontrados e NCMs ambíguos
        """
        anexos_set: Set[str] = set()
        ncms_ambiguos: List[Dict] = []
        
        for ncm in ncms:
            matches = self.get_matches(ncm)
            
            if len(matches) > 1:
                # NCM com múltiplos enquadramentos
                ncms_ambiguos.append({
                    "ncm": ncm,
                    "enquadramentos": [m.to_dict() for m in matches],
                })
            
            # Adicionar anexos ao set
            for match in matches:
                anexos_set.add(match.anexo)
        
        return {
            "anexos_encontrados": sorted(list(anexos_set)),
            "total_anexos": len(anexos_set),
            "ncms_ambiguos": ncms_ambiguos,
            "total_ambiguos": len(ncms_ambiguos),
        }


# =============================================================================
# FUNÇÕES DE INTERFACE PARA O FRONT
# =============================================================================

def consulta_ncm(engine: BeneficiosFiscaisEngine, ncm: str) -> Dict:
    """
    Interface para consulta manual de NCM (Aba "Consulta NCM").
    
    Args:
        engine: Motor de benefícios fiscais
        ncm: NCM a consultar
        
    Returns:
        Dict com matches e flags de múltiplos enquadramentos
    """
    matches = engine.get_matches(ncm)
    
    return {
        "ncm_normalizado": normalize_ncm(ncm),
        "total_enquadramentos": len(matches),
        "multi_enquadramento": len(matches) > 1,
        "sem_beneficio": len(matches) == 0,
        "enquadramentos": [m.to_dict() for m in matches],
        "lista_anexos": [m.anexo for m in matches],
    }


def processar_sped_xml(engine: BeneficiosFiscaisEngine, ncms: List[str]) -> Dict:
    """
    Interface para processamento de SPED/XML (Abas "Ranking SPED" e "XML").
    
    Args:
        engine: Motor de benefícios fiscais
        ncms: Lista de NCMs encontrados no SPED/XML
        
    Returns:
        Dict com anexos encontrados e NCMs ambíguos
    """
    resultado = engine.get_anexos_envolvidos(ncms)
    
    # Adicionar mensagem para UI
    if resultado["total_ambiguos"] > 0:
        anexos_str = ", ".join(resultado["anexos_encontrados"])
        resultado["mensagem_ui"] = (
            f"⚠️ Você possui produtos que se aplicam a múltiplos anexos: {anexos_str}. "
            "Escolha um anexo PRINCIPAL para esta análise."
        )
    else:
        resultado["mensagem_ui"] = "✅ Todos os produtos têm enquadramento único."
    
    return resultado


# =============================================================================
# INICIALIZAÇÃO GLOBAL (para uso no app.py)
# =============================================================================

# Será inicializado no app.py
_engine_global: Optional[BeneficiosFiscaisEngine] = None


def init_engine(planilha_path: str) -> BeneficiosFiscaisEngine:
    """
    Inicializa o motor global de benefícios fiscais.
    
    Args:
        planilha_path: Caminho para a planilha de benefícios
        
    Returns:
        Engine inicializado
    """
    global _engine_global
    _engine_global = BeneficiosFiscaisEngine(planilha_path)
    return _engine_global


def get_engine() -> Optional[BeneficiosFiscaisEngine]:
    """Retorna o motor global (ou None se não inicializado)."""
    return _engine_global
