# 🟡 PRICETAX - Sistema IBS/CBS 2026

![Version](https://img.shields.io/badge/version-4.1-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.40-red)
![License](https://img.shields.io/badge/license-Proprietary-black)

**Sistema completo de consulta e análise tributária para a Reforma Tributária do Consumo (IBS e CBS).**

Desenvolvido pela **PRICETAX** para auxiliar empresas e contadores na transição para o novo sistema tributário brasileiro (LC 214/2025).

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Documentação Técnica](#-documentação-técnica)
- [Contribuição](#-contribuição)
- [Suporte](#-suporte)

---

## 🎯 Sobre o Projeto

O **PRICETAX IBSeCBS** é uma aplicação web desenvolvida em Streamlit que oferece:

- ✅ **Classificação NCM** com alíquotas IBS/CBS 2026
- ✅ **Análise de CFOPs** e sugestão de cClassTrib
- ✅ **Busca semântica** por descrição de produtos (204 sinônimos validados)
- ✅ **Ranking SPED** de vendas por NCM
- ✅ **Análise de XML** de NF-e com cálculo automático de tributos
- ✅ **Inteligência jurídica** com 544 artigos da LC 214/2025

### 🔥 Diferenciais

- **Hierarquia NCM completa**: 7.887 NCMs (71.1%) enriquecidos com descrições hierárquicas
- **Busca inteligente**: Dicionário de sinônimos com 204 mapeamentos validados
- **Coleta silenciosa de dados**: Market intelligence via Google Sheets (invisível ao usuário)
- **Conformidade legal**: Baseado 100% na LC 214/2025 e NT 2025.002-RTC

---

## 🚀 Funcionalidades

### 1️⃣ **Consulta NCM + CFOP**

Busca completa de produtos por NCM com:
- Descrição hierárquica completa (Capítulo → Posição → Subposição → Item)
- Alíquotas IBS/CBS 2026 (ano teste)
- Regime tributário (Cesta Básica, Redução 60%, Tributação Padrão)
- Sugestão automática de cClassTrib baseada em CFOP
- Flags de alimento, cesta básica, hortifrúti, redução 60%
- Alertas e observações legais

**Exemplo de uso:**
```
NCM: 02011000
CFOP: 5102
→ Resultado: Carne bovina congelada, Redução 60%, cClassTrib 200034
```

### 2️⃣ **Consulta CFOP**

Análise isolada de CFOPs com:
- Descrição completa da operação
- Sugestão de cClassTrib
- Natureza da operação (onerosa/não onerosa)
- Fundamento legal

### 3️⃣ **Busca por Descrição**

Busca semântica inteligente com:
- 204 sinônimos validados (linguiça → enchidos, frango → aves, etc)
- Eliminação de termos genéricos (carnes, preparações, aparelhos)
- Resultados específicos e relevantes
- Ordenação por relevância

**Exemplo de uso:**
```
Busca: "linguiça de porco"
→ Resultado: NCM 1601.00.00 - Enchidos (linguiças) e produtos semelhantes
```

### 4️⃣ **Ranking SPED**

Análise de arquivo SPED PIS/COFINS:
- Extração automática de vendas (registros C100/C170)
- Ranking por valor total de vendas
- Consolidação por NCM + CFOP
- Identificação de principais produtos vendidos

### 5️⃣ **Análise de XML NF-e**

Parser completo de XML de Nota Fiscal Eletrônica:
- Extração de produtos (NCM, CFOP, descrição, valor)
- Cálculo automático de IBS/CBS
- Sugestão de cClassTrib por item
- **Coleta silenciosa** de dados de mercado (CNPJ, preços, CST)
- Exportação para Excel

**⚠️ IMPORTANTE:** A coleta de dados é **INVISÍVEL** ao usuário e alimenta inteligência de mercado via Google Sheets.

### 6️⃣ **Inteligência Jurídica**

Consulta à base legal completa:
- 544 artigos da LC 214/2025
- 50 perguntas e respostas (Q&A)
- Busca por número de artigo
- Busca por palavra-chave
- Dashboard de estudo

---

## 🛠️ Tecnologias

### **Backend**
- Python 3.11
- Pandas (manipulação de dados)
- OpenPyXL (leitura de Excel)
- xml.etree.ElementTree (parser XML)
- gspread (Google Sheets API)
- sentence-transformers (busca semântica)

### **Frontend**
- Streamlit 1.40
- Altair (visualizações)
- HTML/CSS customizado

### **Infraestrutura**
- Streamlit Cloud (deploy)
- GitHub (versionamento)
- Google Sheets (market intelligence)

---

## 📦 Instalação

### **Pré-requisitos**
- Python 3.11+
- pip3

### **Passo a passo**

1. **Clone o repositório:**
```bash
git clone https://github.com/RAFAELSOUZA280292/IBSeCBS_PRICETAX.git
cd IBSeCBS_PRICETAX
```

2. **Instale as dependências:**
```bash
pip3 install -r requirements.txt
```

3. **Configure os secrets (opcional - para Google Sheets):**

Crie o arquivo `.streamlit/secrets.toml`:
```toml
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "sua-chave"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "sua-conta@projeto.iam.gserviceaccount.com"
client_id = "seu-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

4. **Execute a aplicação:**
```bash
streamlit run app.py
```

5. **Acesse no navegador:**
```
http://localhost:8501
```

---

## 💻 Uso

### **Exemplo 1: Consultar NCM de arroz**

1. Acesse a aba **"🔍 Consulta NCM + CFOP"**
2. Digite o NCM: `10064000`
3. Selecione o CFOP: `5102`
4. Clique em **"Buscar"**
5. Resultado:
   - **Descrição:** Cereais - Arroz quebrado (Trinca de arroz*)
   - **Regime:** Alíquota Zero (Cesta Básica Nacional)
   - **cClassTrib:** 200003
   - **IBS:** 0,00% | **CBS:** 0,00%

### **Exemplo 2: Analisar XML de NF-e**

1. Acesse a aba **"📄 Análise de XML NF-e"**
2. Faça upload do arquivo XML
3. Visualize a análise completa:
   - Produtos extraídos
   - Cálculo de IBS/CBS por item
   - Total de tributos
4. Baixe o relatório em Excel

### **Exemplo 3: Buscar por descrição**

1. Acesse a aba **"🔎 Busca por Descrição"**
2. Digite: `linguiça de porco`
3. Visualize resultados relevantes:
   - NCM 1601.00.00 - Enchidos (linguiças) e produtos semelhantes

---

## 📁 Estrutura do Projeto

```
IBSeCBS_PRICETAX/
│
├── app.py                              # Aplicação principal Streamlit
├── cclasstrib_mapping.py               # FONTE DA VERDADE para cClassTrib (NOVO)
├── calcular_tributacao.py              # Lógica de cálculo de alíquotas
├── beneficios_fiscais.py               # Lógica de consulta de benefícios
├── utils.py                            # Funções utilitárias
├── xml_parser.py                       # Parser de XML NF-e
│
├── classificacao_tributaria.xlsx       # Base oficial cClassTrib
├── BDBENEF_PRICETAX_2026.xlsx          # Base oficial de benefícios fiscais
├── ncm_hierarquia_completa.csv         # Base NCM enriquecida
│
├── requirements.txt                    # Dependências Python
├── README.md                           # Este arquivo
├── ARCHITECTURE.md                     # Documentação de arquitetura (NOVO)
├── CHANGELOG.md                        # Histórico de alterações (NOVO)
│
└── .streamlit/
    └── secrets.toml                    # Credenciais (NÃO COMMITAR)
```

---

## 📚 Documentação Técnica

### **Arquitetura**

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                       │
│  (5 Tabs: NCM, CFOP, Descrição, SPED, XML, Legal)         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE LÓGICA                         │
│  • tributacao.py (cClassTrib, regras LC 214/2025)          │
│  • utils.py (formatação, conversão)                        │
│  • xml_parser.py (extração de NF-e)                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE DADOS                          │
│  • PLANILHA_PRICETAX_REGRAS_REFINADAS.xlsx (11.091 NCMs)  │
│  • classificacao_tributaria.xlsx (cClassTrib)              │
│  • articles_db.json (544 artigos LC 214/2025)              │
│  • sinonimos_tipi.json (204 sinônimos)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              INTEGRAÇÃO EXTERNA (SILENT)                    │
│  • Google Sheets API (market intelligence)                 │
│  • Spreadsheet ID: 1MpzO2szc_9w1DiBNEOEJcNgsPZpTAxalvbxLjRB0m4o │
└─────────────────────────────────────────────────────────────┘
```

### **Fluxo de Classificação cClassTrib**

```
┌─────────────────────────────────────────────────────────────┐
│  INPUT: NCM + CFOP + Regime IVA                            │
└─────────────────────────────────────────────────────────────┘
                            │
                       ```
┌─────────────────────────────────────────────────────────────┐
│  PRIORIDADE 1: Mapeamento Oficial (cclasstrib_mapping.py)   │
│  • (Redução%, Anexo) → cClassTrib                          │
│  • Ex: (60, "ANEXO_XI") → 200043                           │
│  • Ex: (100, "ANEXO_I") → 200003                          │
└─────────────────────────────────────────────────────────────┘
```                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PRIORIDADE 2: CFOP específico                             │
│  • 5910, 6910, 7910 (brindes) → 410999                    │
│  • 5102, 6102 (vendas) → 000001                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PRIORIDADE 3: Regra genérica                              │
│  • Saída (5xxx/6xxx/7xxx) + CST normal → 000001           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT: cClassTrib + Mensagem Explicativa                 │
└─────────────────────────────────────────────────────────────┘
```

### **Regras de Negócio (LC 214/2025)**

#### **cClassTrib - Classificação Tributária**

| Série | Descrição | Exemplo | Fundamento |
|-------|-----------|---------|------------|
| **000xxx** | Tributação cheia (sem benefício) | 000001 | Operação padrão |
| **200xxx** | Operação onerosa com redução legal | 200003, 200034 | Anexos I, VII, arts. 137-145 |
| **410xxx** | Imunidade, isenção ou não incidência | 410999 | Brindes, doações |

#### **Alimentos - Classificação Correta**

| Tipo | Fundamento | cClassTrib | Redução | Exemplo |
|------|------------|------------|---------|---------|
| **Cesta Básica Nacional** | Anexo I LC 214/25 | **200003** | 100% (alíquota zero) | Arroz, feijão |
| **Cesta Básica Estendida** | Anexo VII LC 214/25 | **200034** | 60% | Carnes, queijos |
| **Alimentos sem benefício** | Tributação padrão | **000001** | 0% | Refrigerantes, doces |

⚠️ **ERRO COMUM:** Usar `000001` para produtos da cesta básica. **SEMPRE usar 200003 ou 200034!**

---

## 🧪 Testes

### **Testes Manuais**

Execute os seguintes testes para validar o sistema:

#### **Teste 1: Cesta Básica Nacional**
```python
# Input
NCM: 10064000 (Arroz quebrado)
CFOP: 5102
Regime IVA: ALIQ_ZERO_CESTA_BASICA_NACIONAL

# Expected Output
cClassTrib: 200003
Mensagem: "✅ Cesta Básica Nacional (Anexo I LC 214/25)"
IBS: 0,00%
CBS: 0,00%
```

#### **Teste 2: Redução 60%**
```python
# Input
NCM: 02011000 (Carne bovina)
CFOP: 5102
Regime IVA: RED_60_ALIMENTOS

# Expected Output
cClassTrib: 200034
Mensagem: "✅ Redução 60% (Anexo VII)"
IBS: 0,04% (0,1% × 40%)
CBS: 0,36% (0,9% × 40%)
```

#### **Teste 3: Tributação Padrão**
```python
# Input
NCM: 22021000 (Refrigerante)
CFOP: 5102
Regime IVA: TRIBUTACAO_PADRAO

# Expected Output
cClassTrib: 000001
Mensagem: "Regra genérica: saída tributada padrão"
IBS: 0,10%
CBS: 0,90%
```

#### **Teste 4: Operação Não Onerosa**
```python
# Input
NCM: 02011000
CFOP: 5910 (Brinde)
Regime IVA: RED_60_ALIMENTOS

# Expected Output
cClassTrib: 410999
Mensagem: "⚠️ Operação não onerosa - Não gera débito de IBS/CBS"
```

---

## 🤝 Contribuição

Este é um projeto proprietário da **PRICETAX**. Contribuições externas não são aceitas no momento.

Para reportar bugs ou sugerir melhorias, entre em contato através do [site oficial](https://pricetax.com.br).

---

## 📞 Suporte

### **Canais de Atendimento**

- 🌐 **Site:** [https://pricetax.com.br](https://pricetax.com.br)
- 📧 **Email:** contato@pricetax.com.br
- 💬 **Suporte:** [https://help.manus.im](https://help.manus.im)

### **Documentação Adicional**

- [LC 214/2025 - Texto Completo](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm)
- [NT 2025.002-RTC - Nota Técnica](https://www.gov.br/reformatributaria)
- [Portal da Reforma Tributária](https://www.gov.br/reformatributaria)

---

## 📄 Licença

**Proprietary License** - © 2024 PRICETAX. Todos os direitos reservados.

Este software é de propriedade exclusiva da PRICETAX e não pode ser copiado, modificado, distribuído ou usado sem autorização expressa.

---

## 📊 Estatísticas do Projeto

- **Linhas de código:** ~2.500
- **NCMs cadastrados:** 11.091
- **NCMs enriquecidos:** 7.887 (71.1%)
- **Sinônimos validados:** 204
- **Artigos legais:** 544
- **Funções documentadas:** 100%
- **Taxa de comentários:** 6% (meta: 10-15%)

---

## 🎓 Créditos

**Desenvolvido por:**
- PRICETAX - Inteligência Tributária
- Manus AI - Assistente de desenvolvimento

**Baseado em:**
- Lei Complementar nº 214/2025
- Nota Técnica 2025.002-RTC
- Emenda Constitucional 132/2023

---

## 📝 Changelog

### **v4.1 (Janeiro 2026)**
- ✅ **Refatoração completa do mapeamento cClassTrib**
- ✅ Criado `cclasstrib_mapping.py` como fonte da verdade
- ✅ Mapeamento de **TODOS os 15 anexos** da LC 214/2025
- ✅ Lógica condicional removida e substituída por dicionário
- ✅ Adicionado seletor de benefícios para NCMs com múltiplos enquadramentos
- ✅ Correção de bugs de UI (cores, contraste, reset de página)

### **v4.0 (Dezembro 2024)**
- ✅ Correção crítica: cClassTrib para cesta básica (200003/200034)
- ✅ Adição de 204 sinônimos validados
- ✅ Enriquecimento de 7.887 NCMs com hierarquia completa
- ✅ Integração da base legal LC 214/2025 (544 artigos)
- ✅ Modularização do código (utils.py, tributacao.py)
- ✅ Aumento de comentários inline
- ✅ README.md completo

### **v3.0 (Novembro 2024)**
- ✅ Análise de XML NF-e
- ✅ Coleta silenciosa de dados de mercado
- ✅ Ranking SPED

### **v2.0 (Outubro 2024)**
- ✅ Busca semântica por descrição
- ✅ Dicionário de sinônimos

### **v1.0 (Setembro 2024)**
- ✅ Consulta NCM + CFOP
- ✅ Consulta CFOP isolada
- ✅ Base TIPI completa

---

**🟡 PRICETAX** - Inteligência Tributária para a Nova Era
