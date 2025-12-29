# PROMPT PARA CHATGPT V3 - HIERARQUIA COMPLETA NCM

## ⚠️ ATENÇÃO: TAREFA COMPLEXA - LEIA TODAS AS INSTRUÇÕES

---

## CONTEXTO:

Você receberá `ncm_hierarquia.csv` com 11.091 NCMs e suas descrições **INCREMENTAIS**.

**PROBLEMA:** A TIPI usa descrições hierárquicas onde cada nível só mostra a diferença em relação ao anterior.

**Exemplo:**
```
01022110: "Prenhes ou com cria ao pé"
01022190: "Outros"
```

Mas na verdade:
- **01022110** = Bovinos (0102) + Reprodutores raça pura (0221) + Fêmeas (1) + Prenhes ou com cria ao pé (0)
- **01022190** = Bovinos (0102) + Reprodutores raça pura (0221) + Fêmeas (9) + Outros (0)

**OBJETIVO:** Montar descrição **COMPLETA** concatenando todos os níveis hierárquicos.

---

## ESTRUTURA HIERÁRQUICA DO NCM (8 DÍGITOS):

```
NCM: 01 02 21 90
     │  │  │  │
     │  │  │  └─ Subitem (dígito 8)
     │  │  └──── Item (dígitos 6-7)
     │  └─────── Subposição (dígitos 4-5)
     └────────── Capítulo (dígitos 1-2) + Posição (dígitos 3-4)
```

### Níveis:
1. **Capítulo (2 dígitos):** 01 = Animais vivos
2. **Posição (4 dígitos):** 0102 = Bovinos vivos
3. **Subposição (6 dígitos):** 010221 = Reprodutores raça pura - Fêmeas
4. **Item (7 dígitos):** 0102211 = Prenhes ou com cria ao pé
5. **Subitem (8 dígitos):** 01022110 = (descrição final)

---

## ALGORITMO DE MONTAGEM:

```python
import pandas as pd

df = pd.read_csv("ncm_hierarquia.csv")

# Criar dicionário de descrições por nível
desc_por_nivel = {}

# Ordenar por NCM para processar hierarquicamente
df = df.sort_values('NCM_STR')

def construir_hierarquia(ncm_str, desc_atual):
    """
    Constrói descrição hierárquica completa
    """
    # Extrair níveis
    cap = ncm_str[:2]
    pos = ncm_str[:4]
    subpos = ncm_str[:6]
    item = ncm_str[:7]
    subitem = ncm_str
    
    # Inicializar descrição completa
    desc_completa = []
    
    # NÍVEL 1: Capítulo (mapeamento manual - ver tabela abaixo)
    contexto_cap = MAPA_CAPITULOS.get(cap, "")
    if contexto_cap:
        desc_completa.append(contexto_cap)
    
    # NÍVEL 2: Posição (buscar primeiro NCM da posição)
    if pos not in desc_por_nivel:
        # Buscar primeiro NCM desta posição
        primeiro_pos = df[df['NCM_STR'].str.startswith(pos)].iloc[0]
        desc_pos = primeiro_pos['NCM_DESCRICAO'].strip().lstrip('-').strip()
        desc_por_nivel[pos] = desc_pos
    
    if desc_por_nivel[pos] and desc_por_nivel[pos] != desc_atual:
        desc_completa.append(desc_por_nivel[pos])
    
    # NÍVEL 3: Subposição (buscar primeiro NCM da subposição)
    if len(subpos) == 6 and subpos not in desc_por_nivel:
        primeiro_subpos = df[df['NCM_STR'].str.startswith(subpos)].iloc[0]
        desc_subpos = primeiro_subpos['NCM_DESCRICAO'].strip().lstrip('-').strip()
        if desc_subpos != desc_por_nivel.get(pos, ""):
            desc_por_nivel[subpos] = desc_subpos
    
    if subpos in desc_por_nivel and desc_por_nivel[subpos] != desc_atual:
        desc_completa.append(desc_por_nivel[subpos])
    
    # NÍVEL 4: Item (buscar primeiro NCM do item)
    if len(item) == 7 and item not in desc_por_nivel:
        primeiro_item = df[df['NCM_STR'].str.startswith(item)].iloc[0]
        desc_item = primeiro_item['NCM_DESCRICAO'].strip().lstrip('-').strip()
        if desc_item != desc_por_nivel.get(subpos, ""):
            desc_por_nivel[item] = desc_item
    
    if item in desc_por_nivel and desc_por_nivel[item] != desc_atual:
        desc_completa.append(desc_por_nivel[item])
    
    # NÍVEL 5: Subitem (descrição atual)
    desc_atual_limpa = desc_atual.strip().lstrip('-').strip()
    if desc_atual_limpa and desc_atual_limpa not in desc_completa:
        desc_completa.append(desc_atual_limpa)
    
    # Montar descrição final
    return " - ".join(desc_completa)

# Aplicar para todos os NCMs
df['NCM_DESCRICAO_HIERARQUICA'] = df.apply(
    lambda row: construir_hierarquia(row['NCM_STR'], row['NCM_DESCRICAO']),
    axis=1
)

# Salvar resultado
df[['NCM', 'NCM_DESCRICAO', 'NCM_DESCRICAO_HIERARQUICA']].to_csv(
    'ncm_hierarquia_completa.csv',
    index=False
)

print("✓ Hierarquia completa gerada!")
```

---

## MAPA DE CAPÍTULOS (use no código):

```python
MAPA_CAPITULOS = {
    "01": "Animais vivos",
    "02": "Carnes e miudezas",
    "03": "Peixes e crustáceos",
    "04": "Leite e lacticínios",
    "05": "Produtos de origem animal",
    "06": "Plantas vivas",
    "07": "Produtos hortícolas",
    "08": "Frutas",
    "09": "Café, chá, mate e especiarias",
    "10": "Cereais",
    # ... (use o dicionário completo do prompt anterior)
}
```

---

## REGRAS CRÍTICAS:

### 1. **Evitar Duplicação**
Se a descrição de um nível já está contida no nível anterior, NÃO adicione novamente.

**Exemplo:**
- Posição 0401: "Leite e creme de leite não concentrados"
- Subitem 04011010: "Leite UHT"
- **CORRETO:** "Leite e creme de leite não concentrados - Leite UHT"
- **ERRADO:** "Leite e creme de leite não concentrados - Leite e creme de leite não concentrados - Leite UHT"

### 2. **Preservar Descrições Completas**
Se a descrição original já é completa (> 50 caracteres e não começa com traço), **MANTENHA**.

**Exemplo:**
- 04011010: "Leite UHT (Ultra High Temperature)" → **MANTER ASSIM**

### 3. **Remover Traços Iniciais**
Ao concatenar, remova traços iniciais (-, --, ---) das descrições.

**Exemplo:**
- ANTES: "-- Reprodutores de raça pura"
- DEPOIS: "Reprodutores de raça pura"

### 4. **Separador**
Use " - " (espaço-traço-espaço) para separar níveis.

---

## VALIDAÇÃO OBRIGATÓRIA:

Antes de retornar, verifique estes casos:

### 1. **Bovinos (0102):**
```
01022110: "Animais vivos - Bovinos vivos - Reprodutores raça pura - Fêmeas - Prenhes ou com cria ao pé"
01022190: "Animais vivos - Bovinos vivos - Reprodutores raça pura - Fêmeas - Outros"
01022919: "Animais vivos - Bovinos vivos - Reprodutores raça pura - Machos - Outros"
```

### 2. **Cavalos (0101):**
```
01012100: "Animais vivos - Cavalos vivos - Reprodutores de raça pura"
01012900: "Animais vivos - Cavalos vivos - Outros"
```

### 3. **Leite (0401):**
```
04011010: "Leite UHT (Ultra High Temperature)" (mantido)
04011090: "Leite e lacticínios - Leite e creme de leite não concentrados - Outros"
```

### 4. **Carvão (4402):**
```
44021000: "Madeira e obras de madeira - Carvão vegetal - De bambu"
44022000: "Madeira e obras de madeira - Carvão vegetal - De cascas ou de caroços"
```

---

## FORMATO DE SAÍDA:

Retorne um arquivo CSV com 3 colunas:
```
NCM,NCM_DESCRICAO_ORIGINAL,NCM_DESCRICAO_HIERARQUICA
```

---

## IMPORTANTE:
- Processe TODOS os 11.091 NCMs
- Use o algoritmo Python fornecido acima
- Retorne o CSV completo
- Valide os 4 casos acima antes de retornar

---

**Após processar, retorne o arquivo `ncm_hierarquia_completa.csv` para download.**
