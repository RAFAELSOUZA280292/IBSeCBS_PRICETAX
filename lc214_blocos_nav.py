import streamlit as st
import json
import os
import re

# Cores PRICETAX
COLOR_GOLD = "#FFDD00"
COLOR_BLUE = "#0056B3"
COLOR_CARD_BG = "#1E1E1E"
COLOR_TEXT_MAIN = "#FFFFFF"
COLOR_TEXT_MUTED = "#AAAAAA"
COLOR_BORDER = "#333333"

def limpar_formatacao(texto):
    """
    Remove linhas de formatação (===), barras invertidas e outros elementos visuais do texto.
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
    
    texto_limpo = '\n'.join(lines_clean)
    
    # Remover TODAS as barras invertidas
    texto_limpo = texto_limpo.replace('\\', '')
    
    # Substituir ≠ por "não é igual a"
    texto_limpo = texto_limpo.replace('≠', '≠')
    
    # Remover linhas vazias excessivas
    texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
    
    return texto_limpo.strip()

def render_blocos_navigation():
    """
    Renderiza navegação por blocos temáticos da LC 214/2025
    Design profissional PRICETAX
    """
    
    # CSS para ocultar elementos técnicos sobrepostos
    st.markdown("""
    <style>
    /* Ocultar elementos que começam com underscore (IDs técnicos) */
    [id^="_art"],
    [class^="_art"],
    [id*="keyboard"],
    [class*="keyboard"],
    [id*="right"],
    [class*="_right"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        position: absolute !important;
        left: -9999px !important;
    }
    
    /* Garantir que expanders não tenham conteúdo duplicado */
    .streamlit-expanderHeader::before,
    .streamlit-expanderHeader::after {
        content: none !important;
    }
    
    /* Prevenir pseudo-elementos indesejados */
    div[data-testid="stExpander"] *::before,
    div[data-testid="stExpander"] *::after {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
    
    # Cabeçalho profissional
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {COLOR_CARD_BG} 0%, #2a2a2a 100%);
            border-left: 4px solid {COLOR_GOLD};
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        ">
            <h3 style="color: {COLOR_GOLD}; margin: 0 0 0.5rem 0;">
                📚 Navegação por Blocos Temáticos
            </h3>
            <p style="color: {COLOR_TEXT_MUTED}; margin: 0; font-size: 0.95rem;">
                32 blocos comentados pela PriceTax com análise estruturada da LC 214/2025
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Mapeamento em grid compacto (4 colunas)
    st.markdown(
        f"""
        <div style="
            background: {COLOR_CARD_BG};
            border: 1px solid {COLOR_BORDER};
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        ">
            <h4 style="color: {COLOR_TEXT_MAIN}; margin: 0 0 1rem 0; font-size: 1rem;">
                Mapeamento Completo (32 Blocos)
            </h4>
            <div style="
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 0.5rem;
                font-size: 0.85rem;
                color: {COLOR_TEXT_MUTED};
            ">
                <div><strong>01</strong> Dispos. Preliminares (1-4)</div>
                <div><strong>02</strong> Operações Tributáveis (5-9)</div>
                <div><strong>03</strong> Contribuintes (10-11)</div>
                <div><strong>04</strong> Base e Alíquotas (12-15)</div>
                <div><strong>05</strong> Alíq. Referência (16-20)</div>
                <div><strong>06</strong> Sujeição Passiva (21-27)</div>
                <div><strong>07</strong> Regimes Diferenciados (28-33)</div>
                <div><strong>08</strong> Cesta Básica Nacional (34-41)</div>
                <div><strong>09</strong> Cesta Estendida (42-49)</div>
                <div><strong>10</strong> Saúde e Educação (50-57)</div>
                <div><strong>11</strong> Serviços Financeiros (58-67)</div>
                <div><strong>12</strong> Planos de Saúde (68-75)</div>
                <div><strong>13</strong> Transporte (76-83)</div>
                <div><strong>14</strong> Combustíveis e Energia (84-92)</div>
                <div><strong>15</strong> Bens Imóveis (93-102)</div>
                <div><strong>16</strong> Economia Digital (103-111)</div>
                <div><strong>17</strong> Operações Internacionais (112-121)</div>
                <div><strong>18</strong> Cashback (122-128)</div>
                <div><strong>19</strong> Não Cumulatividade (129-137)</div>
                <div><strong>20</strong> Ressarcimento (138-146)</div>
                <div><strong>21</strong> Obrigações Acessórias (147-158)</div>
                <div><strong>22</strong> Apuração e Recolhimento (159-170)</div>
                <div><strong>23</strong> Penalidades (171-184)</div>
                <div><strong>24</strong> Processo Administrativo (185-197)</div>
                <div><strong>25</strong> Comitê Gestor do IBS (198-214)</div>
                <div><strong>26</strong> Distribuição de Receitas (215-232)</div>
                <div><strong>27</strong> Fundos de Compensação (233-250)</div>
                <div><strong>28</strong> Regimes Específicos (251-268)</div>
                <div><strong>29</strong> Regimes Favorecidos (269-286)</div>
                <div><strong>30</strong> Administração da CBS (287-304)</div>
                <div><strong>31</strong> Dispos. Transitórias (305-330)</div>
                <div><strong>32</strong> Dispos. Finais (331-354)</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
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
    
    # Exibir bloco selecionado com design profissional
    titulo_exibicao = BLOCOS_TITULOS.get(bloco['numero'], bloco['titulo'])
    
    # Card do bloco selecionado
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {COLOR_BLUE} 0%, #003d82 100%);
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1.5rem 0;
            border: 1px solid {COLOR_BORDER};
        ">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                <div style="
                    background: {COLOR_GOLD};
                    color: #000;
                    font-weight: bold;
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    font-size: 1.2rem;
                ">
                    {bloco['numero']:02d}
                </div>
                <h2 style="color: {COLOR_TEXT_MAIN}; margin: 0; font-size: 1.5rem;">
                    {titulo_exibicao}
                </h2>
            </div>
            <p style="color: {COLOR_TEXT_MUTED}; margin: 0.5rem 0 0 0; font-size: 0.95rem;">
                <strong>Artigos:</strong> {artigos_corretos}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Tags de palavras-chave
    if bloco['palavras_chave']:
        tags_html = " ".join([
            f'<span style="background: {COLOR_CARD_BG}; color: {COLOR_GOLD}; padding: 0.3rem 0.8rem; border-radius: 12px; font-size: 0.85rem; border: 1px solid {COLOR_BORDER};">{tag}</span>'
            for tag in bloco['palavras_chave']
        ])
        st.markdown(
            f"""
            <div style="margin: 1rem 0; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                {tags_html}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Seções do bloco
    if bloco['secoes']:
        st.markdown(
            f"""
            <h3 style="color: {COLOR_GOLD}; margin: 1.5rem 0 1rem 0; font-size: 1.2rem;">
                📋 Estrutura do Bloco
            </h3>
            """,
            unsafe_allow_html=True
        )
        
        for secao in bloco['secoes']:
            with st.expander(f"**{secao['numero']}.** {secao['titulo']}", expanded=False):
                conteudo_limpo = limpar_formatacao(secao['conteudo'])
                st.markdown(
                    f"""
                    <div style="
                        background: {COLOR_CARD_BG};
                        padding: 1rem;
                        border-radius: 4px;
                        border-left: 3px solid {COLOR_BLUE};
                        color: {COLOR_TEXT_MAIN};
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                        line-height: 1.6;
                    ">
                        {conteudo_limpo}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Conteúdo completo
    st.markdown(
        f"""
        <h3 style="color: {COLOR_GOLD}; margin: 1.5rem 0 1rem 0; font-size: 1.2rem;">
            📄 Conteúdo Completo
        </h3>
        """,
        unsafe_allow_html=True
    )
    
    with st.expander("Ver análise completa do bloco", expanded=False):
        conteudo_completo_limpo = limpar_formatacao(bloco['conteudo_completo'])
        st.markdown(
            f"""
            <div style="
                background: {COLOR_CARD_BG};
                padding: 1.5rem;
                border-radius: 4px;
                border: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT_MAIN};
                line-height: 1.6;
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-wrap: break-word;
            ">
                {conteudo_completo_limpo}
            </div>
            """,
            unsafe_allow_html=True
        )
