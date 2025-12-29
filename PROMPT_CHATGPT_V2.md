# PROMPT PARA CHATGPT V2 - ENRIQUECIMENTO PRECISO DE DESCRIÇÕES NCM

## ⚠️ ATENÇÃO: LEIA TODAS AS REGRAS ANTES DE PROCESSAR

---

## CONTEXTO:
Você receberá:
1. **ncm_para_enriquecer_v2.csv** - 11.091 NCMs com descrições atuais e coluna POSICAO (4 dígitos)
2. **mapeamento_posicoes_manual.csv** - Mapeamento manual de posições para contextos específicos

**PROBLEMA ANTERIOR:** Enriquecimento genérico misturou contextos (ex: "Madeira e carvão vegetal" para NCMs de madeira).

**OBJETIVO:** Enriquecimento **CIRÚRGICO** e **PRECISO** usando posições de 4 dígitos.

---

## REGRAS CRÍTICAS (OBRIGATÓRIAS):

### 🎯 REGRA 1: PRIORIDADE DE CONTEXTO
1. **SEMPRE** verificar se a POSICAO (4 dígitos) existe no `mapeamento_posicoes_manual.csv`
2. **SE EXISTIR:** Usar o contexto específico do mapeamento
3. **SE NÃO EXISTIR:** Usar contexto genérico do capítulo (2 dígitos)

**Exemplo:**
- NCM 44021000 → POSICAO = 4402 → Mapeamento = "Carvão vegetal" ✓
- NCM 44031100 → POSICAO = 4403 → Mapeamento = "Madeira em bruto" ✓
- NCM 44071100 → POSICAO = 4407 → Mapeamento = "Madeira serrada ou fendida longitudinalmente" ✓

### 🚫 REGRA 2: NUNCA MISTURAR CONTEXTOS
**ERRADO:**
- 44031100: "Madeira e carvão vegetal - De coníferas" ❌
- 44071100: "Madeira e carvão vegetal - Esquadriada" ❌

**CERTO:**
- 44031100: "Madeira em bruto - De coníferas" ✓
- 44071100: "Madeira serrada ou fendida longitudinalmente - Esquadriada" ✓
- 44021000: "Carvão vegetal - De bambu" ✓

### ✅ REGRA 3: PRESERVAR DESCRIÇÕES COMPLETAS
Se a descrição original já é clara e completa (> 40 caracteres e não começa com traço), **NÃO ALTERE**.

**Exemplos que NÃO devem ser alterados:**
- "Leite UHT (Ultra High Temperature)" ✓
- "Queijos e requeijão" ✓
- "Café torrado, não descafeinado" ✓

### 📝 REGRA 4: ENRIQUECER DESCRIÇÕES GENÉRICAS
**Padrões que DEVEM ser enriquecidos:**
- "-- Outros" → "[Contexto da posição] -- Outros"
- "- Outros" → "[Contexto da posição] - Outros"
- "Outros" → "[Contexto da posição] - Outros"
- "- De bambu" → "[Contexto da posição] - De bambu"

### 🔧 REGRA 5: MANTER TRAÇOS HIERÁRQUICOS
**SEMPRE** preservar traços (-, --) que indicam hierarquia na TIPI.

**Exemplo:**
- ANTES: "-- Reprodutores de raça pura"
- DEPOIS: "Cavalos vivos -- Reprodutores de raça pura" ✓

---

## ALGORITMO DE ENRIQUECIMENTO:

```python
import pandas as pd

# 1. Carregar arquivos
df_ncm = pd.read_csv("ncm_para_enriquecer_v2.csv")
df_map = pd.read_csv("mapeamento_posicoes_manual.csv")

# 2. Criar dicionário de mapeamento
mapa_posicoes = dict(zip(df_map['POSICAO'], df_map['CONTEXTO']))

# 3. Dicionário de capítulos (fallback)
mapa_capitulos = {
    "01": "Animais vivos",
    "02": "Carnes e miudezas",
    "03": "Peixes e crustáceos",
    "04": "Leite e lacticínios",
    "05": "Produtos de origem animal",
    "06": "Plantas vivas e produtos de floricultura",
    "07": "Produtos hortícolas",
    "08": "Frutas",
    "09": "Café, chá, mate e especiarias",
    "10": "Cereais",
    "11": "Produtos da indústria de moagem",
    "12": "Sementes e frutos oleaginosos",
    "13": "Gomas, resinas e outros sucos vegetais",
    "14": "Matérias para entrançar",
    "15": "Gorduras e óleos",
    "16": "Preparações de carne ou peixe",
    "17": "Açúcares e produtos de confeitaria",
    "18": "Cacau e suas preparações",
    "19": "Preparações à base de cereais",
    "20": "Preparações de produtos hortícolas",
    "21": "Preparações alimentícias diversas",
    "22": "Bebidas alcoólicas e vinagres",
    "23": "Resíduos das indústrias alimentares",
    "24": "Tabaco e seus sucedâneos",
    "25": "Sal, enxofre, terras e pedras",
    "26": "Minérios, escórias e cinzas",
    "27": "Combustíveis minerais e óleos",
    "28": "Produtos químicos inorgânicos",
    "29": "Produtos químicos orgânicos",
    "30": "Produtos farmacêuticos",
    "31": "Adubos (fertilizantes)",
    "32": "Extratos tanantes e tintoriais",
    "33": "Óleos essenciais e produtos de perfumaria",
    "34": "Sabões e agentes de limpeza",
    "35": "Matérias albuminóides",
    "36": "Pólvoras e explosivos",
    "37": "Produtos para fotografia",
    "38": "Produtos diversos das indústrias químicas",
    "39": "Plásticos e suas obras",
    "40": "Borracha e suas obras",
    "41": "Peles e couros",
    "42": "Obras de couro",
    "43": "Peleteria (peles com pelo)",
    "44": "Madeira e obras de madeira",
    "45": "Cortiça e suas obras",
    "46": "Obras de espartaria ou cestaria",
    "47": "Pastas de madeira",
    "48": "Papel e cartão",
    "49": "Livros, jornais e gravuras",
    "50": "Seda",
    "51": "Lã e pelos finos ou grosseiros",
    "52": "Algodão",
    "53": "Outras fibras têxteis vegetais",
    "54": "Filamentos sintéticos ou artificiais",
    "55": "Fibras sintéticas ou artificiais, descontínuas",
    "56": "Pastas (ouates), feltros e falsos tecidos",
    "57": "Tapetes e outros revestimentos para pavimentos",
    "58": "Tecidos especiais",
    "59": "Tecidos impregnados, revestidos, recobertos ou estratificados",
    "60": "Tecidos de malha",
    "61": "Vestuário e seus acessórios, de malha",
    "62": "Vestuário e seus acessórios, exceto de malha",
    "63": "Outros artefatos têxteis confeccionados",
    "64": "Calçados, polainas e artefatos semelhantes",
    "65": "Chapéus e artefatos de uso semelhante",
    "66": "Guarda-chuvas, sombrinhas e bengalas",
    "67": "Penas e penugem preparadas",
    "68": "Obras de pedra, gesso, cimento",
    "69": "Produtos cerâmicos",
    "70": "Vidro e suas obras",
    "71": "Pérolas, pedras preciosas e metais preciosos",
    "72": "Ferro fundido, ferro e aço",
    "73": "Obras de ferro fundido, ferro ou aço",
    "74": "Cobre e suas obras",
    "75": "Níquel e suas obras",
    "76": "Alumínio e suas obras",
    "78": "Chumbo e suas obras",
    "79": "Zinco e suas obras",
    "80": "Estanho e suas obras",
    "81": "Outros metais comuns",
    "82": "Ferramentas e artefatos de cutelaria",
    "83": "Obras diversas de metais comuns",
    "84": "Reatores, caldeiras, máquinas e aparelhos mecânicos",
    "85": "Máquinas, aparelhos e materiais elétricos",
    "86": "Veículos e material para vias férreas",
    "87": "Veículos automóveis, tratores e ciclos",
    "88": "Aeronaves e aparelhos espaciais",
    "89": "Embarcações e estruturas flutuantes",
    "90": "Instrumentos de óptica, fotografia, medida e controle",
    "91": "Aparelhos de relojoaria",
    "92": "Instrumentos musicais",
    "93": "Armas e munições",
    "94": "Móveis e mobiliário médico-cirúrgico",
    "95": "Brinquedos, jogos e artigos para esporte",
    "96": "Obras diversas",
    "97": "Objetos de arte, coleção e antiguidades"
}

def enriquecer_descricao(row):
    ncm = str(row['NCM']).zfill(8)
    desc = row['NCM_DESCRICAO']
    posicao = row['POSICAO']
    capitulo = ncm[:2]
    
    # REGRA 3: Preservar descrições completas
    if len(desc) > 40 and not desc.startswith('-'):
        return desc
    
    # REGRA 1: Priorizar mapeamento de posição
    if posicao in mapa_posicoes:
        contexto = mapa_posicoes[posicao]
    else:
        # Fallback para capítulo
        contexto = mapa_capitulos.get(capitulo, "Produto")
    
    # REGRA 4: Enriquecer descrições genéricas
    if desc.strip() in ["- Outros", "-- Outros", "--- Outros", "Outros"]:
        return f"{contexto} {desc.strip()}"
    
    # REGRA 5: Manter traços hierárquicos
    if desc.startswith('-'):
        return f"{contexto} {desc}"
    
    # Retornar original se não se encaixar nos padrões
    return desc

# 4. Aplicar enriquecimento
df_ncm['NCM_DESCRICAO_ENRIQUECIDA'] = df_ncm.apply(enriquecer_descricao, axis=1)

# 5. Salvar resultado
df_ncm[['NCM', 'NCM_DESCRICAO', 'NCM_DESCRICAO_ENRIQUECIDA']].to_csv('ncm_enriquecido_v2.csv', index=False)

print("✓ Enriquecimento concluído!")
print(f"Total processado: {len(df_ncm)}")
```

---

## FORMATO DE SAÍDA:

Retorne um arquivo CSV com 3 colunas:
```
NCM,NCM_DESCRICAO_ORIGINAL,NCM_DESCRICAO_ENRIQUECIDA
```

---

## VALIDAÇÃO OBRIGATÓRIA:

Antes de retornar, verifique:

1. **Carvão vegetal (4402):**
   - 44021000: "Carvão vegetal - De bambu" ✓
   - 44022000: "Carvão vegetal - De cascas ou de caroços" ✓
   - 44029000: "Carvão vegetal - Outros" ✓

2. **Madeira em bruto (4403) NÃO deve ter "carvão":**
   - 44031100: "Madeira em bruto - De coníferas" ✓
   - 44031200: "Madeira em bruto - De não coníferas" ✓

3. **Cavalos (0101):**
   - 01012100: "Cavalos vivos -- Reprodutores de raça pura" ✓
   - 01012900: "Cavalos vivos -- Outros" ✓

4. **Leite (0401):**
   - 04011010: "Leite UHT (Ultra High Temperature)" (mantido) ✓
   - 04011090: "Leite e creme de leite não concentrados - Outros" ✓

---

## IMPORTANTE:
- Processe TODOS os 11.091 NCMs
- Use o código Python fornecido acima
- Retorne o CSV completo
- Valide os 4 casos acima antes de retornar

---

**Após processar, retorne o arquivo `ncm_enriquecido_v2.csv` para download.**
