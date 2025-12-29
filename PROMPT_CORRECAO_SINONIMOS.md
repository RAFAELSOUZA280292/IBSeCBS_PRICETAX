# CORREÇÃO DO DICIONÁRIO DE SINÔNIMOS

## PROBLEMA DETECTADO:

Você mapeou termos populares para termos **MUITO GENÉRICOS** que vão retornar **falsos positivos**.

**Exemplos de problemas:**
- `"linguiça": ["carnes", "derivados"]` → Vai retornar TODAS as carnes (boi, frango, peixe)
- `"queijo": ["lacticínios"]` → Vai retornar TODOS os laticínios (leite, iogurte, manteiga)

---

## REGRA CRÍTICA:

**Use APENAS termos ESPECÍFICOS que aparecem nas descrições da TIPI.**

Consulte o arquivo `top_palavras_tipi.txt` que forneci anteriormente e use **EXATAMENTE** as palavras que estão lá.

---

## CORREÇÕES NECESSÁRIAS:

### **ALIMENTOS:**

**ERRADO:**
```json
"linguiça": ["carnes", "derivados"],
"salsicha": ["carnes", "derivados"],
"mortadela": ["carnes", "derivados"]
```

**CORRETO:**
```json
"linguiça": ["enchidos"],
"linguica": ["enchidos"],
"salsicha": ["enchidos"],
"mortadela": ["enchidos"]
```

**ERRADO:**
```json
"queijo": ["lacticínios"],
"iogurte": ["lacticínios"],
"manteiga": ["lacticínios"]
```

**CORRETO:**
```json
"queijo": ["queijos"],
"iogurte": ["iogurte"],
"manteiga": ["manteiga"]
```

**ERRADO:**
```json
"macarrão": ["massas", "pastas"]
```

**CORRETO:**
```json
"macarrão": ["massas"],
"macarrao": ["massas"]
```

---

### **ANIMAIS:**

**ERRADO:**
```json
"gado": ["bovinos", "vivos"],
"boi": ["bovinos", "vivos"],
"vaca": ["bovinos", "vivos"]
```

**CORRETO:**
```json
"gado": ["bovinos"],
"boi": ["bovinos"],
"vaca": ["bovinos"],
"bezerro": ["bovinos"],
"bezerros": ["bovinos"]
```

**ERRADO:**
```json
"frango": ["aves", "vivos"]
```

**CORRETO:**
```json
"frango": ["aves", "galinhas"],
"frangos": ["aves", "galinhas"],
"galinha": ["aves", "galinhas"],
"galinhas": ["aves", "galinhas"]
```

---

### **TECNOLOGIA:**

**ERRADO:**
```json
"celular": ["aparelhos", "elétricos"],
"smartphone": ["aparelhos", "elétricos"]
```

**CORRETO:**
```json
"celular": ["telefones", "aparelhos"],
"smartphone": ["telefones", "aparelhos"],
"telefone": ["telefones", "aparelhos"]
```

**ERRADO:**
```json
"notebook": ["máquinas", "aparelhos"]
```

**CORRETO:**
```json
"notebook": ["máquinas automáticas"],
"computador": ["máquinas automáticas"],
"tablet": ["máquinas automáticas"]
```

---

## PALAVRAS-CHAVE DA TIPI (USE ESTAS):

Consulte `top_palavras_tipi.txt` e use APENAS estas palavras:

**Alimentos:**
- enchidos (para linguiça, salsicha, mortadela)
- queijos (para queijo)
- iogurte (para iogurte)
- manteiga (para manteiga)
- massas (para macarrão)
- cereais (para arroz, trigo)
- peixes (para peixe)
- crustáceos (para camarão, lagosta)

**Animais:**
- bovinos (para boi, vaca, gado, bezerro)
- suínos (para porco)
- aves, galinhas (para frango, galinha)
- ovinos (para carneiro, ovelha)
- caprinos (para cabra, bode)
- cavalos (para cavalo, égua)
- peixes (para peixe)
- crustáceos (para camarão)

**Tecnologia:**
- telefones, aparelhos (para celular, smartphone)
- máquinas automáticas (para notebook, computador)
- aparelhos receptores (para TV, televisão)
- impressoras (para impressora)

---

## TAREFA:

**Revise TODO o arquivo `sinonimos_tipi.json` e corrija TODOS os mapeamentos usando termos ESPECÍFICOS da TIPI.**

**Validação obrigatória:**
1. ✅ Todos os termos técnicos existem em `top_palavras_tipi.txt`?
2. ✅ Evitou termos genéricos (carnes, derivados, lacticínios)?
3. ✅ Usou termos específicos (enchidos, queijos, bovinos)?

---

**Retorne o arquivo `sinonimos_tipi_corrigido.json` completo.**
