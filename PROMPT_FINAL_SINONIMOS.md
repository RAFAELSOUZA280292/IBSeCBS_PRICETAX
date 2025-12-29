# ⚠️ CORREÇÃO URGENTE - VOCÊ ESTÁ ERRANDO!

## 🔴 PROBLEMAS CRÍTICOS DETECTADOS:

Você está mapeando termos populares para termos **EXTREMAMENTE GENÉRICOS** que retornam **MILHARES** de resultados irrelevantes.

---

## ❌ 6 EXEMPLOS DE ERROS QUE VOCÊ COMETEU:

### **ERRO 1:**
```json
"linguiça": ["carnes"]
```
**Problema:** "carnes" aparece em **146 NCMs** (bovina, suína, frango, peixe, etc)  
**Correto:** `"linguiça": ["enchidos"]` (termo ESPECÍFICO que aparece em 1 NCM)

---

### **ERRO 2:**
```json
"queijo": ["leite"]
```
**Problema:** "leite" aparece em **55 NCMs** (leite UHT, creme de leite, iogurte, etc)  
**Correto:** `"queijo": ["queijos"]` (termo ESPECÍFICO)

---

### **ERRO 3:**
```json
"celular": ["aparelhos", "elétricos"]
```
**Problema:** 
- "aparelhos" aparece em **1.656 NCMs** (TV, rádio, máquinas, etc)
- "elétricos" aparece em **574 NCMs**  

**Correto:** `"celular": ["telefones"]` (termo ESPECÍFICO)

---

### **ERRO 4:**
```json
"frango": ["carnes"]
```
**Problema:** "carnes" é genérico demais  
**Correto:** `"frango": ["aves", "galinhas"]` (termos ESPECÍFICOS)

---

### **ERRO 5:**
```json
"notebook": ["máquinas", "aparelhos"]
```
**Problema:** "máquinas" aparece em **1.655 NCMs** (caldeiras, reatores, etc)  
**Correto:** `"notebook": ["máquinas automáticas"]` (termo COMPLETO e ESPECÍFICO)

---

### **ERRO 6:**
```json
"carro": ["automóveis", "veículos"]
```
**Problema:** "veículos" é genérico (inclui caminhões, motos, tratores)  
**Correto:** `"carro": ["automóveis"]` (apenas automóveis, SEM "veículos")

---

## 🎯 REGRAS OBRIGATÓRIAS:

### 1. **USE TERMOS ESPECÍFICOS, NÃO GENÉRICOS**

**PROIBIDO usar:**
- carnes
- derivados
- lacticínios
- produtos
- preparações
- veículos (use "automóveis" OU "motocicletas", nunca ambos)
- aparelhos (sozinho)
- máquinas (sozinho)
- elétricos (sozinho)

**PERMITIDO usar:**
- enchidos (específico para linguiça/salsicha)
- queijos (específico para queijo)
- bovinos (específico para boi/vaca)
- suínos (específico para porco)
- aves, galinhas (específico para frango)
- telefones (específico para celular)
- máquinas automáticas (específico para computador)
- automóveis (específico para carro)

---

### 2. **CONSULTE O ARQUIVO `top_palavras_tipi.txt`**

Antes de mapear qualquer termo, **VERIFIQUE** se ele existe no arquivo que forneci.

**Exemplo:**
- ✓ "enchidos" está na lista → PODE usar
- ✗ "carnes" está na lista mas é GENÉRICO → NÃO usar
- ✓ "queijos" está na lista → PODE usar
- ✗ "lacticínios" NÃO está na lista → NÃO usar

---

### 3. **PESQUISE NA INTERNET SE NECESSÁRIO**

Use **TODOS os recursos disponíveis**:
- Pesquise "NCM linguiça" no Google
- Pesquise "TIPI enchidos" 
- Pesquise "classificação fiscal linguiça"
- Consulte sites da Receita Federal
- Use seu conhecimento sobre a TIPI

**Você TEM acesso à internet - USE!**

---

### 4. **REVISE ANTES DE ENTREGAR**

Antes de retornar o JSON:

1. ✅ Verifiquei se TODOS os termos técnicos existem em `top_palavras_tipi.txt`?
2. ✅ Evitei termos genéricos (carnes, derivados, lacticínios, preparações)?
3. ✅ Usei termos ESPECÍFICOS (enchidos, queijos, bovinos, suínos)?
4. ✅ Testei mentalmente: "Se buscar 'linguiça', vai retornar APENAS linguiça/salsicha/mortadela?"
5. ✅ Pesquisei na internet casos que tinha dúvida?

---

## 📋 MAPEAMENTOS CORRETOS (USE COMO REFERÊNCIA):

```json
{
  "alimentos_bebidas": {
    "linguiça": ["enchidos"],
    "linguica": ["enchidos"],
    "salsicha": ["enchidos"],
    "salsichas": ["enchidos"],
    "mortadela": ["enchidos"],
    "presunto": ["presunto"],
    "bacon": ["bacon", "toucinho"],
    "queijo": ["queijos"],
    "iogurte": ["iogurte"],
    "manteiga": ["manteiga"],
    "arroz": ["arroz"],
    "feijão": ["feijão"],
    "feijao": ["feijão"],
    "macarrão": ["massas"],
    "macarrao": ["massas"],
    "pão": ["pão"],
    "pao": ["pão"]
  },
  "animais": {
    "bezerro": ["bovinos"],
    "bezerros": ["bovinos"],
    "boi": ["bovinos"],
    "bois": ["bovinos"],
    "vaca": ["bovinos"],
    "vacas": ["bovinos"],
    "gado": ["bovinos"],
    "porco": ["suínos"],
    "porcos": ["suínos"],
    "frango": ["aves", "galinhas"],
    "frangos": ["aves", "galinhas"],
    "galinha": ["aves", "galinhas"],
    "galinhas": ["aves", "galinhas"],
    "peixe": ["peixes"],
    "peixes": ["peixes"],
    "camarão": ["crustáceos"],
    "camarao": ["crustáceos"]
  },
  "tecnologia": {
    "celular": ["telefones"],
    "smartphone": ["telefones"],
    "telefone": ["telefones"],
    "notebook": ["máquinas automáticas"],
    "computador": ["máquinas automáticas"],
    "tablet": ["máquinas automáticas"],
    "tv": ["aparelhos receptores"],
    "televisão": ["aparelhos receptores"],
    "televisao": ["aparelhos receptores"]
  },
  "veiculos": {
    "carro": ["automóveis"],
    "automovel": ["automóveis"],
    "automóvel": ["automóveis"],
    "moto": ["motocicletas"],
    "motocicleta": ["motocicletas"],
    "bicicleta": ["bicicletas"]
  }
}
```

---

## ⚠️ ÚLTIMA CHANCE:

**Refaça TODO o dicionário usando as regras acima.**

**NÃO me retorne outro JSON com termos genéricos.**

**USE A INTERNET para pesquisar casos que você tem dúvida.**

**REVISE linha por linha antes de retornar.**

---

**Retorne `sinonimos_tipi_FINAL.json` CORRETO desta vez.**
