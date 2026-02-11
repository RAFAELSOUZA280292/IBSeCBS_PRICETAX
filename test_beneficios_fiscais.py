"""
Testes Unitários - Módulo de Benefícios Fiscais
================================================

Testes completos para validar normalização de NCM, matching de padrões,
e lógica de múltiplos enquadramentos.

Autor: PRICETAX
Data: Janeiro 2026
"""

import pytest
from beneficios_fiscais import (
    normalize_ncm,
    is_nbs,
    normalize_pattern,
    TipoPattern,
    BeneficiosFiscaisEngine,
    consulta_ncm,
    processar_sped_xml,
)


# =============================================================================
# TESTES DE NORMALIZAÇÃO DE NCM
# =============================================================================

class TestNormalizeNCM:
    """Testes para função normalize_ncm()."""
    
    def test_ncm_com_pontos(self):
        """Deve remover pontos e normalizar."""
        assert normalize_ncm("84.71.90.14") == "84719014"
        assert normalize_ncm("10.06.20.10") == "10062010"
    
    def test_ncm_sem_pontos(self):
        """Deve manter NCM já normalizado."""
        assert normalize_ncm("84719014") == "84719014"
        assert normalize_ncm("10062010") == "10062010"
    
    def test_ncm_com_zeros_perdidos(self):
        """Deve preencher zeros à esquerda."""
        assert normalize_ncm("847190") == "00847190"
        assert normalize_ncm("123") == "00000123"
        assert normalize_ncm("1") == "00000001"
    
    def test_ncm_com_espacos(self):
        """Deve remover espaços."""
        assert normalize_ncm(" 84719014 ") == "84719014"
        assert normalize_ncm("8471 9014") == "84719014"
    
    def test_ncm_invalido_mais_8_digitos(self):
        """Deve retornar None para mais de 8 dígitos."""
        assert normalize_ncm("123456789") is None
        assert normalize_ncm("12345678901") is None
    
    def test_ncm_invalido_vazio(self):
        """Deve retornar None para entrada vazia."""
        assert normalize_ncm("") is None
        assert normalize_ncm(None) is None
    
    def test_ncm_com_caracteres_especiais(self):
        """Deve remover caracteres especiais."""
        assert normalize_ncm("8471-90-14") == "84719014"
        assert normalize_ncm("8471.90-14") == "84719014"


# =============================================================================
# TESTES DE IDENTIFICAÇÃO DE NBS
# =============================================================================

class TestIsNBS:
    """Testes para função is_nbs()."""
    
    def test_nbs_9_digitos(self):
        """Deve identificar NBS com 9 dígitos."""
        assert is_nbs("101057000") is True
        assert is_nbs("123019900") is True
    
    def test_ncm_8_digitos_nao_e_nbs(self):
        """NCM de 8 dígitos não é NBS."""
        assert is_nbs("84719014") is False
        assert is_nbs("10062010") is False
    
    def test_entrada_vazia(self):
        """Entrada vazia não é NBS."""
        assert is_nbs("") is False
        assert is_nbs(None) is False


# =============================================================================
# TESTES DE NORMALIZAÇÃO DE PATTERNS
# =============================================================================

class TestNormalizePattern:
    """Testes para função normalize_pattern()."""
    
    def test_capitulo_1_digito(self):
        """Deve normalizar capítulo de 1 dígito."""
        pattern = normalize_pattern("2")
        assert pattern.tipo == TipoPattern.CAPITULO_1_DIGITO
        assert pattern.prefixo_normalizado == "02"
        assert pattern.matches("02068000")
        assert not pattern.matches("03068000")
    
    def test_capitulo_2_digitos(self):
        """Deve normalizar capítulo de 2 dígitos."""
        pattern = normalize_pattern("31")
        assert pattern.tipo == TipoPattern.CAPITULO_2_DIGITOS
        assert pattern.prefixo_normalizado == "31"
        assert pattern.matches("31012000")
        assert not pattern.matches("32012000")
    
    def test_posicao_3_digitos_especiais(self):
        """Deve normalizar posições especiais 102, 103, 104."""
        pattern = normalize_pattern("102")
        assert pattern.tipo == TipoPattern.POSICAO_3_DIGITOS
        assert pattern.prefixo_normalizado == "0102"
        assert pattern.matches("01021000")
        
        pattern = normalize_pattern("103")
        assert pattern.prefixo_normalizado == "0103"
        
        pattern = normalize_pattern("104")
        assert pattern.prefixo_normalizado == "0104"
    
    def test_prefixo_3_digitos_especiais(self):
        """Deve normalizar prefixos especiais 811, 901, 903."""
        pattern = normalize_pattern("811")
        assert pattern.tipo == TipoPattern.PREFIXO_3_DIGITOS
        assert pattern.prefixo_normalizado == "0811"
        
        pattern = normalize_pattern("901")
        assert pattern.prefixo_normalizado == "0901"
        
        pattern = normalize_pattern("903")
        assert pattern.prefixo_normalizado == "0903"
    
    def test_prefixo_4_digitos(self):
        """Deve normalizar prefixo de 4 dígitos."""
        pattern = normalize_pattern("1051")
        assert pattern.tipo == TipoPattern.PREFIXO_4_DIGITOS
        assert pattern.prefixo_normalizado == "01051"
        assert pattern.matches("01051110")
        assert pattern.matches("01051200")
    
    def test_prefixo_5_digitos(self):
        """Deve normalizar prefixo de 5 dígitos."""
        pattern = normalize_pattern("85171")
        assert pattern.tipo == TipoPattern.PREFIXO_5_DIGITOS
        assert pattern.prefixo_normalizado == "85171"
        assert pattern.matches("85171100")
        assert not pattern.matches("85172000")
    
    def test_prefixo_6_digitos(self):
        """Deve normalizar prefixo de 6 dígitos."""
        pattern = normalize_pattern("100620")
        assert pattern.tipo == TipoPattern.PREFIXO_6_DIGITOS
        assert pattern.prefixo_normalizado == "100620"
        assert pattern.matches("10062010")
        assert pattern.matches("10062020")
        assert not pattern.matches("10063000")
    
    def test_ncm_exato_8_digitos(self):
        """Deve identificar NCM exato de 8 dígitos."""
        pattern = normalize_pattern("02068000")
        assert pattern.tipo == TipoPattern.NCM_EXATO_8_DIGITOS
        assert pattern.ncm_exato == "02068000"
        assert pattern.matches("02068000")
        assert not pattern.matches("02068001")
    
    def test_nbs_9_digitos(self):
        """Deve identificar NBS de 9 dígitos."""
        pattern = normalize_pattern("101057000")
        assert pattern.tipo == TipoPattern.NBS_9_DIGITOS
        assert not pattern.matches("10105700")  # Não deve casar
    
    def test_pattern_invalido(self):
        """Deve identificar padrão inválido."""
        pattern = normalize_pattern("")
        assert pattern.tipo == TipoPattern.INVALIDO
        
        pattern = normalize_pattern("abc")
        assert pattern.tipo == TipoPattern.INVALIDO


# =============================================================================
# TESTES DO MOTOR DE MATCHING
# =============================================================================

class TestBeneficiosFiscaisEngine:
    """Testes para o motor de matching."""
    
    @pytest.fixture
    def engine(self):
        """Fixture que inicializa o motor com a planilha real."""
        import os
        planilha_path = "/home/ubuntu/upload/BDBENEFÍCIOS_PRICETAX_2026.xlsx"
        
        # Verificar se arquivo existe
        if not os.path.exists(planilha_path):
            # Tentar encontrar o arquivo
            upload_dir = "/home/ubuntu/upload"
            files = [f for f in os.listdir(upload_dir) if 'BDBENEF' in f and f.endswith('.xlsx')]
            if files:
                planilha_path = os.path.join(upload_dir, files[0])
            else:
                pytest.skip("Planilha de benefícios não encontrada")
        
        return BeneficiosFiscaisEngine(planilha_path)
    
    def test_match_por_capitulo(self, engine):
        """Deve encontrar match por capítulo."""
        # Capítulo 2 está no ANEXO VII (redução 60%)
        matches = engine.get_matches("02068000")
        assert len(matches) > 0
        assert any(m.anexo == "ANEXO VII" for m in matches)
    
    def test_match_por_ncm_exato(self, engine):
        """Deve encontrar match por NCM exato."""
        # NCM 10064000 está no ANEXO I (redução 100%)
        matches = engine.get_matches("10064000")
        assert len(matches) > 0
        assert any(m.anexo == "ANEXO I" and m.reducao_percentual == 1.0 for m in matches)
    
    def test_multiplos_enquadramentos(self, engine):
        """Deve retornar múltiplos enquadramentos quando aplicável."""
        # NCM 30049099 tem 3 enquadramentos
        matches = engine.get_matches("30049099")
        assert len(matches) >= 2  # Pelo menos 2 enquadramentos
    
    def test_ncm_sem_beneficio(self, engine):
        """Deve retornar lista vazia para NCM sem benefício."""
        # NCM inventado que não existe na planilha
        matches = engine.get_matches("99999999")
        assert len(matches) == 0
    
    def test_ncm_com_pontos(self, engine):
        """Deve funcionar com NCM formatado com pontos."""
        matches1 = engine.get_matches("10064000")
        matches2 = engine.get_matches("10.06.40.00")
        assert len(matches1) == len(matches2)


# =============================================================================
# TESTES DE INTERFACE
# =============================================================================

class TestConsultaNCM:
    """Testes para função consulta_ncm()."""
    
    @pytest.fixture
    def engine(self):
        """Fixture que inicializa o motor."""
        import os
        upload_dir = "/home/ubuntu/upload"
        files = [f for f in os.listdir(upload_dir) if 'BDBENEF' in f and f.endswith('.xlsx')]
        if not files:
            pytest.skip("Planilha não encontrada")
        planilha_path = os.path.join(upload_dir, files[0])
        return BeneficiosFiscaisEngine(planilha_path)
    
    def test_consulta_ncm_com_beneficio(self, engine):
        """Deve retornar dados completos para NCM com benefício."""
        resultado = consulta_ncm(engine, "10064000")
        assert resultado["ncm_normalizado"] == "10064000"
        assert resultado["total_enquadramentos"] > 0
        assert resultado["sem_beneficio"] is False
        assert len(resultado["enquadramentos"]) > 0
    
    def test_consulta_ncm_sem_beneficio(self, engine):
        """Deve indicar quando NCM não tem benefício."""
        resultado = consulta_ncm(engine, "99999999")
        assert resultado["sem_beneficio"] is True
        assert resultado["total_enquadramentos"] == 0
    
    def test_consulta_ncm_multiplos_enquadramentos(self, engine):
        """Deve sinalizar múltiplos enquadramentos."""
        resultado = consulta_ncm(engine, "30049099")
        if resultado["total_enquadramentos"] > 1:
            assert resultado["multi_enquadramento"] is True


class TestProcessarSpedXML:
    """Testes para função processar_sped_xml()."""
    
    @pytest.fixture
    def engine(self):
        """Fixture que inicializa o motor."""
        import os
        upload_dir = "/home/ubuntu/upload"
        files = [f for f in os.listdir(upload_dir) if 'BDBENEF' in f and f.endswith('.xlsx')]
        if not files:
            pytest.skip("Planilha não encontrada")
        planilha_path = os.path.join(upload_dir, files[0])
        return BeneficiosFiscaisEngine(planilha_path)
    
    def test_processar_lista_ncms(self, engine):
        """Deve processar lista de NCMs e identificar anexos."""
        ncms = ["10064000", "02068000", "99999999"]
        resultado = processar_sped_xml(engine, ncms)
        
        assert "anexos_encontrados" in resultado
        assert "total_anexos" in resultado
        assert "ncms_ambiguos" in resultado
        assert "mensagem_ui" in resultado
    
    def test_identificar_ncms_ambiguos(self, engine):
        """Deve identificar NCMs com múltiplos enquadramentos."""
        ncms = ["30049099"]  # NCM com múltiplos enquadramentos
        resultado = processar_sped_xml(engine, ncms)
        
        if resultado["total_ambiguos"] > 0:
            assert len(resultado["ncms_ambiguos"]) > 0
            assert "ATENÇÃO: " in resultado["mensagem_ui"]


# =============================================================================
# EXECUÇÃO DOS TESTES
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
