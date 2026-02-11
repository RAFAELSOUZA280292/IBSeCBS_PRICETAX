"""
PRICETAX - Testes Unitários
============================

Testes básicos para validar a lógica de classificação tributária.

Autor: PRICETAX
Versão: 4.0
Data: Dezembro 2024

Executar com: python3.11 test_tributacao.py
"""

from tributacao import guess_cclasstrib


def test_cesta_basica_nacional():
    """Teste: Cesta Básica Nacional (Anexo I) deve retornar 200003"""
    print("\n" + "="*70)
    print("TESTE 1: Cesta Básica Nacional (Anexo I)")
    print("="*70)
    
    # Input
    cst = "000"
    cfop = "5102"
    regime_iva = "ALIQ_ZERO_CESTA_BASICA_NACIONAL"
    
    # Executar
    code, msg = guess_cclasstrib(cst, cfop, regime_iva)
    
    # Validar
    expected_code = "200003"
    assert code == expected_code, f"[ERRO] FALHOU: Esperado {expected_code}, obtido {code}"
    assert "Cesta Básica Nacional" in msg, f"[ERRO] FALHOU: Mensagem incorreta: {msg}"
    
    print(f"[OK] PASSOU: cClassTrib = {code}")
    print(f"   Mensagem: {msg}")


def test_reducao_60_alimentos():
    """Teste: Redução 60% (Anexo VII) deve retornar 200034"""
    print("\n" + "="*70)
    print("TESTE 2: Redução 60% - Alimentos (Anexo VII)")
    print("="*70)
    
    # Input
    cst = "000"
    cfop = "5102"
    regime_iva = "RED_60_ALIMENTOS"
    
    # Executar
    code, msg = guess_cclasstrib(cst, cfop, regime_iva)
    
    # Validar
    expected_code = "200034"
    assert code == expected_code, f"[ERRO] FALHOU: Esperado {expected_code}, obtido {code}"
    assert "Redução 60%" in msg, f"[ERRO] FALHOU: Mensagem incorreta: {msg}"
    assert "Anexo VII" in msg, f"[ERRO] FALHOU: Deve mencionar Anexo VII: {msg}"
    
    print(f"[OK] PASSOU: cClassTrib = {code}")
    print(f"   Mensagem: {msg}")


def test_reducao_60_essencialidade():
    """Teste: Redução 60% (Essencialidade) deve retornar 200034"""
    print("\n" + "="*70)
    print("TESTE 3: Redução 60% - Essencialidade (arts. 137-145)")
    print("="*70)
    
    # Input
    cst = "000"
    cfop = "5102"
    regime_iva = "RED_60_ESSENCIALIDADE"
    
    # Executar
    code, msg = guess_cclasstrib(cst, cfop, regime_iva)
    
    # Validar
    expected_code = "200034"
    assert code == expected_code, f"[ERRO] FALHOU: Esperado {expected_code}, obtido {code}"
    assert "Redução 60%" in msg, f"[ERRO] FALHOU: Mensagem incorreta: {msg}"
    assert "essencialidade" in msg, f"[ERRO] FALHOU: Deve mencionar essencialidade: {msg}"
    
    print(f"[OK] PASSOU: cClassTrib = {code}")
    print(f"   Mensagem: {msg}")


def test_tributacao_padrao():
    """Teste: Tributação padrão deve retornar 000001"""
    print("\n" + "="*70)
    print("TESTE 4: Tributação Padrão (sem benefício)")
    print("="*70)
    
    # Input
    cst = "000"
    cfop = "5102"
    regime_iva = "TRIBUTACAO_PADRAO"
    
    # Executar
    code, msg = guess_cclasstrib(cst, cfop, regime_iva)
    
    # Validar
    expected_code = "000001"
    assert code == expected_code, f"[ERRO] FALHOU: Esperado {expected_code}, obtido {code}"
    
    print(f"[OK] PASSOU: cClassTrib = {code}")
    print(f"   Mensagem: {msg}")


def test_operacao_nao_onerosa():
    """Teste: Operação não onerosa (brinde) deve retornar 410999"""
    print("\n" + "="*70)
    print("TESTE 5: Operação Não Onerosa (Brinde)")
    print("="*70)
    
    # Input
    cst = "000"
    cfop = "5910"  # Brinde
    regime_iva = "TRIBUTACAO_PADRAO"
    
    # Executar
    code, msg = guess_cclasstrib(cst, cfop, regime_iva)
    
    # Validar
    expected_code = "410999"
    assert code == expected_code, f"[ERRO] FALHOU: Esperado {expected_code}, obtido {code}"
    assert "não onerosa" in msg, f"[ERRO] FALHOU: Mensagem incorreta: {msg}"
    
    print(f"[OK] PASSOU: cClassTrib = {code}")
    print(f"   Mensagem: {msg}")


def test_prioridade_regime_sobre_cfop():
    """Teste: Regime IVA tem prioridade sobre CFOP padrão"""
    print("\n" + "="*70)
    print("TESTE 6: Prioridade - Regime IVA > CFOP")
    print("="*70)
    
    # Input: CFOP 5102 normalmente retornaria 000001
    # Mas regime ALIQ_ZERO deve retornar 200003
    cst = "000"
    cfop = "5102"
    regime_iva = "ALIQ_ZERO_CESTA_BASICA_NACIONAL"
    
    # Executar
    code, msg = guess_cclasstrib(cst, cfop, regime_iva)
    
    # Validar
    expected_code = "200003"
    assert code == expected_code, f"[ERRO] FALHOU: Regime IVA deve ter prioridade! Esperado {expected_code}, obtido {code}"
    
    print(f"[OK] PASSOU: Regime IVA teve prioridade sobre CFOP")
    print(f"   cClassTrib = {code}")
    print(f"   Mensagem: {msg}")


def test_cfop_invalido():
    """Teste: CFOP vazio deve retornar mensagem de erro"""
    print("\n" + "="*70)
    print("TESTE 7: CFOP Inválido (vazio)")
    print("="*70)
    
    # Input
    cst = "000"
    cfop = ""
    regime_iva = "TRIBUTACAO_PADRAO"
    
    # Executar
    code, msg = guess_cclasstrib(cst, cfop, regime_iva)
    
    # Validar
    assert code == "", f"[ERRO] FALHOU: Código deveria ser vazio, obtido {code}"
    assert "Informe o CFOP" in msg, f"[ERRO] FALHOU: Mensagem incorreta: {msg}"
    
    print(f"[OK] PASSOU: Retornou erro adequado")
    print(f"   Mensagem: {msg}")


def test_cfop_interestadual():
    """Teste: CFOP interestadual (6xxx) deve funcionar corretamente"""
    print("\n" + "="*70)
    print("TESTE 8: CFOP Interestadual (6102)")
    print("="*70)
    
    # Input
    cst = "000"
    cfop = "6102"
    regime_iva = "TRIBUTACAO_PADRAO"
    
    # Executar
    code, msg = guess_cclasstrib(cst, cfop, regime_iva)
    
    # Validar
    expected_code = "000001"
    assert code == expected_code, f"[ERRO] FALHOU: Esperado {expected_code}, obtido {code}"
    
    print(f"[OK] PASSOU: cClassTrib = {code}")
    print(f"   Mensagem: {msg}")


def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*70)
    print(" INICIANDO TESTES - PRICETAX IBSeCBS")
    print("="*70)
    
    tests = [
        test_cesta_basica_nacional,
        test_reducao_60_alimentos,
        test_reducao_60_essencialidade,
        test_tributacao_padrao,
        test_operacao_nao_onerosa,
        test_prioridade_regime_sobre_cfop,
        test_cfop_invalido,
        test_cfop_interestadual,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n[ERRO] FALHOU: {e}")
            failed += 1
        except Exception as e:
            print(f"\n[ERRO] ERRO: {e}")
            failed += 1
    
    # Resumo
    print("\n" + "="*70)
    print("[ESTATÍSTICAS] RESUMO DOS TESTES")
    print("="*70)
    print(f"[OK] Passou: {passed}/{len(tests)}")
    print(f"[ERRO] Falhou: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n TODOS OS TESTES PASSARAM!")
    else:
        print(f"\n[ATENÇÃO] {failed} TESTE(S) FALHARAM - REVISAR!")
    
    print("="*70)


if __name__ == "__main__":
    run_all_tests()
