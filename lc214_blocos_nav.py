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
    
    # Cabeçalho com mapeamento de blocos e artigos
    st.markdown("""
    ### 📚 Navegação por Blocos Temáticos
    
    36 blocos comentados pela PriceTax com análise estruturada da LC 214/2025.
    
    **Mapeamento completo:**
    
    | Bloco | Tema | Artigos |
    |-------|------|----------|
    | **01** | Disposições preliminares | 1–3 |
    | **02** | Operações com bens e serviços | 4–13 |
    | **03** | Alíquotas: padrão e referência | 14–20 |
    | **04** | Sujeição passiva | 21–26 |
    | **05** | Extinção do débito | 27–37 |
    | **06** | Pagamento indevido/ressarcimento | 38–40 |
    | **07** | Regimes de apuração | 41–46 |
    | **08** | Não cumulatividade | 47–57 |
    | **09** | Operacionalização | 58–62 |
    | **10** | IBS/CBS na importação | 63–78 |
    | **11** | IBS/CBS na exportação | 79–83 |
    | **12** | Regimes aduaneiros especiais | 84–98 |
    | **13** | ZPE | 99–104 |
    | **14** | Regimes de bens de capital | 105–111 |
    | **15** | Cashback | 112–124 |
    | **16** | Cesta Básica Nacional | 125 |
    | **17** | Regimes diferenciados (regras gerais) | 126–128 |
    | **18** | Redução 60%: Educação e Saúde | 129–130 |
    | **19** | Redução 60%: Dispositivos médicos | 131–134 |
    | **20** | Redução 60%: Alimentos e agro | 135–142 |
    | **21** | Alíquota zero: regras gerais | 143–155 |
    | **22** | Alíquota zero: transporte e reabilitação | 156–163 |
    | **23** | Não contribuintes específicos | 164–171 |
    | **24** | Regime específico: combustíveis | 172–180 |
    | **25** | Regime específico: serviços financeiros | 181–233 |
    | **26** | Regime específico: planos de saúde | 234–250 |
    | **27** | Regime específico: bens imóveis | 251–270 |
    | **28** | Regimes específicos diversos | 271–307 |
    | **29** | Regimes diferenciados da CBS | 308–316 |
    | **30** | Administração IBS/CBS | 317–341 |
    | **31** | Transição: alíquotas 2026–2035 | 342–370 |
    | **32** | Transição: limite redução IBS | 371–383 |
    | **33** | Transição: compensação benefícios ICMS | 384–408 |
    | **34** | Imposto Seletivo (IS) | 409–438 |
    | **35** | ZFM e devolução turista | 439–474 |
    | **36** | Disposições finais | 475–544 |
    
    ---
    """)
    
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
    
    # Mapeamento correto de artigos
    from blocos_artigos_map import BLOCOS_ARTIGOS
    artigos_corretos = BLOCOS_ARTIGOS.get(bloco['numero'], bloco['artigos'])
    
    # Exibir bloco selecionado com design simples
    st.markdown("---")
    st.markdown(f"## Bloco {bloco['numero']:02d}")
    st.markdown(f"### {bloco['titulo']}")
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
                st.markdown(secao['conteudo'])
    
    # Conteúdo completo
    with st.expander("📄 Ver Conteúdo Completo do Bloco", expanded=False):
        st.markdown(bloco['conteudo_completo'])
