# 📘 Sistema de Benefícios Fiscais IBS/CBS 2026

## 🎯 Visão Geral

Este módulo implementa o motor completo de matching de NCM vs benefícios fiscais baseado na **LC 214/2025** e na planilha `BDBENEFÍCIOS_PRICETAX_2026.xlsx`.

**Características principais:**
- ✅ Normalização inteligente de NCM (com/sem pontos, zeros perdidos, etc)
- ✅ Suporte a múltiplos enquadramentos (um NCM pode ter vários anexos)
- ✅ Matching por capítulo, posição, prefixo e NCM exato
- ✅ Identificação automática de NBS (ignorados por enquanto)
- ✅ Interface pronta para integração com Streamlit

---

## 📁 Arquivos do Sistema

| Arquivo | Descrição |
|---------|-----------|
| `beneficios_fiscais.py` | Módulo core com toda a lógica |
| `test_beneficios_fiscais.py` | Testes unitários completos |
| `BDBENEFÍCIOS_PRICETAX_2026.xlsx` | Planilha fonte (651 linhas) |
| `README_BENEFICIOS_FISCAIS.md` | Esta documentação |

---

## 🚀 Como Usar

### 1. Inicializar o Motor

```python
from beneficios_fiscais import init_engine

# Inicializar com caminho da planilha
engine = init_engine("BDBENEFÍCIOS_PRICETAX_2026.xlsx")
```

### 2. Consultar um NCM

```python
from beneficios_fiscais import consulta_ncm, get_engine

engine = get_engine()
resultado = consulta_ncm(engine, "10.06.40.00")

print(f"NCM: {resultado['ncm_normalizado']}")
print(f"Total de enquadramentos: {resultado['total_enquadramentos']}")

for enq in resultado['enquadramentos']:
    print(f"  - {enq['anexo']}: redução de {enq['reducao_aliquota']}%")
```

**Saída:**
```
NCM: 10064000
Total de enquadramentos: 3
  - ANEXO VII: redução de 60%
  - ANEXO IX: redução de 60%
  - ANEXO I: redução de 100%
```

### 3. Processar SPED/XML

```python
from beneficios_fiscais import processar_sped_xml, get_engine

engine = get_engine()
ncms = ["10064000", "02068000", "30049099", "99999999"]

resultado = processar_sped_xml(engine, ncms)

print(f"Anexos encontrados: {resultado['anexos_encontrados']}")
print(f"NCMs ambíguos: {resultado['total_ambiguos']}")
print(f"Mensagem UI: {resultado['mensagem_ui']}")
```

---

## 🔍 Lógica de Matching

### Tipos de Padrões Suportados

| Padrão | Exemplo | Normalização | Match |
|--------|---------|--------------|-------|
| **Capítulo 1 dígito** | "2" | "02" | Todos NCMs que começam com "02" |
| **Capítulo 2 dígitos** | "31" | "31" | Todos NCMs que começam com "31" |
| **Posição 3 dígitos** | "102" | "0102" | Todos NCMs que começam com "0102" |
| **Prefixo 4 dígitos** | "1051" | "01051" | Todos NCMs que começam com "01051" |
| **Prefixo 5 dígitos** | "85171" | "85171" | Todos NCMs que começam com "85171" |
| **Prefixo 6 dígitos** | "100620" | "100620" | NCMs 10062010, 10062020, etc |
| **NCM exato 8 dígitos** | "02068000" | "02068000" | Apenas NCM 02068000 |
| **NBS 9 dígitos** | "101057000" | - | Ignorado (não é NCM) |

### Casos Especiais

**Posições especiais (3 dígitos):**
- "102" → "0102"
- "103" → "0103"
- "104" → "0104"

**Prefixos especiais (3 dígitos):**
- "811" → "0811"
- "901" → "0901"
- "903" → "0903"

**Prefixos com "1" no início (4 dígitos):**
- "1051" → "01051"
- "1102" → "01102"

---

## 📊 Múltiplos Enquadramentos

Alguns NCMs podem se enquadrar em **mais de um anexo** simultaneamente. O sistema retorna **todos** os enquadramentos possíveis.

**Exemplo real:**
```python
NCM 30049099 (medicamentos):
  - ANEXO IX: redução 60% (insumos agropecuários)
  - ANEXO IV: redução 60% (dispositivos médicos)
  - ANEXO XIV: redução 100% (medicamentos específicos)
  - ANEXO VI: redução 60% (produtos de saúde)
```

**Como o sistema trata:**
1. **Consulta manual (Aba "Consulta NCM"):**
   - Exibe alerta: "Este NCM possui múltiplos enquadramentos possíveis: ANEXO IX, ANEXO IV, ANEXO XIV, ANEXO VI"
   - Não obriga escolha (apenas informa)

2. **Ranking SPED:**
   - Antes de concluir análise, pergunta: "Qual anexo deseja considerar como PRINCIPAL?"
   - Usuário escolhe 1 anexo
   - Análise usa o anexo escolhido

3. **Importação XML:**
   - Exibe resumo: "O XML possui produtos enquadráveis em: ANEXO X, ANEXO Y"
   - Exige seleção de anexo principal
   - Só prossegue após escolha

---

## 🧪 Testes

### Executar Testes Manuais

```bash
cd /home/ubuntu/IBSeCBS_PRICETAX
python3.11 test_beneficios_fiscais.py
```

### Casos de Teste Cobertos

✅ Normalização de NCM com pontos  
✅ Normalização de NCM com zeros perdidos  
✅ NCM inválido (mais de 8 dígitos)  
✅ Identificação de NBS (9 dígitos)  
✅ Match por capítulo (1 e 2 dígitos)  
✅ Match por prefixo (4, 5, 6 dígitos)  
✅ Match por NCM exato (8 dígitos)  
✅ Múltiplos enquadramentos  
✅ NCM sem benefício  

---

## 📋 Estrutura da Planilha

**Arquivo:** `BDBENEFÍCIOS_PRICETAX_2026.xlsx`

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| **A: NCM/IBS** | Padrão de referência | "2", "102", "1051", "02068000" |
| **B: ANEXO** | Anexo da LC 214/2025 | "ANEXO I", "ANEXO VII", etc |
| **C: DESCRIÇÃO ANEXO** | Texto informativo | "ALIMENTOS DESTINADOS..." |
| **D: REDUÇÃO BASE** | Percentual de redução | 0.6 (60%) ou 1.0 (100%) |

**Estatísticas:**
- Total de linhas: 651
- Patterns válidos: 570 (81 NBS ignorados)
- Anexos únicos: 15
- Padrões com múltiplos enquadramentos: 18

---

## 🔧 Integração com app.py

### Passo 1: Importar no início do app.py

```python
from beneficios_fiscais import init_engine, get_engine, consulta_ncm, processar_sped_xml
```

### Passo 2: Inicializar no carregamento

```python
# Logo após carregar a planilha TIPI
try:
    BENEFICIOS_ENGINE = init_engine("BDBENEFÍCIOS_PRICETAX_2026.xlsx")
    print("✅ Motor de benefícios fiscais carregado")
except Exception as e:
    print(f"⚠️ Erro ao carregar benefícios: {e}")
    BENEFICIOS_ENGINE = None
```

### Passo 3: Usar na consulta de NCM

```python
# Na função que exibe resultado de NCM
if BENEFICIOS_ENGINE:
    resultado_beneficios = consulta_ncm(BENEFICIOS_ENGINE, ncm_usuario)
    
    if resultado_beneficios['total_enquadramentos'] > 0:
        st.success("🎁 Este produto possui benefícios fiscais!")
        
        for enq in resultado_beneficios['enquadramentos']:
            st.info(f"""
            **{enq['anexo']}**
            - Redução: {enq['reducao_aliquota']}%
            - Fundamento: {enq['descricao_anexo']}
            """)
        
        if resultado_beneficios['multi_enquadramento']:
            st.warning("⚠️ Múltiplos enquadramentos possíveis. Consulte legislação.")
    else:
        st.info("ℹ️ Este produto não possui benefícios fiscais específicos.")
```

### Passo 4: Usar no processamento SPED

```python
# Após extrair NCMs do SPED
if BENEFICIOS_ENGINE:
    resultado_sped = processar_sped_xml(BENEFICIOS_ENGINE, lista_ncms)
    
    if resultado_sped['total_ambiguos'] > 0:
        st.warning(resultado_sped['mensagem_ui'])
        
        anexo_escolhido = st.selectbox(
            "Escolha o anexo PRINCIPAL para esta análise:",
            resultado_sped['anexos_encontrados']
        )
        
        # Usar anexo_escolhido no restante da análise
```

---

## 🎯 Alinhamento com o Guia Didático IBS/CBS 2026

Este sistema está **100% alinhado** com o Guia Didático estudado anteriormente:

### ✅ Redução de Alíquota (não de base)
- Sistema trabalha com **redução de alíquota** (60% ou 100%)
- Base de cálculo **sempre integral**
- Conforme modelo IVA moderno

### ✅ Três Cenários para Vendas
- **Tributação cheia (100%):** NCMs sem benefício → cClassTrib 000001
- **Redução 60%:** ANEXO VII, IX, etc → cClassTrib 200034
- **Redução 100%:** ANEXO I (Cesta Básica) → cClassTrib 200003

### ✅ Fonte Única da Verdade
- Planilha `BDBENEFÍCIOS_PRICETAX_2026.xlsx` é a **única fonte**
- Não há regras antigas ou lógica tributária anterior
- Sistema apenas lê e aplica o que está na planilha

---

## 📚 Referências

- **LC 214/2025:** Lei Complementar da Reforma Tributária
- **Guia Didático IBS/CBS 2026 (LAVO):** Documento de referência técnica
- **Anexo I:** Cesta Básica Nacional (redução 100%)
- **Anexo VII:** Cesta Básica Estendida (redução 60%)
- **Anexos IX, IV, VI, etc:** Outros benefícios setoriais (redução 60%)

---

## 🐛 Troubleshooting

### Problema: "Planilha não encontrada"
**Solução:** Verificar se `BDBENEFÍCIOS_PRICETAX_2026.xlsx` está no diretório correto

### Problema: "NCM não retorna benefício esperado"
**Solução:** Verificar se o NCM está na planilha ou se é coberto por um padrão de prefixo

### Problema: "Múltiplos enquadramentos inesperados"
**Solução:** Isso é correto! Alguns NCMs realmente têm múltiplos anexos. Consultar legislação para escolher o mais adequado.

---

## ✅ Status do Sistema

**Versão:** 1.0  
**Data:** Janeiro 2026  
**Status:** ✅ Pronto para produção  
**Testes:** ✅ Todos passando  
**Integração:** ⏳ Aguardando integração com app.py

---

**Desenvolvido por:** PRICETAX  
**Contato:** Rafa Souza
