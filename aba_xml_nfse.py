"""
aba_xml_nfse.py
===============

Módulo da aba de Análise de XML NFSe para o sistema PRICETAX.

Este módulo fornece uma interface completa para upload, análise e visualização
de XMLs de Nota Fiscal de Serviços Eletrônica (NFSe) do Portal Nacional.

Funcionalidades:
- Upload de múltiplos XMLs
- Dashboard executivo com métricas consolidadas
- Tabela interativa com todas as notas
- Filtros por período, status e tomador
- Gráficos de evolução temporal e distribuição de tributos
- Relatório detalhado por nota fiscal
- Exportação para CSV

Autor: PRICETAX
Data: 23 de Janeiro de 2026
Versão: 1.0
"""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from typing import List, Dict, Any
import io
import tempfile
from pathlib import Path

# Importar parser NFSe
from parser_nfse import parse_nfse_xml, parse_multiple_nfse, format_currency, format_percentage


def render_aba_xml_nfse():
    """
    Renderiza a aba completa de Análise de XML NFSe.
    """
    
    st.markdown(
        """
        <div class="pricetax-card">
            <h2>Análise de XML NFSe</h2>
            <p>
                Faça upload de um ou múltiplos XMLs de Nota Fiscal de Serviços Eletrônica (NFSe)
                do Portal Nacional para análise detalhada de tributos, valores e tomadores.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # ===========================================================================
    # UPLOAD DE ARQUIVOS
    # ===========================================================================
    
    st.markdown("### Upload de Arquivos XML")
    
    uploaded_files = st.file_uploader(
        "Selecione um ou mais arquivos XML de NFSe",
        type=["xml"],
        accept_multiple_files=True,
        help="Arraste e solte os arquivos XML ou clique para selecionar. Você pode selecionar múltiplos arquivos.",
    )
    
    if not uploaded_files:
        st.info(
            "Aguardando upload de arquivos XML. "
            "Você pode fazer upload de um ou vários arquivos simultaneamente."
        )
        return
    
    # ===========================================================================
    # PROCESSAMENTO DOS XMLS
    # ===========================================================================
    
    with st.spinner(f"Processando {len(uploaded_files)} arquivo(s) XML..."):
        # Salvar arquivos temporariamente para processamento
        temp_paths = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_paths.append(tmp_file.name)
        
        # Processar XMLs
        notas = parse_multiple_nfse(temp_paths)
        
        # Limpar arquivos temporários
        for temp_path in temp_paths:
            Path(temp_path).unlink(missing_ok=True)
    
    if not notas:
        st.error("Nenhum XML foi processado com sucesso. Verifique se os arquivos estão no formato correto.")
        return
    
    st.success(f"{len(notas)} nota(s) fiscal(is) processada(s) com sucesso!")
    
    # ===========================================================================
    # CONVERSÃO PARA DATAFRAME
    # ===========================================================================
    
    df_notas = criar_dataframe_notas(notas)
    
    # ===========================================================================
    # DASHBOARD EXECUTIVO
    # ===========================================================================
    
    st.markdown("---")
    st.markdown("### Dashboard Executivo")
    
    render_dashboard(df_notas, notas)
    
    # ===========================================================================
    # FILTROS
    # ===========================================================================
    
    st.markdown("---")
    st.markdown("### Filtros")
    
    df_filtrado = aplicar_filtros(df_notas)
    
    # ===========================================================================
    # TABELA DE NOTAS
    # ===========================================================================
    
    st.markdown("---")
    st.markdown(f"### Notas Fiscais ({len(df_filtrado)} registros)")
    
    # Alerta de autenticidade
    st.info(
        "**Validação de Autenticidade:** "
        "A autenticidade destes documentos deve ser verificada no Portal Nacional da NFSe. "
        "Atualmente, os XMLs não contêm eventos de cancelamento. "
        "Para consulta oficial, acesse: [Portal Nacional NFSe](https://www.nfse.gov.br/consultapublica)"
    )
    
    render_tabela_notas(df_filtrado)
    
    # ===========================================================================
    # GRÁFICOS
    # ===========================================================================
    
    if len(df_filtrado) > 0:
        st.markdown("---")
        st.markdown("### Análise Gráfica")
        
        render_graficos(df_filtrado)
    
    # ===========================================================================
    # RELATÓRIO DETALHADO POR NOTA
    # ===========================================================================
    
    st.markdown("---")
    st.markdown("### Relatório Detalhado por Nota")
    
    render_relatorio_detalhado(df_filtrado, notas)
    
    # ===========================================================================
    # EXPORTAÇÃO
    # ===========================================================================
    
    st.markdown("---")
    st.markdown("### Exportação de Dados")
    
    render_exportacao(df_filtrado, notas)


def criar_dataframe_notas(notas: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Converte lista de notas para DataFrame do pandas.
    
    Args:
        notas: Lista de dicionários com dados das NFSe
    
    Returns:
        pd.DataFrame: DataFrame com dados tabulares
    """
    rows = []
    
    for nota in notas:
        row = {
            # Identificação
            "Chave de Acesso": nota["chave_acesso"],
            "Número NFSe": nota["numero_nfse"],
            "Status": nota["status"],
            "Data Emissão": nota["data_emissao"],
            
            # Prestador (Emitente)
            "Nome Prestador": nota["emitente"]["razao_social"],
            "CNPJ/CPF Prestador": nota["emitente"]["cnpj"],
            
            # Tomador
            "Nome Tomador": nota["tomador"]["razao_social_nome"],
            "CNPJ/CPF Tomador": nota["tomador"]["cnpj_cpf"],
            
            # Serviço
            "Código NBS": nota["servico"]["codigo_nbs"],
            "Descrição NBS": nota["servico"]["descricao_nbs"],
            "Código Tributação Nacional": nota["servico"]["codigo_tributacao_nacional"],
            "Descrição Tributação Nacional": nota["servico"]["descricao_tributacao_nacional"],
            
            # Valores
            "Valor Bruto": nota["valor_bruto"],
            
            # Tributos NÃO Retidos
            "CST PIS": nota["pis"]["cst"],
            "Alíquota PIS": nota["pis"]["aliquota"],
            "Valor PIS": nota["pis"]["valor"],
            
            "CST COFINS": nota["cofins"]["cst"],
            "Alíquota COFINS": nota["cofins"]["aliquota"],
            "Valor COFINS": nota["cofins"]["valor"],
            
            # Tributos Retidos
            "ISS Retido": "Sim" if nota["issqn"]["retido"] else "Não",
            "BC ISS": nota["valor_bruto"],  # Base de cálculo do ISS é o valor bruto
            "Alíquota ISS": nota["issqn"]["aliquota"],
            "Valor ISS": nota["issqn"]["valor"],
            
            "IRRF Retido": nota["irrf"]["valor"],
            "CSLL Retido": nota["csll"]["valor"],
            "PIS Retido": nota["pis"]["valor"] if nota["pis"]["retido"] else 0.0,
            "COFINS Retido": nota["cofins"]["valor"] if nota["cofins"]["retido"] else 0.0,
            
            # Outros
            "Valor Líquido": nota["valor_liquido"],
            "Total Retido": nota["valor_total_retido"],
            "Município": nota["localizacao"]["local_prestacao"],
            "Simples Nacional": "Sim" if nota["regime"]["optante_simples_nacional"] else "Não",
            "Arquivo": nota["arquivo_original"],
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Converter data de emissão para datetime para ordenação
    try:
        df["Data Emissão Datetime"] = pd.to_datetime(df["Data Emissão"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    except:
        df["Data Emissão Datetime"] = pd.NaT
    
    # Ordenar por data de emissão (mais recente primeiro)
    df = df.sort_values("Data Emissão Datetime", ascending=False).reset_index(drop=True)
    
    return df


def render_dashboard(df: pd.DataFrame, notas: List[Dict[str, Any]]):
    """
    Renderiza dashboard executivo com métricas consolidadas.
    
    Args:
        df: DataFrame com notas fiscais
        notas: Lista original de notas (para dados adicionais)
    """
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total de Notas",
            value=f"{len(df):,}".replace(",", "."),
        )
    
    with col2:
        total_bruto = df["Valor Bruto"].sum()
        st.metric(
            label="Valor Total Bruto",
            value=format_currency(total_bruto),
        )
    
    with col3:
        total_liquido = df["Valor Líquido"].sum()
        st.metric(
            label="Valor Total Líquido",
            value=format_currency(total_liquido),
        )
    
    with col4:
        total_retido = df["Total Retido"].sum()
        st.metric(
            label="Total Retido",
            value=format_currency(total_retido),
        )
    
    # Métricas de tributos
    st.markdown("#### Tributos Consolidados")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_pis = df["Valor PIS"].sum()
        st.metric(
            label="Total PIS",
            value=format_currency(total_pis),
        )
    
    with col2:
        total_cofins = df["Valor COFINS"].sum()
        st.metric(
            label="Total COFINS",
            value=format_currency(total_cofins),
        )
    
    with col3:
        total_irrf = df["IRRF Retido"].sum()
        st.metric(
            label="Total IRRF",
            value=format_currency(total_irrf),
        )
    
    with col4:
        total_csll = df["CSLL Retido"].sum()
        st.metric(
            label="Total CSLL",
            value=format_currency(total_csll),
        )
    
    with col5:
        total_issqn = df["Valor ISS"].sum()
        st.metric(
            label="Total ISSQN",
            value=format_currency(total_issqn),
        )
    
    # Distribuição por status
    st.markdown("#### Distribuição por Status")
    status_counts = df["Status"].value_counts()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ativas = status_counts.get("Ativa", 0)
        st.metric(label="Ativas", value=f"{ativas:,}".replace(",", "."))
    
    with col2:
        canceladas = status_counts.get("Cancelada", 0)
        st.metric(label="Canceladas", value=f"{canceladas:,}".replace(",", "."))
    
    with col3:
        substituidas = status_counts.get("Substituída", 0)
        st.metric(label="Substituídas", value=f"{substituidas:,}".replace(",", "."))


def aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica filtros interativos ao DataFrame.
    
    Args:
        df: DataFrame original
    
    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro por status
        status_options = ["Todos"] + sorted(df["Status"].unique().tolist())
        status_selecionado = st.selectbox(
            "Filtrar por Status",
            options=status_options,
            index=0,
        )
    
    with col2:
        # Filtro por tomador
        tomadores = ["Todos"] + sorted(df["Nome Tomador"].unique().tolist())
        tomador_selecionado = st.selectbox(
            "Filtrar por Tomador",
            options=tomadores,
            index=0,
        )
    
    with col3:
        # Filtro por município
        municipios = ["Todos"] + sorted(df["Município"].unique().tolist())
        municipio_selecionado = st.selectbox(
            "Filtrar por Município",
            options=municipios,
            index=0,
        )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if status_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == status_selecionado]
    
    if tomador_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Nome Tomador"] == tomador_selecionado]
    
    if municipio_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Município"] == municipio_selecionado]
    
    return df_filtrado


def render_tabela_notas(df: pd.DataFrame):
    """
    Renderiza tabela interativa com notas fiscais.
    
    Args:
        df: DataFrame com notas fiscais
    """
    # Selecionar colunas para exibição (ordem solicitada)
    colunas_exibir = [
        # Identificação
        "Chave de Acesso",
        "Número NFSe",
        "Status",
        "Data Emissão",
        
        # Prestador
        "Nome Prestador",
        "CNPJ/CPF Prestador",
        
        # Tomador
        "Nome Tomador",
        "CNPJ/CPF Tomador",
        
        # Serviço
        "Código NBS",
        "Descrição NBS",
        "Código Tributação Nacional",
        "Descrição Tributação Nacional",
        
        # Valor
        "Valor Bruto",
        
        # Tributos NÃO Retidos
        "CST PIS",
        "Alíquota PIS",
        "Valor PIS",
        "CST COFINS",
        "Alíquota COFINS",
        "Valor COFINS",
        
        # Tributos Retidos
        "ISS Retido",
        "BC ISS",
        "Alíquota ISS",
        "Valor ISS",
        "IRRF Retido",
        "CSLL Retido",
        "PIS Retido",
        "COFINS Retido",
    ]
    
    df_exibir = df[colunas_exibir].copy()
    
    # Formatar valores monetários
    colunas_monetarias = [
        "Valor Bruto",
        "Valor PIS",
        "Valor COFINS",
        "BC ISS",
        "Valor ISS",
        "IRRF Retido",
        "CSLL Retido",
        "PIS Retido",
        "COFINS Retido",
    ]
    for col in colunas_monetarias:
        if col in df_exibir.columns:
            df_exibir[col] = df_exibir[col].apply(lambda x: format_currency(x))
    
    # Formatar alíquotas (percentuais)
    colunas_percentuais = ["Alíquota PIS", "Alíquota COFINS", "Alíquota ISS"]
    for col in colunas_percentuais:
        if col in df_exibir.columns:
            df_exibir[col] = df_exibir[col].apply(lambda x: f"{x:.2f}%" if x > 0 else "0,00%")
    
    # Exibir tabela
    st.dataframe(
        df_exibir,
        use_container_width=True,
        height=400,
    )
    
    # Adicionar links de autenticidade abaixo da tabela
    st.markdown("")
    st.markdown("**Consultar Autenticidade:**")
    st.markdown(
        "Clique no botão ao lado de cada nota para verificar a autenticidade no Portal Nacional da NFSe. "
        "Será necessário resolver um CAPTCHA no site."
    )
    
    # Criar botões de consulta para cada nota
    for idx, row in df.iterrows():
        chave = row["Chave de Acesso"]
        numero = row["Número NFSe"]
        url = f"https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave={chave}"
        
        col_btn, col_info = st.columns([1, 5])
        with col_btn:
            st.link_button(
                f"NFSe {numero}",
                url,
                help="Abrir Portal Nacional para consulta de autenticidade",
                use_container_width=True,
            )
        with col_info:
            st.caption(f"Prestador: {row['Nome Prestador']} | Tomador: {row['Nome Tomador']} | Valor: {format_currency(row['Valor Bruto'])}")
    
    st.markdown("---")


def render_graficos(df: pd.DataFrame):
    """
    Renderiza gráficos de análise.
    
    Args:
        df: DataFrame com notas fiscais
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Distribuição de Tributos")
        
        # Gráfico de pizza com distribuição de tributos
        total_pis = df["Valor PIS"].sum()
        total_cofins = df["Valor COFINS"].sum()
        total_irrf = df["IRRF Retido"].sum()
        total_csll = df["CSLL Retido"].sum()
        total_issqn = df["Valor ISS"].sum()
        
        df_tributos = pd.DataFrame({
            "Tributo": ["PIS", "COFINS", "IRRF", "CSLL", "ISSQN"],
            "Valor": [total_pis, total_cofins, total_irrf, total_csll, total_issqn],
        })
        
        # Remover tributos com valor zero
        df_tributos = df_tributos[df_tributos["Valor"] > 0]
        
        if len(df_tributos) > 0:
            chart = alt.Chart(df_tributos).mark_arc().encode(
                theta=alt.Theta(field="Valor", type="quantitative"),
                color=alt.Color(field="Tributo", type="nominal", legend=alt.Legend(title="Tributo")),
                tooltip=[
                    alt.Tooltip("Tributo:N", title="Tributo"),
                    alt.Tooltip("Valor:Q", title="Valor", format=",.2f"),
                ],
            ).properties(
                height=300,
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Nenhum tributo para exibir")
    
    with col2:
        st.markdown("#### Top 10 Tomadores por Valor")
        
        # Ranking de tomadores
        df_tomadores = df.groupby("Nome Tomador")["Valor Bruto"].sum().reset_index()
        df_tomadores = df_tomadores.sort_values("Valor Bruto", ascending=False).head(10)
        
        if len(df_tomadores) > 0:
            chart = alt.Chart(df_tomadores).mark_bar().encode(
                x=alt.X("Valor Bruto:Q", title="Valor Bruto (R$)"),
                y=alt.Y("Nome Tomador:N", title="Tomador", sort="-x"),
                tooltip=[
                    alt.Tooltip("Nome Tomador:N", title="Tomador"),
                    alt.Tooltip("Valor Bruto:Q", title="Valor Bruto", format=",.2f"),
                ],
            ).properties(
                height=300,
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Nenhum tomador para exibir")
    
    # Gráficos adicionais: Top 10 Prestadores e Top 10 Tomadores
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### Top 10 Prestadores por Valor")
        
        # Ranking de prestadores
        df_prestadores = df.groupby("Nome Prestador")["Valor Bruto"].sum().reset_index()
        df_prestadores = df_prestadores.sort_values("Valor Bruto", ascending=False).head(10)
        
        if len(df_prestadores) > 0:
            chart = alt.Chart(df_prestadores).mark_bar(color="#1f77b4").encode(
                x=alt.X("Valor Bruto:Q", title="Valor Bruto (R$)"),
                y=alt.Y("Nome Prestador:N", title="Prestador", sort="-x"),
                tooltip=[
                    alt.Tooltip("Nome Prestador:N", title="Prestador"),
                    alt.Tooltip("Valor Bruto:Q", title="Valor Bruto", format=",.2f"),
                ],
            ).properties(
                height=300,
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Nenhum prestador para exibir")
    
    with col4:
        st.markdown("#### Top 10 Tomadores por Valor")
        
        # Ranking de tomadores (mantido do código existente)
        df_tomadores_dup = df.groupby("Nome Tomador")["Valor Bruto"].sum().reset_index()
        df_tomadores_dup = df_tomadores_dup.sort_values("Valor Bruto", ascending=False).head(10)
        
        if len(df_tomadores_dup) > 0:
            chart = alt.Chart(df_tomadores_dup).mark_bar(color="#ff7f0e").encode(
                x=alt.X("Valor Bruto:Q", title="Valor Bruto (R$)"),
                y=alt.Y("Nome Tomador:N", title="Tomador", sort="-x"),
                tooltip=[
                    alt.Tooltip("Nome Tomador:N", title="Tomador"),
                    alt.Tooltip("Valor Bruto:Q", title="Valor Bruto", format=",.2f"),
                ],
            ).properties(
                height=300,
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Nenhum tomador para exibir")
    
    # Gráfico de evolução temporal (se houver dados de múltiplos períodos)
    if "Data Emissão Datetime" in df.columns and df["Data Emissão Datetime"].notna().any():
        st.markdown("---")
        st.markdown("#### Evolução Temporal de Valores")
        
        df_temporal = df.copy()
        df_temporal["Mês/Ano"] = df_temporal["Data Emissão Datetime"].dt.to_period("M").astype(str)
        
        df_evolucao = df_temporal.groupby("Mês/Ano").agg({
            "Valor Bruto": "sum",
            "Valor Líquido": "sum",
        }).reset_index()
        
        if len(df_evolucao) > 1:
            # Converter para formato longo
            df_evolucao_long = df_evolucao.melt(
                id_vars=["Mês/Ano"],
                value_vars=["Valor Bruto", "Valor Líquido"],
                var_name="Tipo",
                value_name="Valor",
            )
            
            chart = alt.Chart(df_evolucao_long).mark_line(point=True).encode(
                x=alt.X("Mês/Ano:N", title="Período"),
                y=alt.Y("Valor:Q", title="Valor (R$)"),
                color=alt.Color("Tipo:N", legend=alt.Legend(title="Tipo de Valor")),
                tooltip=[
                    alt.Tooltip("Mês/Ano:N", title="Período"),
                    alt.Tooltip("Tipo:N", title="Tipo"),
                    alt.Tooltip("Valor:Q", title="Valor", format=",.2f"),
                ],
            ).properties(
                height=300,
            )
            st.altair_chart(chart, use_container_width=True)


def render_relatorio_detalhado(df: pd.DataFrame, notas: List[Dict[str, Any]]):
    """
    Renderiza relatório detalhado de uma nota selecionada.
    
    Args:
        df: DataFrame com notas fiscais
        notas: Lista original de notas
    """
    if len(df) == 0:
        st.info("Nenhuma nota disponível para exibir relatório detalhado.")
        return
    
    # Seletor de nota
    numeros_nfse = df["Número NFSe"].tolist()
    numero_selecionado = st.selectbox(
        "Selecione uma nota para visualizar o relatório completo",
        options=numeros_nfse,
        format_func=lambda x: f"NFSe {x} - {df[df['Número NFSe'] == x]['Nome Tomador'].iloc[0]}",
    )
    
    # Encontrar nota selecionada
    nota_selecionada = None
    for nota in notas:
        if nota["numero_nfse"] == numero_selecionado:
            nota_selecionada = nota
            break
    
    if not nota_selecionada:
        st.error("Nota não encontrada.")
        return
    
    # Exibir relatório
    st.markdown(f"#### Relatório Completo - NFSe {numero_selecionado}")
    
    # Botão de autenticidade
    chave_acesso = nota_selecionada.get('chave_acesso', '')
    if chave_acesso:
        url_autenticidade = f"https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave={chave_acesso}"
        st.link_button(
            "Consultar Autenticidade no Portal Nacional",
            url_autenticidade,
            help="Abrir Portal Nacional para verificar a autenticidade desta NFSe (requer CAPTCHA)",
            type="primary",
            use_container_width=False,
        )
        st.caption(f"Chave de Acesso: {chave_acesso}")
    
    st.markdown("")
    
    # Identificação
    st.markdown("**Identificação**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text(f"Número NFSe: {nota_selecionada['numero_nfse']}")
        st.text(f"Número DFSe: {nota_selecionada['numero_dfse']}")
    with col2:
        st.text(f"Status: {nota_selecionada['status']}")
        st.text(f"Data Emissão: {nota_selecionada['data_emissao']}")
    with col3:
        st.text(f"Data Competência: {nota_selecionada['data_competencia']}")
        st.text(f"Data Processamento: {nota_selecionada['data_processamento']}")
    
    st.markdown("---")
    
    # Emitente
    st.markdown("**Emitente**")
    emit = nota_selecionada["emitente"]
    st.text(f"{emit['razao_social']}")
    st.text(f"CNPJ: {emit['cnpj']} | IM: {emit['inscricao_municipal']}")
    st.text(f"{emit['logradouro']}, {emit['numero']} - {emit['bairro']}")
    st.text(f"{emit['uf']} | CEP: {emit['cep']}")
    if emit['telefone']:
        st.text(f"Telefone: {emit['telefone']}")
    if emit['email']:
        st.text(f"Email: {emit['email']}")
    
    st.markdown("---")
    
    # Tomador
    st.markdown("**Tomador**")
    toma = nota_selecionada["tomador"]
    st.text(f"{toma['razao_social_nome']}")
    st.text(f"{toma['tipo_pessoa']}: {toma['cnpj_cpf']}")
    if toma['logradouro']:
        st.text(f"{toma['logradouro']}, {toma['numero']}")
        if toma['complemento']:
            st.text(f"Complemento: {toma['complemento']}")
        st.text(f"{toma['bairro']} | CEP: {toma['cep']}")
    if toma['email']:
        st.text(f"Email: {toma['email']}")
    
    st.markdown("---")
    
    # Serviço
    st.markdown("**Serviço Prestado**")
    serv = nota_selecionada["servico"]
    st.text(f"Código NBS: {serv['codigo_nbs']}")
    st.text(f"Descrição NBS: {serv['descricao_nbs']}")
    st.text(f"Código Tributação Nacional: {serv['codigo_tributacao_nacional']}")
    st.text(f"Descrição: {serv['descricao_tributacao_nacional']}")
    
    with st.expander("Ver Descrição Completa do Serviço"):
        st.text(serv['descricao_servico'])
    
    st.markdown("---")
    
    # Valores
    st.markdown("**Valores**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Valor Bruto", format_currency(nota_selecionada['valor_bruto']))
    with col2:
        st.metric("Total Retido", format_currency(nota_selecionada['valor_total_retido']))
    with col3:
        st.metric("Valor Líquido", format_currency(nota_selecionada['valor_liquido']))
    
    st.markdown("---")
    
    # Tributos
    st.markdown("**Tributos Detalhados**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**PIS**")
        st.text(f"CST: {nota_selecionada['pis']['cst']}")
        st.text(f"Base de Cálculo: {format_currency(nota_selecionada['pis']['base_calculo'])}")
        st.text(f"Alíquota: {format_percentage(nota_selecionada['pis']['aliquota'])}")
        st.text(f"Valor: {format_currency(nota_selecionada['pis']['valor'])}")
        st.text(f"Retido: {'Sim' if nota_selecionada['pis']['retido'] else 'Não'}")
        
        st.markdown("**IRRF**")
        st.text(f"Valor: {format_currency(nota_selecionada['irrf']['valor'])}")
        
        st.markdown("**ISSQN**")
        if nota_selecionada['issqn']['aliquota'] > 0:
            st.text(f"Alíquota: {format_percentage(nota_selecionada['issqn']['aliquota'])}")
            st.text(f"Valor: {format_currency(nota_selecionada['issqn']['valor'])}")
        st.text(f"Retido: {'Sim' if nota_selecionada['issqn']['retido'] else 'Não'}")
    
    with col2:
        st.markdown("**COFINS**")
        st.text(f"CST: {nota_selecionada['cofins']['cst']}")
        st.text(f"Base de Cálculo: {format_currency(nota_selecionada['cofins']['base_calculo'])}")
        st.text(f"Alíquota: {format_percentage(nota_selecionada['cofins']['aliquota'])}")
        st.text(f"Valor: {format_currency(nota_selecionada['cofins']['valor'])}")
        st.text(f"Retido: {'Sim' if nota_selecionada['cofins']['retido'] else 'Não'}")
        
        st.markdown("**CSLL**")
        st.text(f"Valor: {format_currency(nota_selecionada['csll']['valor'])}")
    
    st.markdown("---")
    
    # Regime Tributário
    st.markdown("**Regime Tributário**")
    regime = nota_selecionada["regime"]
    st.text(f"Optante Simples Nacional: {'Sim' if regime['optante_simples_nacional'] else 'Não'}")
    if regime['regime_especial_tributacao']:
        st.text(f"Regime Especial: {regime['regime_especial_tributacao']}")


def render_exportacao(df: pd.DataFrame, notas: List[Dict[str, Any]]):
    """
    Renderiza opções de exportação de dados.
    
    Args:
        df: DataFrame com notas fiscais
        notas: Lista original de notas
    """
    st.markdown("Exporte os dados processados para análise em planilhas ou outros sistemas.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Exportar tabela resumida
        csv_resumido = df.to_csv(index=False, encoding="utf-8-sig", sep=";", decimal=",")
        st.download_button(
            label="Baixar Tabela Resumida (CSV)",
            data=csv_resumido,
            file_name=f"nfse_resumo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    
    with col2:
        # Exportar dados completos
        df_completo = criar_dataframe_completo(notas)
        csv_completo = df_completo.to_csv(index=False, encoding="utf-8-sig", sep=";", decimal=",")
        st.download_button(
            label="Baixar Dados Completos (CSV)",
            data=csv_completo,
            file_name=f"nfse_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


def criar_dataframe_completo(notas: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Cria DataFrame com todos os campos das notas.
    
    Args:
        notas: Lista de notas
    
    Returns:
        pd.DataFrame: DataFrame completo
    """
    rows = []
    
    for nota in notas:
        row = {
            # Identificação
            "Chave de Acesso": nota["chave_acesso"],
            "Número NFSe": nota["numero_nfse"],
            "Número DFSe": nota["numero_dfse"],
            "Status": nota["status"],
            "Código Status": nota["codigo_status"],
            "Data Emissão": nota["data_emissao"],
            "Data Processamento": nota["data_processamento"],
            "Data Competência": nota["data_competencia"],
            
            # Emitente
            "Emitente Razão Social": nota["emitente"]["razao_social"],
            "Emitente CNPJ": nota["emitente"]["cnpj"],
            "Emitente IM": nota["emitente"]["inscricao_municipal"],
            "Emitente Logradouro": nota["emitente"]["logradouro"],
            "Emitente Número": nota["emitente"]["numero"],
            "Emitente Bairro": nota["emitente"]["bairro"],
            "Emitente UF": nota["emitente"]["uf"],
            "Emitente CEP": nota["emitente"]["cep"],
            "Emitente Telefone": nota["emitente"]["telefone"],
            "Emitente Email": nota["emitente"]["email"],
            
            # Tomador
            "Tomador Nome": nota["tomador"]["razao_social_nome"],
            "Tomador Tipo Pessoa": nota["tomador"]["tipo_pessoa"],
            "Tomador CNPJ/CPF": nota["tomador"]["cnpj_cpf"],
            "Tomador Logradouro": nota["tomador"]["logradouro"],
            "Tomador Número": nota["tomador"]["numero"],
            "Tomador Complemento": nota["tomador"]["complemento"],
            "Tomador Bairro": nota["tomador"]["bairro"],
            "Tomador CEP": nota["tomador"]["cep"],
            "Tomador Email": nota["tomador"]["email"],
            
            # Serviço
            "Código NBS": nota["servico"]["codigo_nbs"],
            "Descrição NBS": nota["servico"]["descricao_nbs"],
            "Código Tributação Nacional": nota["servico"]["codigo_tributacao_nacional"],
            "Descrição Tributação Nacional": nota["servico"]["descricao_tributacao_nacional"],
            "Descrição Serviço": nota["servico"]["descricao_servico"],
            
            # Valores
            "Valor Bruto": nota["valor_bruto"],
            "Valor Líquido": nota["valor_liquido"],
            "Total Retido": nota["valor_total_retido"],
            
            # Tributos
            "PIS CST": nota["pis"]["cst"],
            "PIS Base Cálculo": nota["pis"]["base_calculo"],
            "PIS Alíquota": nota["pis"]["aliquota"],
            "PIS Valor": nota["pis"]["valor"],
            "PIS Retido": "Sim" if nota["pis"]["retido"] else "Não",
            
            "COFINS CST": nota["cofins"]["cst"],
            "COFINS Base Cálculo": nota["cofins"]["base_calculo"],
            "COFINS Alíquota": nota["cofins"]["aliquota"],
            "COFINS Valor": nota["cofins"]["valor"],
            "COFINS Retido": "Sim" if nota["cofins"]["retido"] else "Não",
            
            "IRRF Valor": nota["irrf"]["valor"],
            "CSLL Valor": nota["csll"]["valor"],
            
            "ISSQN Alíquota": nota["issqn"]["aliquota"],
            "ISSQN Valor": nota["issqn"]["valor"],
            "ISSQN Retido": "Sim" if nota["issqn"]["retido"] else "Não",
            
            # Localização
            "Local Emissão": nota["localizacao"]["local_emissao"],
            "Local Prestação": nota["localizacao"]["local_prestacao"],
            "Município Incidência": nota["localizacao"]["municipio_incidencia"],
            
            # Regime
            "Simples Nacional": "Sim" if nota["regime"]["optante_simples_nacional"] else "Não",
            "Regime Especial": nota["regime"]["regime_especial_tributacao"],
            
            # Metadados
            "Arquivo Original": nota["arquivo_original"],
        }
        rows.append(row)
    
    return pd.DataFrame(rows)
