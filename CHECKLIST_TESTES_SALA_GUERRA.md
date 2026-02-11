
# SALA DE GUERRA - CHECKLIST DE TESTES PRÉ-LANÇAMENTO
Data: 10/02/2026
Objetivo: Garantir 100% de funcionalidade para 100 usuários

## 1. TESTE DE ABAS E FUNCIONALIDADES

### FERRAMENTAS
- [ ] Consulta NCM
  - [ ] Busca por NCM (8 dígitos)
  - [ ] Busca por CFOP
  - [ ] Busca por descrição
  - [ ] Exibição de benefícios fiscais
  - [ ] Cálculo de alíquotas IBS/CBS
  
- [ ] Ranking de Saídas SPED
  - [ ] Upload de arquivo TXT
  - [ ] Processamento e ranking
  - [ ] Exibição de resultados
  
- [ ] cClassTrib
  - [ ] Consulta de códigos
  - [ ] Busca por descrição
  - [ ] Exibição de fundamentos legais
  
- [ ] Download CFOP x cClassTrib
  - [ ] Download de planilha
  - [ ] Formato correto (XLSX)
  
- [ ] Análise XML NF-e
  - [ ] Upload de XML
  - [ ] Parsing de dados
  - [ ] Cálculo de tributação
  - [ ] Exibição de itens
  - [ ] Benefícios fiscais identificados
  - [ ] Divergências destacadas
  
- [ ] Análise XML NFSe
  - [ ] Upload de XML
  - [ ] Parsing de dados
  - [ ] Cálculo de tributação
  - [ ] Exibição de serviços
  
- [ ] Processamento em Lote
  - [ ] Upload de ZIP com múltiplos XMLs
  - [ ] Processamento paralelo
  - [ ] Estatísticas agregadas
  - [ ] Gráficos (Plotly)
  - [ ] Top 5 fornecedores
  - [ ] Download de relatório
  
- [ ] Consulta CNPJ
  - [ ] Busca por CNPJ
  - [ ] Exibição de dados
  - [ ] Tratamento de erro (CNPJ inválido)

### LEGISLAÇÃO
- [ ] LC 214/2025
  - [ ] Consulta por Artigo/Palavra
  - [ ] Blocos Temáticos (32 blocos)
  - [ ] Texto Integral da Lei
  - [ ] Índice Sistemático
  - [ ] Índice Remissivo
  - [ ] Central de Q&A (50 questões)

### ADMIN
- [ ] Painel Administrativo
  - [ ] Autenticação (apenas PriceADM)
  - [ ] Logs de autenticação
  - [ ] Filtros de data
  - [ ] Estatísticas de logins
  - [ ] Gráficos de análise

## 2. FLUXOS CRÍTICOS

- [ ] Autenticação
  - [ ] Login com credenciais válidas
  - [ ] Bloqueio após 3 tentativas
  - [ ] Mensagens de erro claras
  
- [ ] Upload de Arquivos
  - [ ] XML válido (aceito)
  - [ ] XML inválido (erro tratado)
  - [ ] Arquivo muito grande (limite 200MB)
  - [ ] Formato incorreto (rejeitado)
  
- [ ] Busca e Filtros
  - [ ] Busca com resultados
  - [ ] Busca sem resultados
  - [ ] Filtros combinados
  
- [ ] Downloads
  - [ ] Planilhas geradas corretamente
  - [ ] Formato correto (XLSX)
  - [ ] Nome de arquivo adequado

## 3. UX/UI

- [ ] Contraste de Cores
  - [ ] Texto legível em fundo escuro
  - [ ] Texto legível em fundo claro
  - [ ] Amarelo ouro (#FFDD00) visível
  - [ ] Sem texto branco em fundo branco
  
- [ ] Legibilidade
  - [ ] Fonte adequada
  - [ ] Tamanho de fonte adequado
  - [ ] Espaçamento entre elementos
  - [ ] Hierarquia visual clara
  
- [ ] Feedback Visual
  - [ ] Loading states (spinners)
  - [ ] Mensagens de sucesso (verde)
  - [ ] Mensagens de erro (vermelho)
  - [ ] Mensagens de aviso (amarelo)
  - [ ] Mensagens de info (azul)
  
- [ ] Elementos Visuais
  - [ ] Sem emojis
  - [ ] Sem texto técnico sobreposto
  - [ ] Sem "keyboard_double"
  - [ ] Sem tags [COLCHETES] redundantes
  - [ ] Design profissional

## 4. PERFORMANCE

- [ ] Carregamento Inicial
  - [ ] Tempo < 5 segundos
  - [ ] Cache funcionando
  
- [ ] Operações Pesadas
  - [ ] Upload XML < 3 segundos
  - [ ] Processamento lote < 30 segundos
  - [ ] Busca NCM < 2 segundos
  
- [ ] Responsividade
  - [ ] Interface não trava
  - [ ] Feedback imediato ao usuário

## 5. SEGURANÇA E ERROS

- [ ] Tratamento de Erros
  - [ ] XML corrompido (erro tratado)
  - [ ] Dados inválidos (erro tratado)
  - [ ] Campos vazios (validação)
  - [ ] None/NaN (tratados)
  
- [ ] Validação de Inputs
  - [ ] NCM (8 dígitos)
  - [ ] CFOP (4 dígitos)
  - [ ] CNPJ (14 dígitos + validação)
  
- [ ] Segurança
  - [ ] Autenticação obrigatória
  - [ ] Sessão persistente
  - [ ] Sem exposição de dados sensíveis

## 6. COMPATIBILIDADE

- [ ] Streamlit Cloud
  - [ ] Python 3.13 compatível
  - [ ] Plotly funcionando
  - [ ] Pandas funcionando
  - [ ] Openpyxl funcionando
  
- [ ] Resoluções
  - [ ] Desktop (1920x1080)
  - [ ] Laptop (1366x768)
  - [ ] Tablet (768x1024)

## ISSUES ENCONTRADOS

(Registrar aqui qualquer problema encontrado durante os testes)

---

## APROVAÇÃO FINAL

- [ ] Todos os testes passaram
- [ ] Zero erros críticos
- [ ] Zero erros de UX
- [ ] Performance adequada
- [ ] Pronto para 100 usuários

---

Responsável: P.O. (Product Owner)
Status: EM EXECUÇÃO
