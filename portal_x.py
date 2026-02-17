"""
Portal X - Portal do Fornecedor Inteligente
Sistema de gestão de cotações com validação fiscal automatizada

Exclusivo para usuário: PriceADM
Desenvolvido por: Rafael Souza
Data: 13/02/2026
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from enum import Enum
import os

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

PORTAL_X_DATA_FILE = "portal_x_cotacoes.json"

class StatusCotacao(Enum):
    """
    Enum para status das cotações
    """
    EM_ANALISE = "em_analise"
    APROVADO = "aprovado"
    REPROVADO = "reprovado"
    AGUARDANDO_NF = "aguardando_nf"
    NF_RECEBIDA = "nf_recebida"
    NF_VALIDADA = "nf_validada"
    NF_RECUSADA = "nf_recusada"

STATUS_COLORS = {
    StatusCotacao.EM_ANALISE: "#FFA500",  # Laranja
    StatusCotacao.APROVADO: "#28A745",     # Verde
    StatusCotacao.REPROVADO: "#DC3545",    # Vermelho
    StatusCotacao.AGUARDANDO_NF: "#FF8C00", # Laranja escuro
    StatusCotacao.NF_RECEBIDA: "#007BFF",  # Azul
    StatusCotacao.NF_VALIDADA: "#6F42C1",  # Roxo
    StatusCotacao.NF_RECUSADA: "#343A40"   # Preto
}

STATUS_LABELS = {
    StatusCotacao.EM_ANALISE: "Em análise",
    StatusCotacao.APROVADO: "Aprovado",
    StatusCotacao.REPROVADO: "Reprovado",
    StatusCotacao.AGUARDANDO_NF: "Aguardando envio de Nota Fiscal",
    StatusCotacao.NF_RECEBIDA: "Nota fiscal recebida",
    StatusCotacao.NF_VALIDADA: "Nota fiscal validada",
    StatusCotacao.NF_RECUSADA: "Nota fiscal recusada"
}

# ============================================================================
# FUNÇÕES DE PERSISTÊNCIA
# ============================================================================

def carregar_cotacoes():
    """
    Carrega cotações do arquivo JSON
    
    Returns:
        dict: Dicionário com todas as cotações
    """
    if os.path.exists(PORTAL_X_DATA_FILE):
        try:
            with open(PORTAL_X_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar cotações: {e}")
            return {}
    return {}

def salvar_cotacoes(cotacoes):
    """
    Salva cotações no arquivo JSON
    
    Args:
        cotacoes (dict): Dicionário com todas as cotações
    """
    try:
        with open(PORTAL_X_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(cotacoes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erro ao salvar cotações: {e}")

def gerar_id_cotacao():
    """
    Gera ID único para cotação
    
    Returns:
        str: ID único no formato COT-YYYYMMDD-HHMMSS
    """
    return f"COT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def render_portal_x():
    """
    Renderiza a interface principal do Portal X
    Exclusivo para usuário PriceADM
    """
    st.title("Portal X - Portal do Fornecedor")
    st.markdown("Sistema de gestão de cotações com validação fiscal automatizada")
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "Nova Cotação",
        "Minhas Cotações",
        "Comparativo",
        "Relatórios"
    ])
    
    with tab1:
        render_nova_cotacao()
    
    with tab2:
        render_minhas_cotacoes()
    
    with tab3:
        render_comparativo()
    
    with tab4:
        render_relatorios()

# ============================================================================
# TAB 1: NOVA COTAÇÃO
# ============================================================================

def render_nova_cotacao():
    """
    Renderiza formulário de nova cotação
    """
    st.header("Cadastrar Nova Cotação")
    
    # Informações do item
    st.subheader("Informações do Item")
    col1, col2 = st.columns(2)
    
    with col1:
        nome_item = st.text_input("Nome do Item", placeholder="Ex: iPhone 17 Pro")
        quantidade = st.number_input("Quantidade", min_value=1, value=1)
    
    with col2:
        ncm = st.text_input("NCM (opcional)", placeholder="Ex: 85171231")
        descricao = st.text_area("Descrição", placeholder="Descrição detalhada do item")
    
    st.divider()
    
    # Número de cotações
    st.subheader("Cotações")
    num_cotacoes = st.number_input(
        "Quantas cotações deseja cadastrar?",
        min_value=2,
        max_value=10,
        value=3,
        help="Cadastre múltiplas cotações para comparar fornecedores"
    )
    
    # Lista para armazenar cotações
    cotacoes_temp = []
    
    # Formulário para cada cotação
    for i in range(num_cotacoes):
        with st.expander(f"Cotação {i+1}", expanded=(i==0)):
            col1, col2 = st.columns(2)
            
            with col1:
                fornecedor = st.text_input(
                    "Nome do Fornecedor",
                    key=f"fornecedor_{i}",
                    placeholder="Ex: Tech Distribuidora"
                )
                cnpj = st.text_input(
                    "CNPJ",
                    key=f"cnpj_{i}",
                    placeholder="00.000.000/0000-00"
                )
                vendedor = st.text_input(
                    "Nome do Vendedor",
                    key=f"vendedor_{i}",
                    placeholder="Ex: João Silva"
                )
                email = st.text_input(
                    "E-mail do Fornecedor",
                    key=f"email_{i}",
                    placeholder="contato@fornecedor.com.br"
                )
            
            with col2:
                numero_cotacao = st.text_input(
                    "Número da Cotação",
                    key=f"num_cot_{i}",
                    placeholder="Ex: COT-2026-001"
                )
                data_cotacao = st.date_input(
                    "Data da Cotação",
                    key=f"data_{i}",
                    value=datetime.now()
                )
                preco_unitario = st.number_input(
                    "Preço Unitário (R$)",
                    key=f"preco_{i}",
                    min_value=0.01,
                    format="%.2f"
                )
                prazo_entrega = st.number_input(
                    "Prazo de Entrega (dias)",
                    key=f"prazo_{i}",
                    min_value=1,
                    value=30
                )
            
            condicoes_pagamento = st.text_area(
                "Condições de Pagamento",
                key=f"pagamento_{i}",
                placeholder="Ex: 30/60/90 dias"
            )
            
            # Armazenar cotação temporária
            cotacoes_temp.append({
                "fornecedor": fornecedor,
                "cnpj": cnpj,
                "vendedor": vendedor,
                "email": email,
                "numero_cotacao": numero_cotacao,
                "data_cotacao": data_cotacao.strftime("%Y-%m-%d"),
                "preco_unitario": preco_unitario,
                "prazo_entrega": prazo_entrega,
                "condicoes_pagamento": condicoes_pagamento
            })
    
    st.divider()
    
    # Botão de salvar
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Salvar Cotações", type="primary", use_container_width=True):
            # Validar campos obrigatórios
            if not nome_item:
                st.error("Nome do item é obrigatório")
                return
            
            # Validar se pelo menos 2 cotações têm fornecedor
            cotacoes_validas = [c for c in cotacoes_temp if c["fornecedor"]]
            if len(cotacoes_validas) < 2:
                st.error("Cadastre pelo menos 2 cotações com fornecedor")
                return
            
            # Gerar ID único
            id_cotacao = gerar_id_cotacao()
            
            # Carregar cotações existentes
            todas_cotacoes = carregar_cotacoes()
            
            # Criar nova entrada
            todas_cotacoes[id_cotacao] = {
                "id": id_cotacao,
                "nome_item": nome_item,
                "quantidade": quantidade,
                "ncm": ncm,
                "descricao": descricao,
                "data_cadastro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cotacoes": cotacoes_validas,
                "status_geral": StatusCotacao.EM_ANALISE.value
            }
            
            # Salvar
            salvar_cotacoes(todas_cotacoes)
            
            st.success(f"Cotações salvas com sucesso! ID: {id_cotacao}")
            st.balloons()
            
            # Limpar formulário (rerun)
            st.rerun()
    
    with col2:
        if st.button("Limpar Formulário", use_container_width=True):
            st.rerun()

# ============================================================================
# TAB 2: MINHAS COTAÇÕES
# ============================================================================

def render_minhas_cotacoes():
    """
    Renderiza lista de cotações cadastradas
    """
    st.header("Minhas Cotações")
    
    # Carregar cotações
    todas_cotacoes = carregar_cotacoes()
    
    if not todas_cotacoes:
        st.info("Nenhuma cotação cadastrada ainda. Cadastre sua primeira cotação na aba 'Nova Cotação'.")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_status = st.selectbox(
            "Filtrar por Status",
            ["Todos"] + [STATUS_LABELS[s] for s in StatusCotacao]
        )
    
    with col2:
        filtro_data = st.selectbox(
            "Período",
            ["Todos", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias"]
        )
    
    with col3:
        busca = st.text_input("Buscar", placeholder="Nome do item ou fornecedor")
    
    st.divider()
    
    # Aplicar filtros
    cotacoes_filtradas = todas_cotacoes.copy()
    
    # Filtro de status
    if filtro_status != "Todos":
        status_key = [k for k, v in STATUS_LABELS.items() if v == filtro_status][0]
        cotacoes_filtradas = {
            k: v for k, v in cotacoes_filtradas.items()
            if v.get("status_geral") == status_key.value
        }
    
    # Filtro de data
    if filtro_data != "Todos":
        dias = {"Últimos 7 dias": 7, "Últimos 30 dias": 30, "Últimos 90 dias": 90}[filtro_data]
        data_limite = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")
        cotacoes_filtradas = {
            k: v for k, v in cotacoes_filtradas.items()
            if v.get("data_cadastro", "")[:10] >= data_limite
        }
    
    # Filtro de busca
    if busca:
        cotacoes_filtradas = {
            k: v for k, v in cotacoes_filtradas.items()
            if busca.lower() in v.get("nome_item", "").lower() or
               any(busca.lower() in c.get("fornecedor", "").lower() for c in v.get("cotacoes", []))
        }
    
    # Exibir cotações
    if not cotacoes_filtradas:
        st.warning("Nenhuma cotação encontrada com os filtros aplicados")
        return
    
    st.write(f"**{len(cotacoes_filtradas)} cotação(ões) encontrada(s)**")
    
    # Listar cotações
    for id_cot, dados in sorted(cotacoes_filtradas.items(), key=lambda x: x[1]["data_cadastro"], reverse=True):
        with st.expander(f"{dados['nome_item']} - {id_cot}"):
            # Status
            status = StatusCotacao(dados.get("status_geral", StatusCotacao.EM_ANALISE.value))
            st.markdown(f"**Status:** <span style='color: {STATUS_COLORS[status]}'>{STATUS_LABELS[status]}</span>", unsafe_allow_html=True)
            
            # Informações gerais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Quantidade:** {dados['quantidade']}")
            with col2:
                st.write(f"**NCM:** {dados.get('ncm', 'N/A')}")
            with col3:
                st.write(f"**Data:** {dados['data_cadastro'][:10]}")
            
            if dados.get('descricao'):
                st.write(f"**Descrição:** {dados['descricao']}")
            
            st.divider()
            
            # Cotações dos fornecedores
            st.write("**Cotações:**")
            for i, cot in enumerate(dados['cotacoes']):
                st.write(f"**{i+1}. {cot['fornecedor']}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"Preço: R$ {cot['preco_unitario']:.2f}")
                with col2:
                    st.write(f"Total: R$ {cot['preco_unitario'] * dados['quantidade']:.2f}")
                with col3:
                    st.write(f"Prazo: {cot['prazo_entrega']} dias")
                with col4:
                    st.write(f"CNPJ: {cot.get('cnpj', 'N/A')}")

# ============================================================================
# TAB 3: COMPARATIVO
# ============================================================================

def render_comparativo():
    """
    Renderiza comparativo de fornecedores
    """
    st.header("Comparativo de Fornecedores")
    st.info("Funcionalidade em desenvolvimento. Em breve você poderá comparar cotações lado a lado.")

# ============================================================================
# TAB 4: RELATÓRIOS
# ============================================================================

def render_relatorios():
    """
    Renderiza relatórios e estatísticas
    """
    st.header("Relatórios e Estatísticas")
    st.info("Funcionalidade em desenvolvimento. Em breve você terá acesso a relatórios detalhados.")
