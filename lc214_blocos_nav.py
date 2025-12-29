import streamlit as st
import json
import os

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
        blocos = json.load(f)
    
    st.markdown("### 📚 Navegação por Blocos Temáticos")
    st.markdown("36 blocos comentados pela PriceTax com análise estruturada da LC 214/2025")
    
    # Dropdown de seleção com títulos corretos
    bloco_options = {}
    for b in blocos:
        label = f"Bloco {b['numero']:02d}: {b['titulo']}"
        bloco_options[label] = b['numero'] - 1
    
    selected_label = st.selectbox(
        "Selecione um bloco temático:",
        list(bloco_options.keys()),
        key="bloco_selector"
    )
    
    selected_idx = bloco_options[selected_label]
    bloco = blocos[selected_idx]
    
    # Exibir bloco selecionado com design simples
    st.markdown("---")
    st.markdown(f"## Bloco {bloco['numero']:02d}")
    st.markdown(f"### {bloco['titulo']}")
    st.markdown(f"**Artigos:** {bloco['artigos']}")
    
    # Tags de palavras-chave
    if bloco['palavras_chave']:
        st.markdown("**Temas:** " + " • ".join(bloco['palavras_chave']))
    
    st.markdown("---")
    
    # Seções do bloco
    if bloco['secoes']:
        st.markdown("### 📋 Estrutura do Bloco")
        
        for secao in bloco['secoes']:
            with st.expander(f"{secao['numero']}. {secao['titulo']}", expanded=False):
                st.markdown(secao['conteudo'])
    
    # Conteúdo completo
    with st.expander("📄 Ver Conteúdo Completo do Bloco", expanded=False):
        st.markdown(bloco['conteudo_completo'])
