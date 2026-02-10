"""
Menu Lateral Premium - PRICETAX
================================
Menu lateral hierárquico com design premium inspirado em C6 Bank
"""

import streamlit as st


def render_menu_lateral():
    """
    Renderiza menu lateral premium com hierarquia de categorias
    Retorna: string com a página selecionada
    """
    
    # CSS do menu lateral premium
    st.markdown("""
    <style>
    /* Sidebar Premium */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A1A 0%, #000000 100%);
        border-right: 1px solid rgba(255, 221, 0, 0.15);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }
    
    /* Logo PRICETAX no sidebar */
    .sidebar-logo {
        text-align: center;
        padding: 1rem 0 2rem 0;
        border-bottom: 1px solid rgba(255, 221, 0, 0.15);
        margin-bottom: 2rem;
    }
    
    .sidebar-logo h1 {
        color: #FFDD00;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 1px;
    }
    
    .sidebar-logo p {
        color: #999999;
        font-size: 0.75rem;
        margin: 0.25rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Categoria do menu */
    .menu-categoria {
        color: #FFDD00;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 1.5rem 0 0.75rem 0;
        padding: 0 1rem;
    }
    
    /* Item do menu */
    .stRadio > div {
        gap: 0.25rem;
    }
    
    .stRadio > div > label {
        background: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin: 0 !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    .stRadio > div > label:hover {
        background: rgba(255, 221, 0, 0.08) !important;
    }
    
    .stRadio > div > label > div:first-child {
        display: none !important;
    }
    
    .stRadio > div > label > div:last-child {
        color: #CCCCCC !important;
        font-size: 0.9rem !important;
        font-weight: 400 !important;
    }
    
    .stRadio > div > label[data-checked="true"] {
        background: rgba(255, 221, 0, 0.15) !important;
        border-left: 3px solid #FFDD00 !important;
    }
    
    .stRadio > div > label[data-checked="true"] > div:last-child {
        color: #FFDD00 !important;
        font-weight: 500 !important;
    }
    
    /* Badge "Em Construção" */
    .menu-badge {
        display: inline-block;
        background: rgba(255, 221, 0, 0.2);
        color: #FFDD00;
        font-size: 0.65rem;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        margin-left: 0.5rem;
        font-weight: 500;
    }
    
    /* Link externo */
    .menu-link-externo::after {
        content: " ↗";
        color: #FFDD00;
        font-size: 0.8rem;
    }
    
    /* Admin button */
    .admin-button {
        position: fixed;
        bottom: 2rem;
        left: 1rem;
        right: 1rem;
        background: linear-gradient(135deg, #FFDD00 0%, #FFB800 100%);
        color: #000000;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(255, 221, 0, 0.3);
    }
    
    .admin-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(255, 221, 0, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # Logo PRICETAX
        st.markdown("""
        <div class="sidebar-logo">
            <h1>PRICETAX</h1>
            <p>Reforma Tributária</p>
        </div>
        """, unsafe_allow_html=True)
        
        # FERRAMENTAS PRICETAX
        st.markdown('<div class="menu-categoria">FERRAMENTAS PRICETAX</div>', unsafe_allow_html=True)
        
        ferramentas_opcoes = [
            "Simulador Impactos RT",
            "Ranking de Saídas SPED",
            "Índice cClassTrib",
            "Tabela cClassTrib",
            "Correção CFOP/NCM/cClassTrib",
            "Validação Unitária IBS e CBS",
            "Dashboard NFSe Nacional XML",
            "Consulta Fornecedor Unificado",
            "Análise IBS e CBS em Lote",
            "Consulta Fornecedor em Lote 🚧",
            "Ivana I.A. RT 🚧"
        ]
        
        ferramenta = st.radio(
            "ferramentas",
            ferramentas_opcoes,
            label_visibility="collapsed",
            key="menu_ferramentas"
        )
        
        # LEGISLAÇÃO FACILITADA
        st.markdown('<div class="menu-categoria">LEGISLAÇÃO FACILITADA</div>', unsafe_allow_html=True)
        
        legislacao_opcoes = [
            "LC 214/2025",
            "Consulta por Artigo e Palavra Chave",
            "Regimes Especiais e Diferenciados",
            "Perguntas e Respostas"
        ]
        
        legislacao = st.radio(
            "legislacao",
            legislacao_opcoes,
            label_visibility="collapsed",
            key="menu_legislacao"
        )
        
        # NEWS
        st.markdown('<div class="menu-categoria">NEWS</div>', unsafe_allow_html=True)
        if st.button("📰 Notícias PRICETAX", use_container_width=True):
            st.markdown('<meta http-equiv="refresh" content="0; url=https://pricetax.com.br/noticias">', unsafe_allow_html=True)
        
        # ACADEMY
        st.markdown('<div class="menu-categoria">ACADEMY</div>', unsafe_allow_html=True)
        st.button("🎓 Academy (Em Construção)", use_container_width=True, disabled=True)
        
        # ADMIN (só para PriceADM)
        if st.session_state.get("authenticated_user") == "PriceADM":
            st.markdown('<div class="menu-categoria">ADMINISTRAÇÃO</div>', unsafe_allow_html=True)
            admin = st.button("⚙️ Painel Admin", use_container_width=True, type="primary")
            if admin:
                return "Admin"
    
    # Retornar página selecionada
    if ferramenta:
        return ferramenta
    elif legislacao:
        return legislacao
    
    return None


def mapear_pagina_para_aba(pagina_selecionada):
    """
    Mapeia a página selecionada no menu para o índice da aba correspondente
    """
    mapeamento = {
        # Ferramentas
        "Simulador Impactos RT": "link:https://app.pricetax.com.br",
        "Ranking de Saídas SPED": 1,
        "Índice cClassTrib": 2,
        "Tabela cClassTrib": 3,
        "Correção CFOP/NCM/cClassTrib": 0,
        "Validação Unitária IBS e CBS": 4,
        "Dashboard NFSe Nacional XML": 5,
        "Consulta Fornecedor Unificado": 8,
        "Análise IBS e CBS em Lote": 6,
        "Consulta Fornecedor em Lote 🚧": None,
        "Ivana I.A. RT 🚧": None,
        
        # Legislação
        "LC 214/2025": 7,
        "Consulta por Artigo e Palavra Chave": "lc_tab:0",
        "Regimes Especiais e Diferenciados": "lc_tab:1",
        "Perguntas e Respostas": "lc_tab:3",
        
        # Admin
        "Admin": 9
    }
    
    return mapeamento.get(pagina_selecionada)
