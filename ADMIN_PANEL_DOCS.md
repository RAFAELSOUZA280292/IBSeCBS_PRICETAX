# Painel Administrativo - Documentação

## Visão Geral

O Painel Administrativo é uma aba exclusiva do sistema PRICETAX que permite ao usuário **PriceADM** visualizar e analisar logs de autenticação de forma profissional e intuitiva.

---

## Acesso

**Usuário autorizado:** `PriceADM`

**Segurança:**
- Dupla camada de controle de acesso
- Aba só aparece para PriceADM
- Validação adicional dentro do módulo
- Mensagem de erro para usuários não autorizados

---

## Funcionalidades

### 1. Métricas Gerais

Painel com 4 métricas principais:

- **Total de Tentativas:** Número total de tentativas de login
- **Logins Bem-Sucedidos:** Quantidade e taxa de sucesso
- **Tentativas Falhas:** Quantidade e taxa de falha
- **Usuários Ativos:** Número de usuários únicos que fizeram login

### 2. Filtros Interativos

**Status:**
- SUCESSO
- FALHA

**Usuário:**
- Lista todos os usuários que tentaram login
- Seleção múltipla

**Período:**
- Todos
- Últimas 24h
- Últimos 7 dias
- Últimos 30 dias

### 3. Visualizações Gráficas

**Gráfico de Pizza - Logins por Status**
- Distribuição entre sucessos e falhas
- Cores: Verde (sucesso) e Vermelho (falha)

**Gráfico de Barras - Logins por Usuário**
- Top 10 usuários com mais tentativas
- Ordenado por quantidade

**Linha do Tempo**
- Evolução de logins ao longo do tempo
- Separado por status (sucesso/falha)
- Visualização diária

### 4. Tabela Detalhada

Exibe todos os registros de log com:
- Data/Hora (formato: DD/MM/YYYY HH:MM:SS)
- Status (SUCESSO ou FALHA)
- Usuário

**Recursos:**
- Ordenação por data (mais recente primeiro)
- Rolagem vertical
- Altura fixa (400px)

### 5. Exportação

**Botão "Exportar CSV":**
- Gera arquivo CSV com logs filtrados
- Nome do arquivo: `logs_autenticacao_YYYYMMDD_HHMMSS.csv`
- Encoding: UTF-8 com BOM (compatível com Excel)
- Colunas: Data/Hora, Status, Usuário

---

## Estrutura de Logs

**Arquivo:** `logs/auth_log.txt`

**Formato:**
```
[YYYY-MM-DD HH:MM:SS] STATUS - Usuário: NOME_USUARIO
```

**Exemplo:**
```
[2026-01-26 16:45:23] SUCESSO - Usuário: PriceADM
[2026-01-26 16:46:10] FALHA - Usuário: teste123
[2026-01-26 16:47:05] SUCESSO - Usuário: JPContabilClientes
```

**Campos:**
- **Timestamp:** Data e hora da tentativa
- **Status:** SUCESSO ou FALHA
- **Usuário:** Nome do usuário (ou "[vazio]" se campo em branco)

---

## Segurança e Privacidade

**Proteção de Dados:**
- Logs não são versionados no GitHub (`.gitignore`)
- Armazenamento apenas no servidor Streamlit Cloud
- Senhas nunca são registradas (apenas hash SHA-256)
- Acesso restrito ao administrador

**Backup:**
- Logs persistem entre restarts do app
- Recomenda-se exportação periódica em CSV

---

## Design Responsivo

**Desktop:**
- Layout em colunas (métricas, gráficos)
- Visualização otimizada para telas grandes

**Mobile:**
- Adaptação automática de gráficos
- Tabela com scroll horizontal se necessário
- Botões touch-friendly

---

## Tecnologias Utilizadas

- **Streamlit:** Framework web
- **Pandas:** Manipulação de dados
- **Plotly:** Gráficos interativos
- **Python datetime:** Processamento de timestamps

---

## Casos de Uso

### 1. Monitoramento de Segurança
- Identificar tentativas de acesso não autorizado
- Detectar padrões de tentativas falhas
- Verificar horários de acesso

### 2. Auditoria
- Rastrear quem acessou o sistema e quando
- Gerar relatórios de uso
- Compliance e conformidade

### 3. Análise de Comportamento
- Identificar usuários mais ativos
- Analisar horários de pico
- Otimizar suporte

---

## Manutenção

**Limpeza de Logs:**
- Logs crescem indefinidamente
- Recomenda-se limpeza manual periódica
- Exportar antes de limpar

**Monitoramento:**
- Verificar tamanho do arquivo periodicamente
- Exportar logs históricos para backup
- Considerar rotação de logs se necessário

---

## Suporte

Para dúvidas ou problemas com o painel administrativo, entre em contato através do WhatsApp: +55 41 99892-4080
