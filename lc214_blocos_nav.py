import streamlit as st
import json
import os

def render_blocos_navigation():
    """
    Renderiza navegação premium por blocos temáticos da LC 214/2025
    Padrão Big Four de qualidade
    """
    
    # Carregar blocos
    blocos_path = os.path.join(os.path.dirname(__file__), 'data', 'lc214_blocos_completos.json')
    
    if not os.path.exists(blocos_path):
        st.error("Base de dados de blocos não encontrada. Verifique o deploy.")
        return
    
    with open(blocos_path, 'r', encoding='utf-8') as f:
        blocos = json.load(f)
    
    # Cores Big Four
    COLOR_BLUE_CORP = "#003366"
    COLOR_GOLD = "#D4AF37"
    COLOR_GRAY = "#4A4A4A"
    COLOR_BORDER = "#E0E0E0"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLOR_BLUE_CORP} 0%, #004080 100%); 
                padding: 2rem; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: white; margin: 0; font-size: 1.8rem; font-weight: 600;">
            📚 Navegação por Blocos Temáticos
        </h2>
        <p style="color: rgba(255,255,255,0.9); margin-top: 0.5rem; font-size: 1rem;">
            36 blocos comentados pela PriceTax | Padrão Big Four de análise jurídica
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Dropdown de seleção
    bloco_options = [f"Bloco {b['numero']:02d}: {b['titulo'][:60]}..." for b in blocos]
    selected_idx = st.selectbox(
        "Selecione um bloco temático:",
        range(len(blocos)),
        format_func=lambda i: bloco_options[i],
        key="bloco_selector"
    )
    
    bloco = blocos[selected_idx]
    
    # Exibir bloco selecionado
    st.markdown(f"""
    <div style="border-left: 4px solid {COLOR_GOLD}; padding-left: 1.5rem; margin: 2rem 0;">
        <h3 style="color: {COLOR_BLUE_CORP}; margin-bottom: 0.5rem;">
            BLOCO {bloco['numero']:02d} — {bloco['titulo']}
        </h3>
        <p style="color: {COLOR_GRAY}; font-size: 0.95rem;">
            <strong>Artigos:</strong> {bloco['artigos']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tags de palavras-chave
    if bloco['palavras_chave']:
        tags_html = " ".join([
            f'<span style="background: {COLOR_GOLD}; color: white; padding: 0.3rem 0.8rem; '
            f'border-radius: 20px; font-size: 0.85rem; margin-right: 0.5rem; display: inline-block; '
            f'margin-bottom: 0.5rem;">{tag}</span>'
            for tag in bloco['palavras_chave']
        ])
        st.markdown(f'<div style="margin-bottom: 1.5rem;">{tags_html}</div>', unsafe_allow_html=True)
    
    # Seções do bloco
    if bloco['secoes']:
        st.markdown(f"### 📋 Estrutura do Bloco")
        
        for secao in bloco['secoes']:
            with st.expander(f"{secao['numero']}. {secao['titulo']}", expanded=False):
                st.markdown(secao['conteudo'])
    
    # Conteúdo completo em accordion
    with st.expander("📄 Ver Conteúdo Completo do Bloco", expanded=False):
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border: 1px solid {COLOR_BORDER}; 
                    border-radius: 8px; max-height: 600px; overflow-y: auto;">
            <pre style="white-space: pre-wrap; font-family: 'Open Sans', sans-serif; 
                        font-size: 0.95rem; color: {COLOR_GRAY}; line-height: 1.6;">
{bloco['conteudo_completo']}
            </pre>
        </div>
        """, unsafe_allow_html=True)

