# Mapeamento Estrutural de XML NFSe - Portal Nacional

## Análise Realizada
**Data:** 23 de Janeiro de 2026  
**Arquivos Analisados:** 3 XMLs de NFSe  
**Padrão:** Portal Nacional (SPED)

---

## Estrutura Hierárquica do XML

```
NFSe (root)
├── infNFSe
│   ├── Dados da Nota Emitida
│   ├── emit (Emitente)
│   ├── valores (Resumo Financeiro)
│   └── DPS (Declaração de Prestação de Serviços)
│       ├── infDPS
│       │   ├── prest (Prestador)
│       │   ├── toma (Tomador)
│       │   ├── serv (Serviço)
│       │   └── valores (Detalhamento Financeiro)
│       │       ├── vServPrest
│       │       └── trib (Tributos)
│       │           ├── tribMun (ISSQN)
│       │           ├── tribFed (PIS/COFINS/IRRF/CSLL)
│       │           └── totTrib
└── Signature (Assinatura Digital)
```

---

## Campos Mapeados por Categoria

### 1. Identificação da Nota (infNFSe)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `nNFSe` | Número da NFSe | 438 | Sim |
| `nDFSe` | Número do Documento Fiscal | 7617597 | Sim |
| `cStat` | Status da Nota (100=Autorizada) | 100 | Sim |
| `dhProc` | Data/Hora de Processamento | 2026-01-20T14:22:50-03:00 | Sim |
| `xLocEmi` | Local de Emissão | Curitiba | Sim |
| `xLocPrestacao` | Local de Prestação | Curitiba | Sim |
| `cLocIncid` | Código Município Incidência | 4106902 | Sim |
| `xLocIncid` | Nome Município Incidência | Curitiba | Sim |
| `ambGer` | Ambiente (1=Produção, 2=Homologação) | 2 | Sim |
| `tpEmis` | Tipo de Emissão (1=Normal) | 1 | Sim |
| `procEmi` | Processo de Emissão (2=Web) | 2 | Sim |
| `verAplic` | Versão do Aplicativo | EmissorWeb_1.5.0.0 | Sim |

### 2. Emitente (emit)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `CNPJ` | CNPJ do Emitente | 00965356000160 | Sim |
| `IM` | Inscrição Municipal | 3198125 | Sim |
| `xNome` | Razão Social | SUPPORT ENGENHARIA LTDA | Sim |
| `enderNac/xLgr` | Logradouro | R. PROFESSOR JOAQUIM DE MATTOS BARRETO | Sim |
| `enderNac/nro` | Número | 000443 | Sim |
| `enderNac/xBairro` | Bairro | São Lourenço | Sim |
| `enderNac/cMun` | Código Município | 4106902 | Sim |
| `enderNac/UF` | UF | PR | Sim |
| `enderNac/CEP` | CEP | 82200210 | Sim |
| `fone` | Telefone | 4133525055 | Não |
| `email` | Email | helena@support.com.br | Não |

### 3. Tomador (toma - dentro de DPS/infDPS)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `CNPJ` ou `CPF` | CNPJ/CPF do Tomador | 34622881000102 | Sim |
| `xNome` | Razão Social/Nome | WINITY S.A. | Sim |
| `end/endNac/cMun` | Código Município | 3550308 | Sim |
| `end/endNac/CEP` | CEP | 04534013 | Sim |
| `end/xLgr` | Logradouro | JOAQUIM FLORIANO | Sim |
| `end/nro` | Número | 913 | Sim |
| `end/xCpl` | Complemento | CONJ  31 E 32 | Não |
| `end/xBairro` | Bairro | ITAIM BIBI | Sim |
| `email` | Email | (varia) | Não |

### 4. Serviço (serv - dentro de DPS/infDPS)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `locPrest/cLocPrestacao` | Código Local Prestação | 4106902 | Sim |
| `cServ/cTribNac` | Código Tributação Nacional | 070302 | Sim |
| `cServ/xDescServ` | Descrição do Serviço | Elaboração de projetos... | Sim |
| `cServ/cNBS` | Código NBS | 114032500 | Sim |
| `xTribNac` | Descrição Tributação Nacional | Elaboração de anteprojetos... | Sim |
| `xNBS` | Descrição NBS | Serviços de engenharia... | Sim |

### 5. Valores Resumidos (valores - dentro de infNFSe)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `vBC` | Valor Base de Cálculo | 7714.63 | Sim |
| `pAliqAplic` | Alíquota ISSQN Aplicada | 5.00 | Não* |
| `vISSQN` | Valor ISSQN | 652.28 | Não* |
| `vTotalRet` | Valor Total Retido | 474.46 | Sim |
| `vLiq` | Valor Líquido | 7240.17 | Sim |

*Nota: Campos `pAliqAplic` e `vISSQN` aparecem apenas quando ISSQN não é retido

### 6. Valores Detalhados (valores - dentro de DPS/infDPS)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `vServPrest/vServ` | Valor do Serviço Prestado | 7714.63 | Sim |

### 7. Tributos Municipais (tribMun)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `tribISSQN` | Tributação ISSQN (1=Sim) | 1 | Sim |
| `tpRetISSQN` | Tipo Retenção ISSQN (1=Retido, 2=Não Retido) | 1 | Sim |

### 8. Tributos Federais (tribFed)

#### PIS/COFINS (piscofins)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `CST` | Código Situação Tributária | 01 | Sim |
| `vBCPisCofins` | Base de Cálculo PIS/COFINS | 7714.63 | Sim |
| `pAliqPis` | Alíquota PIS (%) | 0.65 | Sim |
| `pAliqCofins` | Alíquota COFINS (%) | 3.00 | Sim |
| `vPis` | Valor PIS | 50.15 | Sim |
| `vCofins` | Valor COFINS | 231.44 | Sim |
| `tpRetPisCofins` | Tipo Retenção (1=Retido, 2=Não Retido) | 1 | Sim |

#### Outros Tributos Federais

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `vRetIRRF` | Valor IRRF Retido | 115.72 | Não |
| `vRetCSLL` | Valor CSLL Retido | 77.15 | Não |

### 9. Total de Tributos (totTrib/pTotTrib)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `pTotTribFed` | % Total Tributos Federais | 11.33 | Sim |
| `pTotTribEst` | % Total Tributos Estaduais | 0.00 | Sim |
| `pTotTribMun` | % Total Tributos Municipais | 0.00 | Sim |

### 10. Dados do DPS (infDPS)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `tpAmb` | Tipo Ambiente (1=Produção) | 1 | Sim |
| `dhEmi` | Data/Hora Emissão | 2026-01-20T14:22:50-03:00 | Sim |
| `serie` | Série do DPS | 900 | Sim |
| `nDPS` | Número do DPS | 878 | Sim |
| `dCompet` | Data de Competência | 2026-01-20 | Sim |
| `tpEmit` | Tipo de Emitente (1=Prestador) | 1 | Sim |
| `cLocEmi` | Código Local Emissão | 4106902 | Sim |

### 11. Regime Tributário (regTrib - dentro de prest)

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| `opSimpNac` | Optante Simples Nacional (1=Sim) | 1 | Sim |
| `regEspTrib` | Regime Especial Tributação | 6 | Sim |

---

## Status da Nota Fiscal

### Códigos de Status (cStat)

| Código | Descrição | Status |
|--------|-----------|--------|
| 100 | NFSe Autorizada | Ativa |
| 101 | NFSe Cancelada | Cancelada |
| 102 | NFSe Substituída | Substituída |

---

## Regras de Negócio Identificadas

### 1. Retenção de Tributos

**ISSQN:**
- `tpRetISSQN = 1`: ISSQN retido pelo tomador
- `tpRetISSQN = 2`: ISSQN não retido (pago pelo prestador)

**PIS/COFINS:**
- `tpRetPisCofins = 1`: Retido pelo tomador
- `tpRetPisCofins = 2`: Não retido

### 2. Cálculo de Valores

```
Valor Líquido = Valor Base de Cálculo - Valor Total Retido

Valor Total Retido = PIS + COFINS + IRRF + CSLL + ISSQN (se retido)
```

### 3. Identificação de Pessoa (Tomador)

- Se `CNPJ` presente → Pessoa Jurídica
- Se `CPF` presente → Pessoa Física

---

## Campos para Dashboard

### Métricas Principais

1. **Total de Notas:** Contagem de XMLs processados
2. **Valor Total Bruto:** Soma de `vBC`
3. **Valor Total Líquido:** Soma de `vLiq`
4. **Total Retido:** Soma de `vTotalRet`
5. **Total PIS:** Soma de `vPis`
6. **Total COFINS:** Soma de `vCofins`
7. **Total IRRF:** Soma de `vRetIRRF`
8. **Total CSLL:** Soma de `vRetCSLL`
9. **Total ISSQN:** Soma de `vISSQN` (quando presente)

### Filtros Sugeridos

- **Período:** Por `dhEmi` ou `dCompet`
- **Status:** Por `cStat`
- **Tomador:** Por `toma/xNome` ou `toma/CNPJ`
- **Município:** Por `xLocPrestacao`
- **Retenção:** Por `tpRetISSQN` e `tpRetPisCofins`

### Gráficos Sugeridos

1. **Evolução Temporal:** Valor bruto por mês
2. **Distribuição de Tributos:** Pizza com PIS, COFINS, IRRF, CSLL, ISSQN
3. **Top Tomadores:** Ranking por valor total
4. **Status das Notas:** Ativas vs Canceladas vs Substituídas

---

## Observações Técnicas

### Namespace XML
```xml
xmlns="http://www.sped.fazenda.gov.br/nfse"
```

### Versões Identificadas
- NFSe versão 1.00
- NFSe versão 1.01
- DPS versão 1.00
- DPS versão 1.01

### Assinatura Digital
Todos os XMLs contêm assinatura digital XML (XMLDSig) com:
- Algoritmo: RSA-SHA256
- Certificado: Sectigo Public Server Authentication CA OV R36

---

## Próximos Passos

1. ✓ Estrutura mapeada
2. [ ] Criar módulo parser Python
3. [ ] Implementar validação de schema
4. [ ] Construir dashboard interativo
5. [ ] Adicionar exportação CSV/Excel
6. [ ] Integrar na aplicação PRICETAX

---

**Documentado por:** Manus AI (Programador Sênior)  
**Versão:** 1.0
