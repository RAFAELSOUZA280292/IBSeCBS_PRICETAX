import streamlit as st
import json
import os
import re

def limpar_formatacao(texto):
    """
    Remove linhas de formatação (===) e outros elementos visuais do texto.
    """
    if not texto:
        return texto
    
    # Remover linhas com 3+ sinais de igual
    lines = texto.split('\n')
    lines_clean = []
    for line in lines:
        if line.count('=') >= 3:
            continue
        lines_clean.append(line)
    
    # Remover linhas vazias excessivas
    texto_limpo = '\n'.join(lines_clean)
    texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
    
    return texto_limpo.strip()

def render_blocos_navigation():
    """
    Renderiza navegação por blocos temáticos da LC 214/2025
    Design simples e funcional
    """
    
    # Carregar blocos
    blocos_path = os.path.join(os.path.dirname(__file__), 'data', 'lc214_blocos_completos.json')
    
    if not os.path.exists(blocos_path):
        st.error("Base de dados de blocos não encontrada. Verifique o deploy.")
        return
    
    with open(blocos_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Suportar formato antigo (lista) e novo (dict com metadados)
    if isinstance(data, dict) and 'blocos' in data:
        blocos = data['blocos']
    else:
        blocos = data
    
    # Cabeçalho com mapeamento de blocos e artigos
    st.markdown("""
    ### 📚 Navegação por Blocos Temáticos
    
    32 blocos comentados pela PriceTax com análise estruturada da LC 214/2025.
    
    **Mapeamento completo:**
    
    | Bloco | Tema | Artigos |
    |-------|------|----------|
    | **01** | Disposições preliminares | 1–4 |
    | **02** | Operações tributáveis | 5–9 |
    | **03** | Contribuintes e responsáveis | 10–11 |
    | **04** | Base de cálculo e alíquotas | 12–15 |
    | **05** | Alíquotas de referência | 16–20 |
    | **06** | Sujeição passiva | 21–27 |
    | **07** | Regimes diferenciados | 28–33 |
    | **08** | Cesta básica nacional | 34–41 |
    | **09** | Cesta estendida | 42–49 |
    | **10** | Saúde e educação | 50–57 |
    | **11** | Serviços financeiros | 58–67 |
    | **12** | Planos de saúde | 68–75 |
    | **13** | Transporte | 76–83 |
    | **14** | Combustíveis e energia | 84–92 |
    | **15** | Bens imóveis | 93–102 |
    | **16** | Economia digital | 103–111 |
    | **17** | Operações internacionais | 112–121 |
    | **18** | Cashback | 122–128 |
    | **19** | Não cumulatividade | 129–137 |
    | **20** | Ressarcimento e compensação | 138–146 |
    | **21** | Obrigações acessórias | 147–158 |
    | **22** | Apuração e recolhimento | 159–170 |
    | **23** | Penalidades | 171–184 |
    | **24** | Processo administrativo | 185–197 |
    | **25** | Comitê Gestor do IBS | 198–214 |
    | **26** | Distribuição de receitas | 215–232 |
    | **27** | Fundos de compensação | 233–250 |
    | **28** | Regimes específicos | 251–268 |
    | **29** | Regimes favorecidos | 269–286 |
    | **30** | Administração da CBS | 287–304 |
    | **31** | Disposições transitórias | 305–330 |
    | **32** | Disposições finais | 331–354 |
    
    ---
    """)
    
    # Dropdown de seleção com títulos corretos do anexo
    from blocos_titulos_map import BLOCOS_TITULOS
    
    bloco_options = {}
    for b in blocos:
        # Usar título correto do mapeamento
        titulo_correto = BLOCOS_TITULOS.get(b['numero'], b['titulo'])
        label = f"Bloco {b['numero']:02d}: {titulo_correto}"
        bloco_options[label] = b['numero'] - 1
    
    selected_label = st.selectbox(
        "Selecione um bloco temático:",
        list(bloco_options.keys()),
        key="bloco_selector"
    )
    
    selected_idx = bloco_options[selected_label]
    bloco = blocos[selected_idx]
    
    # Mapeamento correto de artigos
    from blocos_artigos_map import BLOCOS_ARTIGOS
    artigos_corretos = BLOCOS_ARTIGOS.get(bloco['numero'], bloco['artigos'])
    
    # Exibir bloco selecionado com design simples
    titulo_exibicao = BLOCOS_TITULOS.get(bloco['numero'], bloco['titulo'])
    
    st.markdown("---")
    st.markdown(f"## Bloco {bloco['numero']:02d}")
    st.markdown(f"### {titulo_exibicao}")
    st.markdown(f"**Artigos:** {artigos_corretos}")
    
    # Tags de palavras-chave
    if bloco['palavras_chave']:
        st.markdown("**Temas:** " + " • ".join(bloco['palavras_chave']))
    
    st.markdown("---")
    
    # Seções do bloco
    if bloco['secoes']:
        st.markdown("### 📋 Estrutura do Bloco")
        
        for secao in bloco['secoes']:
            with st.expander(f"{secao['numero']}. {secao['titulo']}", expanded=False):
                conteudo_limpo = limpar_formatacao(secao['conteudo'])
                st.markdown(conteudo_limpo)
    
    # Conteúdo completo
    with st.expander("📄 Ver Conteúdo Completo do Bloco", expanded=False):
        conteudo_completo_limpo = limpar_formatacao(bloco['conteudo_completo'])
        st.markdown(conteudo_completo_limpo)
