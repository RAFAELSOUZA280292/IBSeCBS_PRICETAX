# PROMPT PARA CHATGPT - DICIONÁRIO DE SINÔNIMOS TIPI

## OBJETIVO:

Criar um **dicionário completo de sinônimos** que mapeia **termos populares** (que usuários buscam) para **termos técnicos** (que aparecem na TIPI).

---

## CONTEXTO:

A TIPI (Tabela de Incidência do Imposto sobre Produtos Industrializados) usa nomenclatura técnica e formal que **não corresponde** aos termos que usuários comuns usam.

**Exemplos de problemas:**
- Usuário busca "**linguiça**" → TIPI usa "**enchidos**"
- Usuário busca "**bezerro**" → TIPI usa "**bovinos**"
- Usuário busca "**notebook**" → TIPI usa "**máquinas automáticas para processamento de dados**"

---

## TAREFA:

Analise as **TOP 200 palavras** mais comuns na TIPI (arquivo anexo) e crie um dicionário JSON que mapeia:

**Termo Popular → [Termos Técnicos TIPI]**

---

## CATEGORIAS PRIORITÁRIAS:

### 1. **ALIMENTOS E BEBIDAS**
- Produtos agrícolas (frutas, verduras, grãos)
- Carnes e derivados
- Laticínios
- Bebidas

### 2. **ANIMAIS**
- Animais vivos (gado, aves, peixes)
- Produtos de origem animal

### 3. **TECNOLOGIA**
- Eletrônicos (celular, notebook, tablet)
- Informática
- Telecomunicações

### 4. **VESTUÁRIO**
- Roupas e calçados
- Tecidos e fibras

### 5. **VEÍCULOS**
- Automóveis e peças
- Motocicletas
- Bicicletas

### 6. **CONSTRUÇÃO**
- Materiais de construção
- Ferramentas

### 7. **SAÚDE**
- Medicamentos
- Equipamentos médicos

---

## FORMATO DE SAÍDA:

Retorne um arquivo JSON com esta estrutura:

```json
{
  "alimentos": {
    "linguiça": ["enchidos"],
    "linguica": ["enchidos"],
    "salsicha": ["enchidos"],
    "mortadela": ["enchidos"],
    "presunto": ["presunto"],
    "queijo": ["queijos", "lacticínios"],
    "iogurte": ["iogurte", "lacticínios"],
    "manteiga": ["manteiga", "lacticínios"],
    "arroz": ["arroz", "cereais"],
    "feijão": ["feijão", "leguminosas"],
    "macarrão": ["massas", "pastas alimentícias"],
    "pão": ["pão", "produtos de padaria"]
  },
  "animais": {
    "bezerro": ["bovinos"],
    "bezerros": ["bovinos"],
    "boi": ["bovinos"],
    "vaca": ["bovinos"],
    "gado": ["bovinos"],
    "porco": ["suínos"],
    "frango": ["aves", "galinhas"],
    "peixe": ["peixes"],
    "camarão": ["crustáceos"]
  },
  "tecnologia": {
    "celular": ["telefones", "aparelhos telefônicos"],
    "smartphone": ["telefones", "aparelhos telefônicos"],
    "notebook": ["máquinas automáticas", "computadores"],
    "computador": ["máquinas automáticas", "computadores"],
    "tablet": ["máquinas automáticas", "computadores"],
    "tv": ["aparelhos receptores", "televisão"],
    "televisão": ["aparelhos receptores", "televisão"],
    "monitor": ["monitores", "aparelhos"],
    "impressora": ["máquinas", "impressoras"]
  },
  "vestuario": {
    "camisa": ["camisas", "vestuário"],
    "calça": ["calças", "vestuário"],
    "sapato": ["calçados"],
    "tênis": ["calçados", "tênis"],
    "meia": ["meias", "vestuário"]
  },
  "veiculos": {
    "carro": ["automóveis", "veículos"],
    "moto": ["motocicletas", "veículos"],
    "bicicleta": ["bicicletas", "velocípedes"],
    "pneu": ["pneus", "pneumáticos"]
  },
  "construcao": {
    "cimento": ["cimentos"],
    "tijolo": ["tijolos", "materiais cerâmicos"],
    "tinta": ["tintas", "vernizes"],
    "madeira": ["madeira", "obras"],
    "ferro": ["ferro", "aço"]
  },
  "saude": {
    "remédio": ["medicamentos", "farmacêuticos"],
    "comprimido": ["medicamentos", "farmacêuticos"],
    "vacina": ["vacinas", "farmacêuticos"],
    "seringa": ["seringas", "instrumentos"]
  }
}
```

---

## REGRAS IMPORTANTES:

1. **Seja abrangente:** Inclua variações (singular/plural, com/sem acento)
2. **Seja específico:** Evite termos genéricos demais (ex: "preparações")
3. **Priorize relevância:** Foque em produtos que usuários realmente buscam
4. **Use termos da TIPI:** Os sinônimos devem corresponder a palavras que REALMENTE aparecem nas descrições
5. **Mínimo 100 termos populares** mapeados

---

## DADOS FORNECIDOS:

**Arquivo:** `top_palavras_tipi.txt`
- Top 200 palavras mais comuns na TIPI
- Use como referência para os termos técnicos

---

## VALIDAÇÃO:

Antes de retornar, verifique:
1. ✅ Todos os termos técnicos existem no arquivo `top_palavras_tipi.txt`?
2. ✅ Incluiu variações comuns (singular/plural, com/sem acento)?
3. ✅ Cobriu as 7 categorias prioritárias?
4. ✅ Mínimo de 100 mapeamentos?

---

**Retorne o arquivo `sinonimos_tipi.json` completo.**
