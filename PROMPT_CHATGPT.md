# PROMPT PARA CHATGPT - ENRIQUECIMENTO DE DESCRIÇÕES NCM

## CONTEXTO:
Você receberá um arquivo CSV com 11.091 códigos NCM (Nomenclatura Comum do Mercosul) e suas descrições oficiais da TIPI (Tabela de Incidência do Imposto sobre Produtos Industrializados).

**PROBLEMA:** Muitas descrições são genéricas e hierárquicas, dificultando buscas. Exemplo:
- NCM 44021000: "De bambu" → deveria ser "Carvão vegetal de bambu"
- NCM 1012900: "Outros" → deveria ser "Outros cavalos vivos"

## OBJETIVO:
Enriquecer TODAS as 11.091 descrições para torná-las **autossuficientes** e **facilmente encontráveis** em buscas por palavras-chave.

## REGRAS DE ENRIQUECIMENTO:

### 1. MANTER CONTEXTO DO CAPÍTULO
- Use os 2 primeiros dígitos do NCM para identificar o capítulo
- Adicione o contexto do capítulo no início da descrição

**Exemplos de capítulos:**
- 01-05: Animais vivos e produtos de origem animal
- 06-14: Produtos do reino vegetal
- 15: Gorduras e óleos
- 16: Preparações de carne, peixe
- 17: Açúcares e produtos de confeitaria
- 18: Cacau e suas preparações
- 19: Preparações à base de cereais
- 20: Preparações de produtos hortícolas
- 21: Preparações alimentícias diversas
- 22: Bebidas, líquidos alcoólicos e vinagres
- 23: Resíduos das indústrias alimentares
- 24: Tabaco e seus sucedâneos manufaturados
- 25: Sal; enxofre; terras e pedras
- 27: Combustíveis minerais, óleos minerais
- 28: Produtos químicos inorgânicos
- 29: Produtos químicos orgânicos
- 30: Produtos farmacêuticos
- 31: Adubos (fertilizantes)
- 32: Extratos tanantes e tintoriais
- 33: Óleos essenciais e resinóides; produtos de perfumaria
- 34: Sabões, agentes orgânicos de superfície
- 35: Matérias albuminóides; produtos à base de amidos
- 36: Pólvoras e explosivos
- 37: Produtos para fotografia e cinematografia
- 38: Produtos diversos das indústrias químicas
- 39: Plásticos e suas obras
- 40: Borracha e suas obras
- 41: Peles, exceto a peleteria (peles com pelo), e couros
- 42: Obras de couro
- 43: Peleteria (peles com pelo) e suas obras
- 44: Madeira, carvão vegetal e obras de madeira
- 45: Cortiça e suas obras
- 46: Obras de espartaria ou de cestaria
- 47: Pastas de madeira ou de outras matérias fibrosas celulósicas
- 48: Papel e cartão
- 49: Livros, jornais, gravuras
- 50-63: Têxteis e suas obras
- 64: Calçados, polainas e artefatos semelhantes
- 65: Chapéus e artefatos de uso semelhante
- 66: Guarda-chuvas, sombrinhas, bengalas
- 67: Penas e penugem preparadas
- 68: Obras de pedra, gesso, cimento, amianto, mica
- 69: Produtos cerâmicos
- 70: Vidro e suas obras
- 71: Pérolas naturais ou cultivadas, pedras preciosas
- 72: Ferro fundido, ferro e aço
- 73: Obras de ferro fundido, ferro ou aço
- 74: Cobre e suas obras
- 75: Níquel e suas obras
- 76: Alumínio e suas obras
- 78: Chumbo e suas obras
- 79: Zinco e suas obras
- 80: Estanho e suas obras
- 81: Outros metais comuns
- 82: Ferramentas, artefatos de cutelaria e talheres, de metais comuns
- 83: Obras diversas de metais comuns
- 84: Reatores nucleares, caldeiras, máquinas, aparelhos e instrumentos mecânicos
- 85: Máquinas, aparelhos e materiais elétricos
- 86: Veículos e material para vias férreas
- 87: Veículos automóveis, tratores, ciclos
- 88: Aeronaves e aparelhos espaciais
- 89: Embarcações e estruturas flutuantes
- 90: Instrumentos e aparelhos de óptica, fotografia, cinematografia, medida, controle ou de precisão
- 91: Aparelhos de relojoaria
- 92: Instrumentos musicais
- 93: Armas e munições
- 94: Móveis; mobiliário médico-cirúrgico; colchões, almofadas
- 95: Brinquedos, jogos, artigos para divertimento ou para esporte
- 96: Obras diversas
- 97: Objetos de arte, de coleção e antiguidades

### 2. PADRÕES DE ENRIQUECIMENTO

**Para descrições genéricas:**
- "Outros" → "[Produto do capítulo] - Outros"
- "Demais" → "[Produto do capítulo] - Demais"
- "Não especificados" → "[Produto do capítulo] não especificados"

**Para descrições incompletas:**
- "De bambu" → "[Produto principal] de bambu"
- "Com motor" → "[Produto principal] com motor"
- "Elétricos" → "[Produto principal] elétricos"

**Para descrições técnicas:**
- Manter termos técnicos, mas adicionar contexto
- "Potenciômetro de carvão" → OK (já está claro)
- "De carvão" → "Cortadores de carvão" (adicionar verbo/substantivo)

### 3. MANTER ESTRUTURA HIERÁRQUICA
- Preservar traços (-, --) que indicam nível hierárquico
- Adicionar contexto ANTES dos traços

**Exemplo:**
- ANTES: "-- Reprodutores de raça pura"
- DEPOIS: "Cavalos vivos -- Reprodutores de raça pura"

### 4. EVITAR REDUNDÂNCIA
- Se a descrição já é clara e completa, NÃO altere
- Exemplos que NÃO precisam de alteração:
  - "Leite e creme de leite, concentrados"
  - "Queijos e requeijão"
  - "Café torrado, não descafeinado"

## FORMATO DE SAÍDA:

Retorne um arquivo CSV com 3 colunas:
```
NCM,NCM_DESCRICAO_ORIGINAL,NCM_DESCRICAO_ENRIQUECIDA
```

**Exemplo:**
```csv
NCM,NCM_DESCRICAO_ORIGINAL,NCM_DESCRICAO_ENRIQUECIDA
44021000,- De bambu,Carvão vegetal - De bambu
44022000,- De cascas ou de caroços,Carvão vegetal - De cascas ou de caroços
44029000,- Outros,Carvão vegetal - Outros
1012900,-- Outros,Cavalos vivos -- Outros
84303110,Cortadores de carvão ou de rocha,Cortadores de carvão ou de rocha
```

## INSTRUÇÕES DE PROCESSAMENTO:

1. Faça o upload do arquivo `ncm_para_enriquecer.csv`
2. Processe TODOS os 11.091 NCMs
3. Use Python/Pandas para automatizar o processo
4. Retorne o CSV completo para download

## CÓDIGO SUGERIDO (OPCIONAL):

```python
import pandas as pd

# Carregar CSV
df = pd.read_csv("ncm_para_enriquecer.csv")

# Dicionário de contextos por capítulo (primeiros 2 dígitos)
contextos = {
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
    "44": "Madeira e carvão vegetal",
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
    ncm = str(row['NCM'])
    desc = row['NCM_DESCRICAO']
    cap = ncm[:2]
    
    # Se já está completa, não alterar
    if len(desc) > 40 and not desc.startswith('-'):
        return desc
    
    # Pegar contexto do capítulo
    contexto = contextos.get(cap, "Produto")
    
    # Enriquecer descrições genéricas
    if desc.strip() in ["- Outros", "-- Outros", "--- Outros", "Outros"]:
        return f"{contexto} - Outros"
    
    # Enriquecer descrições que começam com traço
    if desc.startswith('-'):
        return f"{contexto} {desc}"
    
    # Retornar original se não se encaixar nos padrões
    return desc

# Aplicar enriquecimento
df['NCM_DESCRICAO_ENRIQUECIDA'] = df.apply(enriquecer_descricao, axis=1)

# Salvar resultado
df[['NCM', 'NCM_DESCRICAO', 'NCM_DESCRICAO_ENRIQUECIDA']].to_csv('ncm_enriquecido.csv', index=False)
```

## IMPORTANTE:
- Processe TODOS os 11.091 NCMs
- Retorne o CSV completo
- Mantenha a estrutura hierárquica (traços)
- Seja consistente nas escolhas de contexto
- Priorize clareza e facilidade de busca

---

**Após processar, retorne o arquivo `ncm_enriquecido.csv` para download.**
