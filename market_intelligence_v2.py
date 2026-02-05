"""
Módulo de Inteligência de Mercado - Dashboard Expandido
========================================================

Dashboard completo com filtros avançados e análises tributárias detalhadas.
Inclui PIS, COFINS, ICMS, IPI, CSTs e análises por cClassTrib.

Autor: PRICETAX Intelligence System
Data: 2026-01-29
Versão: 2.0
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os


def render_market_intelligence_dashboard():
    """
    Renderiza dashboard expandido de Inteligência de Mercado com filtros e análises completas.
    """
    
    st.markdown("### Inteligência de Mercado - Dashboard Completo")
    
    # Verificar se há dados
    data_file = "logs/xml_nfe_data.csv"
    
    if not os.path.isfile(data_file):
        st.info("Nenhum dado capturado ainda. Faça upload de XMLs na aba 'Análise XML' para começar a coletar dados.")
        return
    
    # Carregar dados
    try:
        # Tentar migração automática se houver erro de campos
        try:
            df = pd.read_csv(data_file)
        except pd.errors.ParserError as e:
            if "Expected" in str(e) and "fields" in str(e):
                st.warning("Detectado formato antigo de dados. Migrando automaticamente...")
                
                # Executar migração
                import subprocess
                result = subprocess.run(
                    ['python3.11', 'migrate_csv.py'],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                
                if result.returncode == 0:
                    st.success("Migração concluída! Recarregando dados...")
                    df = pd.read_csv(data_file)
                else:
                    raise Exception(f"Erro na migração: {result.stderr}")
            else:
                raise
        
        if len(df) == 0:
            st.info("Nenhum registro encontrado no banco de dados.")
            return
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return
        # ===== FILTROS =====
    st.markdown("### Filtros")
    
    # Primeira linha de filtros (chave de acesso - campo largo)
    filtro_chave = st.text_input(
        "Chave de Acesso NFe (44 dígitos)",
        placeholder="Digite a chave completa ou parcial",
        key="filtro_chave",
        help="Busca parcial: digite qualquer parte da chave"
    )
    
    # Segunda linha de filtros
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
    with col1:
        # Filtro por Emitente
        emitentes = ['Todos'] + sorted(df['emitente_razao'].dropna().unique().tolist())
        filtro_emitente = st.selectbox("Emitente", emitentes, key="filtro_emitente")
    
    with col2:
        # Filtro por Destinatário
        destinatarios = ['Todos'] + sorted(df['destinatario_razao'].dropna().unique().tolist())
        filtro_destinatario = st.selectbox("Destinatário", destinatarios, key="filtro_destinatario")
    
    with col3:
        # Filtro por NCM
        ncms = ['Todos'] + sorted(df['ncm'].dropna().unique().tolist())
        filtro_ncm = st.selectbox("NCM", ncms, key="filtro_ncm")
    
    with col4:
        # Filtro por CFOP
        cfops = ['Todos'] + sorted(df['cfop'].dropna().unique().tolist())
        filtro_cfop = st.selectbox("CFOP", cfops, key="filtro_cfop")
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        # Filtro por UF Origem
        ufs_origem = ['Todos'] + sorted(df['emitente_uf'].dropna().unique().tolist())
        filtro_uf_origem = st.selectbox("UF Origem", ufs_origem, key="filtro_uf_origem")
    
    with col6:
        # Filtro por UF Destino
        ufs_destino = ['Todos'] + sorted(df['destinatario_uf'].dropna().unique().tolist())
        filtro_uf_destino = st.selectbox("UF Destino", ufs_destino, key="filtro_uf_destino")
    
    with col7:
        # Filtro por cClassTrib
        cclasstrib_list = ['Todos'] + sorted(df['cclasstrib'].dropna().unique().tolist())
        filtro_cclasstrib = st.selectbox("cClassTrib", cclasstrib_list, key="filtro_cclasstrib")
    
    with col8:
        # Filtro por Tipo de Operação
        filtro_tipo_op = st.selectbox("Tipo Operação", ['Todos', 'ENTRADA', 'SAIDA'], key="filtro_tipo_op")
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    # Filtro de chave de acesso (busca parcial)
    if filtro_chave:
        df_filtrado = df_filtrado[df_filtrado['chave_acesso'].str.contains(filtro_chave, case=False, na=False)]
    
    if filtro_emitente != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['emitente_razao'] == filtro_emitente]
    
    if filtro_destinatario != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['destinatario_razao'] == filtro_destinatario]
    
    if filtro_ncm != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['ncm'] == filtro_ncm]
    
    if filtro_cfop != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['cfop'] == filtro_cfop]
    
    if filtro_uf_origem != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['emitente_uf'] == filtro_uf_origem]
    
    if filtro_uf_destino != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['destinatario_uf'] == filtro_uf_destino]
    
    if filtro_cclasstrib != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['cclasstrib'] == filtro_cclasstrib]
    
    if filtro_tipo_op != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['tipo_operacao'] == filtro_tipo_op]
    
    if len(df_filtrado) == 0:
        st.warning("Nenhum registro encontrado com os filtros aplicados.")
        return
    
    st.markdown(f"**Registros filtrados:** {len(df_filtrado)} de {len(df)}")
    
    # ===== MÉTRICAS PRINCIPAIS =====
    st.markdown("---")
    st.markdown("#### Métricas Principais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total de Registros", f"{len(df_filtrado):,}")
    
    with col2:
        valor_total = df_filtrado['valor_total'].sum()
        st.metric("Valor Total", f"R$ {valor_total:,.2f}")
    
    with col3:
        ncms_unicos = df_filtrado['ncm'].nunique()
        st.metric("NCMs Únicos", f"{ncms_unicos}")
    
    with col4:
        cfops_unicos = df_filtrado['cfop'].nunique()
        st.metric("CFOPs Únicos", f"{cfops_unicos}")
    
    with col5:
        cclasstrib_unicos = df_filtrado['cclasstrib'].nunique()
        st.metric("cClassTribs Únicos", f"{cclasstrib_unicos}")
    
    # ===== MÉTRICAS TRIBUTÁRIAS =====
    st.markdown("---")
    st.markdown("#### Métricas Tributárias")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_icms = df_filtrado['vicms'].sum()
        st.metric("Total ICMS", f"R$ {total_icms:,.2f}")
    
    with col2:
        total_pis = df_filtrado['vpis'].sum()
        st.metric("Total PIS", f"R$ {total_pis:,.2f}")
    
    with col3:
        total_cofins = df_filtrado['vcofins'].sum()
        st.metric("Total COFINS", f"R$ {total_cofins:,.2f}")
    
    with col4:
        total_ipi = df_filtrado['vipi'].sum()
        st.metric("Total IPI", f"R$ {total_ipi:,.2f}")
    
    with col5:
        total_ibs_cbs = df_filtrado['vibs'].sum() + df_filtrado['vcbs'].sum()
        st.metric("Total IBS+CBS", f"R$ {total_ibs_cbs:,.2f}")
    
    # ===== ABAS DE ANÁLISE =====
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Produtos (NCM)",
        "Operações (CFOP)",
        "Tributação (cClassTrib)",
        "CSTs e Impostos",
        "Dados Completos"
    ])
    
    # ===== TAB 1: PRODUTOS (NCM) =====
    with tab1:
        st.markdown("### Análise por NCM")
        
        # Top 20 NCMs por Valor Total
        top_ncms = df_filtrado.groupby('ncm').agg({
            'valor_total': 'sum',
            'quantidade': 'sum',
            'valor_unitario': 'mean'
        }).sort_values('valor_total', ascending=False).head(20)
        
        top_ncms = top_ncms.reset_index()
        top_ncms.columns = ['NCM', 'Valor Total', 'Quantidade', 'Valor Médio']
        
        # Gráfico de barras
        fig_ncm = px.bar(
            top_ncms,
            x='NCM',
            y='Valor Total',
            title='Top 20 NCMs por Valor Total',
            labels={'Valor Total': 'Valor Total (R$)'},
            color='Valor Total',
            color_continuous_scale='Viridis'
        )
        fig_ncm.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_ncm, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("#### Tabela Detalhada")
        st.dataframe(
            top_ncms.style.format({
                'Valor Total': 'R$ {:,.2f}',
                'Quantidade': '{:,.2f}',
                'Valor Médio': 'R$ {:,.2f}'
            }),
            use_container_width=True
        )
    
    # ===== TAB 2: OPERAÇÕES (CFOP) =====
    with tab2:
        st.markdown("### Análise por CFOP")
        
        # Análise por CFOP
        cfop_analysis = df_filtrado.groupby('cfop').agg({
            'valor_total': 'sum',
            'vicms': 'sum',
            'vpis': 'sum',
            'vcofins': 'sum',
            'vipi': 'sum',
            'vibs': 'sum',
            'vcbs': 'sum'
        }).sort_values('valor_total', ascending=False)
        
        cfop_analysis = cfop_analysis.reset_index()
        cfop_analysis.columns = ['CFOP', 'Valor Total', 'ICMS', 'PIS', 'COFINS', 'IPI', 'IBS', 'CBS']
        
        # Gráfico de barras empilhadas
        fig_cfop = go.Figure()
        
        fig_cfop.add_trace(go.Bar(
            x=cfop_analysis['CFOP'],
            y=cfop_analysis['ICMS'],
            name='ICMS',
            marker_color='#3B82F6'
        ))
        
        fig_cfop.add_trace(go.Bar(
            x=cfop_analysis['CFOP'],
            y=cfop_analysis['PIS'],
            name='PIS',
            marker_color='#10B981'
        ))
        
        fig_cfop.add_trace(go.Bar(
            x=cfop_analysis['CFOP'],
            y=cfop_analysis['COFINS'],
            name='COFINS',
            marker_color='#F59E0B'
        ))
        
        fig_cfop.add_trace(go.Bar(
            x=cfop_analysis['CFOP'],
            y=cfop_analysis['IPI'],
            name='IPI',
            marker_color='#EF4444'
        ))
        
        fig_cfop.add_trace(go.Bar(
            x=cfop_analysis['CFOP'],
            y=cfop_analysis['IBS'],
            name='IBS',
            marker_color='#8B5CF6'
        ))
        
        fig_cfop.add_trace(go.Bar(
            x=cfop_analysis['CFOP'],
            y=cfop_analysis['CBS'],
            name='CBS',
            marker_color='#EC4899'
        ))
        
        fig_cfop.update_layout(
            title='Impostos por CFOP',
            xaxis_title='CFOP',
            yaxis_title='Valor (R$)',
            barmode='stack',
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig_cfop, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("#### Tabela Detalhada")
        st.dataframe(
            cfop_analysis.style.format({
                'Valor Total': 'R$ {:,.2f}',
                'ICMS': 'R$ {:,.2f}',
                'PIS': 'R$ {:,.2f}',
                'COFINS': 'R$ {:,.2f}',
                'IPI': 'R$ {:,.2f}',
                'IBS': 'R$ {:,.2f}',
                'CBS': 'R$ {:,.2f}'
            }),
            use_container_width=True
        )
    
    # ===== TAB 3: TRIBUTAÇÃO (cClassTrib) =====
    with tab3:
        st.markdown("### Análise por cClassTrib")
        
        # Análise por cClassTrib
        cclasstrib_analysis = df_filtrado.groupby('cclasstrib').agg({
            'valor_total': 'sum',
            'vibs': 'sum',
            'vcbs': 'sum',
            'ncm': 'count'
        }).sort_values('valor_total', ascending=False)
        
        cclasstrib_analysis = cclasstrib_analysis.reset_index()
        cclasstrib_analysis.columns = ['cClassTrib', 'Valor Total', 'IBS', 'CBS', 'Quantidade']
        
        # Gráfico de pizza
        fig_cclasstrib_pie = px.pie(
            cclasstrib_analysis,
            values='Valor Total',
            names='cClassTrib',
            title='Distribuição de Valor por cClassTrib'
        )
        st.plotly_chart(fig_cclasstrib_pie, use_container_width=True)
        
        # Gráfico de barras IBS vs CBS
        fig_cclasstrib_bar = go.Figure()
        
        fig_cclasstrib_bar.add_trace(go.Bar(
            x=cclasstrib_analysis['cClassTrib'],
            y=cclasstrib_analysis['IBS'],
            name='IBS',
            marker_color='#8B5CF6'
        ))
        
        fig_cclasstrib_bar.add_trace(go.Bar(
            x=cclasstrib_analysis['cClassTrib'],
            y=cclasstrib_analysis['CBS'],
            name='CBS',
            marker_color='#EC4899'
        ))
        
        fig_cclasstrib_bar.update_layout(
            title='IBS vs CBS por cClassTrib',
            xaxis_title='cClassTrib',
            yaxis_title='Valor (R$)',
            barmode='group'
        )
        
        st.plotly_chart(fig_cclasstrib_bar, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("#### Tabela Detalhada")
        st.dataframe(
            cclasstrib_analysis.style.format({
                'Valor Total': 'R$ {:,.2f}',
                'IBS': 'R$ {:,.2f}',
                'CBS': 'R$ {:,.2f}',
                'Quantidade': '{:,}'
            }),
            use_container_width=True
        )
    
    # ===== TAB 4: CSTs E IMPOSTOS =====
    with tab4:
        st.markdown("### Análise de CSTs e Impostos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição CST ICMS
            st.markdown("#### CST ICMS")
            cst_icms_dist = df_filtrado['cst_icms'].value_counts().head(10)
            fig_cst_icms = px.pie(
                values=cst_icms_dist.values,
                names=cst_icms_dist.index,
                title='Top 10 CST ICMS'
            )
            st.plotly_chart(fig_cst_icms, use_container_width=True)
            
            # Distribuição CST PIS
            st.markdown("#### CST PIS")
            cst_pis_dist = df_filtrado['cst_pis'].value_counts().head(10)
            fig_cst_pis = px.pie(
                values=cst_pis_dist.values,
                names=cst_pis_dist.index,
                title='Top 10 CST PIS'
            )
            st.plotly_chart(fig_cst_pis, use_container_width=True)
        
        with col2:
            # Distribuição CST COFINS
            st.markdown("#### CST COFINS")
            cst_cofins_dist = df_filtrado['cst_cofins'].value_counts().head(10)
            fig_cst_cofins = px.pie(
                values=cst_cofins_dist.values,
                names=cst_cofins_dist.index,
                title='Top 10 CST COFINS'
            )
            st.plotly_chart(fig_cst_cofins, use_container_width=True)
            
            # Distribuição CST IPI
            st.markdown("#### CST IPI")
            cst_ipi_dist = df_filtrado['cst_ipi'].value_counts().head(10)
            if len(cst_ipi_dist) > 0:
                fig_cst_ipi = px.pie(
                    values=cst_ipi_dist.values,
                    names=cst_ipi_dist.index,
                    title='Top 10 CST IPI'
                )
                st.plotly_chart(fig_cst_ipi, use_container_width=True)
            else:
                st.info("Nenhum registro com IPI encontrado.")
        
        # Comparativo de alíquotas médias
        st.markdown("---")
        st.markdown("#### Alíquotas Médias por Imposto")
        
        # Calcular alíquotas médias (quando base > 0)
        aliquotas_medias = {}
        
        # ICMS
        df_icms = df_filtrado[df_filtrado['vbc_icms'] > 0]
        if len(df_icms) > 0:
            aliquotas_medias['ICMS'] = (df_icms['vicms'] / df_icms['vbc_icms'] * 100).mean()
        
        # PIS
        df_pis = df_filtrado[df_filtrado['vbc_pis'] > 0]
        if len(df_pis) > 0:
            aliquotas_medias['PIS'] = (df_pis['vpis'] / df_pis['vbc_pis'] * 100).mean()
        
        # COFINS
        df_cofins = df_filtrado[df_filtrado['vbc_cofins'] > 0]
        if len(df_cofins) > 0:
            aliquotas_medias['COFINS'] = (df_cofins['vcofins'] / df_cofins['vbc_cofins'] * 100).mean()
        
        # IPI
        df_ipi = df_filtrado[df_filtrado['vbc_ipi'] > 0]
        if len(df_ipi) > 0:
            aliquotas_medias['IPI'] = df_ipi['pipi'].mean()
        
        # IBS
        df_ibs = df_filtrado[df_filtrado['vibs'] > 0]
        if len(df_ibs) > 0:
            aliquotas_medias['IBS'] = df_ibs['pibs'].mean()
        
        # CBS
        df_cbs = df_filtrado[df_filtrado['vcbs'] > 0]
        if len(df_cbs) > 0:
            aliquotas_medias['CBS'] = df_cbs['pcbs'].mean()
        
        if aliquotas_medias:
            fig_aliq = px.bar(
                x=list(aliquotas_medias.keys()),
                y=list(aliquotas_medias.values()),
                title='Alíquotas Médias por Imposto (%)',
                labels={'x': 'Imposto', 'y': 'Alíquota Média (%)'},
                color=list(aliquotas_medias.values()),
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig_aliq, use_container_width=True)
    
    # ===== TAB 5: DADOS COMPLETOS =====
    with tab5:
        st.markdown("### Dados Completos")
        
        # Seleção de colunas para exibição
        colunas_disponiveis = df_filtrado.columns.tolist()
        # Definir colunas padrão mais completas
        colunas_default = [
            'timestamp_captura',
            'usuario',
            'chave_acesso',
            'data_emissao',
            'tipo_operacao',
            'emitente_cnpj',
            'emitente_razao',
            'emitente_uf',
            'destinatario_cnpj',
            'destinatario_razao',
            'destinatario_uf',
            'ncm',
            'cfop',
            'descricao_produto',
            'valor_unitario',
            'quantidade',
            'valor_total',
            'cst_icms',
            'vicms',
            'cst_pis',
            'vpis',
            'cst_cofins',
            'vcofins',
            'cst_ipi',
            'vipi',
            'cst_ibscbs',
            'cclasstrib',
            'vibs',
            'vcbs'
        ]
        
        # Filtrar apenas colunas que existem no DataFrame
        colunas_default_existentes = [col for col in colunas_default if col in colunas_disponiveis]
        
        colunas_selecionadas = st.multiselect(
            "Selecione as colunas para exibir",
            colunas_disponiveis,
            default=colunas_default_existentes
        )
        
        if colunas_selecionadas:
            st.dataframe(df_filtrado[colunas_selecionadas], use_container_width=True)
        else:
            st.info("Selecione ao menos uma coluna para exibir.")
        
        # Exportação
        st.markdown("---")
        st.markdown("#### Exportar Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Exportar CSV
            csv_data = df_filtrado.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="Baixar Dados Filtrados (CSV)",
                data=csv_data,
                file_name=f"inteligencia_mercado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Exportar Excel
            try:
                from io import BytesIO
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, sheet_name='Dados', index=False)
                buffer.seek(0)
                
                st.download_button(
                    label="Baixar Dados Filtrados (Excel)",
                    data=buffer,
                    file_name=f"inteligencia_mercado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Erro ao gerar Excel: {e}")
