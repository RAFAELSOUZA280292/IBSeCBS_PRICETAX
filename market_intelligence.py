"""
Módulo de Inteligência de Mercado - Dashboard Administrativo
=============================================================

Análise e visualização de dados capturados de XMLs (NFe/NFSe).
Acesso exclusivo para usuário Admin.

Autor: PRICETAX Intelligence System
Data: 2026-01-28
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os


def render_market_intelligence_tab():
    """
    Renderiza aba de Inteligência de Mercado no painel Admin.
    Exibe análises, dashboards e insights dos dados capturados.
    """
    
    # Verificar se usuário é Admin
    authenticated_user = st.session_state.get("authenticated_user", "")
    if authenticated_user != "PriceADM":
        st.error("Acesso Negado")
        st.warning("Esta área é restrita ao administrador do sistema.")
        return
    
    st.markdown("## Inteligência de Mercado")
    st.markdown("Análise de dados capturados automaticamente de XMLs processados na plataforma.")
    
    # Verificar se existem dados
    nfe_file = "logs/xml_nfe_data.csv"
    nfse_file = "logs/xml_nfse_data.csv"
    
    has_nfe = os.path.isfile(nfe_file)
    has_nfse = os.path.isfile(nfse_file)
    
    if not has_nfe and not has_nfse:
        st.info("Nenhum dado capturado ainda. Os dados serão coletados automaticamente quando usuários fizerem upload de XMLs.")
        return
    
    # Tabs para diferentes análises
    tab_nfe, tab_nfse, tab_export = st.tabs([
        "Produtos (NFe)",
        "Serviços (NFSe)",
        "Exportação"
    ])
    
    # =========================================================================
    # TAB: PRODUTOS (NFe)
    # =========================================================================
    with tab_nfe:
        if not has_nfe:
            st.info("Nenhum dado de NFe capturado ainda.")
        else:
            render_nfe_analysis(nfe_file)
    
    # =========================================================================
    # TAB: SERVIÇOS (NFSe)
    # =========================================================================
    with tab_nfse:
        if not has_nfse:
            st.info("Nenhum dado de NFSe capturado ainda.")
        else:
            render_nfse_analysis(nfse_file)
    
    # =========================================================================
    # TAB: EXPORTAÇÃO
    # =========================================================================
    with tab_export:
        render_export_section(nfe_file if has_nfe else None, nfse_file if has_nfse else None)


def render_nfe_analysis(nfe_file: str):
    """Renderiza análise de dados de NFe (Produtos)."""
    
    try:
        df = pd.read_csv(nfe_file)
        
        if len(df) == 0:
            st.info("Nenhum registro encontrado.")
            return
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Registros", f"{len(df):,}")
        
        with col2:
            total_valor = df['valor_total'].sum()
            st.metric("Valor Total", f"R$ {total_valor:,.2f}")
        
        with col3:
            ncms_unicos = df['ncm'].nunique()
            st.metric("NCMs Únicos", f"{ncms_unicos:,}")
        
        with col4:
            cfops_unicos = df['cfop'].nunique()
            st.metric("CFOPs Únicos", f"{cfops_unicos:,}")
        
        st.markdown("---")
        
        # Filtros
        st.markdown("### Filtros")
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            tipo_op = st.multiselect(
                "Tipo de Operação",
                options=df['tipo_operacao'].unique().tolist(),
                default=df['tipo_operacao'].unique().tolist()
            )
        
        with col_f2:
            ufs_origem = st.multiselect(
                "UF Origem",
                options=sorted(df['uf_emitente'].unique().tolist()),
                default=[]
            )
        
        with col_f3:
            ufs_destino = st.multiselect(
                "UF Destino",
                options=sorted(df['uf_destinatario'].unique().tolist()),
                default=[]
            )
        
        # Aplicar filtros
        df_filtered = df[df['tipo_operacao'].isin(tipo_op)]
        if ufs_origem:
            df_filtered = df_filtered[df_filtered['uf_emitente'].isin(ufs_origem)]
        if ufs_destino:
            df_filtered = df_filtered[df_filtered['uf_destinatario'].isin(ufs_destino)]
        
        st.markdown(f"**Registros após filtros:** {len(df_filtered):,}")
        
        st.markdown("---")
        
        # Análises
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            st.markdown("### Top 20 NCMs por Valor Total")
            ncm_agg = df_filtered.groupby('ncm').agg({
                'valor_total': 'sum',
                'quantidade': 'sum'
            }).reset_index().sort_values('valor_total', ascending=False).head(20)
            
            fig_ncm = px.bar(
                ncm_agg,
                x='ncm',
                y='valor_total',
                title="Valor Total por NCM",
                labels={'valor_total': 'Valor Total (R$)', 'ncm': 'NCM'}
            )
            st.plotly_chart(fig_ncm, use_container_width=True)
        
        with col_a2:
            st.markdown("### Top 20 CFOPs por Quantidade")
            cfop_agg = df_filtered.groupby('cfop').size().reset_index(name='count').sort_values('count', ascending=False).head(20)
            
            fig_cfop = px.bar(
                cfop_agg,
                x='cfop',
                y='count',
                title="Quantidade de Registros por CFOP",
                labels={'count': 'Quantidade', 'cfop': 'CFOP'}
            )
            st.plotly_chart(fig_cfop, use_container_width=True)
        
        # Mapa UF Origem x Destino
        st.markdown("### Fluxo Geográfico (UF Origem → Destino)")
        uf_flow = df_filtered.groupby(['uf_emitente', 'uf_destinatario']).agg({
            'valor_total': 'sum'
        }).reset_index().sort_values('valor_total', ascending=False).head(30)
        
        st.dataframe(
            uf_flow.rename(columns={
                'uf_emitente': 'UF Origem',
                'uf_destinatario': 'UF Destino',
                'valor_total': 'Valor Total (R$)'
            }),
            use_container_width=True
        )
        
        # Análise de cClassTrib
        st.markdown("### Distribuição de cClassTrib")
        cclasstrib_agg = df_filtered[df_filtered['cclasstrib'] != ''].groupby('cclasstrib').size().reset_index(name='count').sort_values('count', ascending=False).head(15)
        
        if len(cclasstrib_agg) > 0:
            fig_class = px.pie(
                cclasstrib_agg,
                names='cclasstrib',
                values='count',
                title="Distribuição de cClassTrib"
            )
            st.plotly_chart(fig_class, use_container_width=True)
        else:
            st.info("Nenhum cClassTrib encontrado nos dados filtrados.")
        
        # Tabela detalhada
        st.markdown("### Dados Detalhados (Top 100 por Valor)")
        df_display = df_filtered.sort_values('valor_total', ascending=False).head(100)[[
            'timestamp_captura', 'usuario', 'tipo_operacao', 'ncm', 'cfop',
            'descricao_produto', 'valor_unitario', 'quantidade', 'valor_total',
            'uf_emitente', 'uf_destinatario', 'cclasstrib'
        ]]
        
        st.dataframe(df_display, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao processar dados de NFe: {e}")


def render_nfse_analysis(nfse_file: str):
    """Renderiza análise de dados de NFSe (Serviços)."""
    
    try:
        df = pd.read_csv(nfse_file)
        
        if len(df) == 0:
            st.info("Nenhum registro encontrado.")
            return
        
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Registros", f"{len(df):,}")
        
        with col2:
            total_valor = df['valor_servico'].sum()
            st.metric("Valor Total", f"R$ {total_valor:,.2f}")
        
        with col3:
            nbs_unicos = df['nbs'].nunique()
            st.metric("NBS Únicos", f"{nbs_unicos:,}")
        
        st.markdown("---")
        
        # Top 20 NBS
        st.markdown("### Top 20 Serviços (NBS) por Valor")
        nbs_agg = df.groupby('nbs').agg({
            'valor_servico': 'sum'
        }).reset_index().sort_values('valor_servico', ascending=False).head(20)
        
        fig_nbs = px.bar(
            nbs_agg,
            x='nbs',
            y='valor_servico',
            title="Valor Total por NBS",
            labels={'valor_servico': 'Valor Total (R$)', 'nbs': 'NBS'}
        )
        st.plotly_chart(fig_nbs, use_container_width=True)
        
        # Distribuição geográfica
        st.markdown("### Distribuição Geográfica (Prestadores)")
        uf_agg = df.groupby('uf_prestador').agg({
            'valor_servico': 'sum'
        }).reset_index().sort_values('valor_servico', ascending=False)
        
        fig_uf = px.bar(
            uf_agg,
            x='uf_prestador',
            y='valor_servico',
            title="Valor Total por UF (Prestador)",
            labels={'valor_servico': 'Valor Total (R$)', 'uf_prestador': 'UF'}
        )
        st.plotly_chart(fig_uf, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("### Dados Detalhados")
        df_display = df.sort_values('valor_servico', ascending=False)[[
            'timestamp_captura', 'usuario', 'nbs', 'descricao_servico',
            'valor_servico', 'aliquota_iss', 'valor_iss',
            'aliquota_ibs', 'valor_ibs', 'aliquota_cbs', 'valor_cbs',
            'uf_prestador', 'uf_tomador', 'cclasstrib'
        ]]
        
        st.dataframe(df_display, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao processar dados de NFSe: {e}")


def render_export_section(nfe_file: str = None, nfse_file: str = None):
    """Renderiza seção de exportação de dados."""
    
    st.markdown("### Exportação de Dados")
    st.markdown("Baixe os dados capturados em CSV ou Excel para análise externa.")
    
    # NFe Export
    if nfe_file and os.path.isfile(nfe_file):
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV Export
            with open(nfe_file, 'rb') as f:
                st.download_button(
                    label="Baixar Dados de NFe (CSV)",
                    data=f,
                    file_name=f"nfe_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Excel Export
            try:
                import io
                df_nfe = pd.read_csv(nfe_file)
                excel_buffer = io.BytesIO()
                df_nfe.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)
                
                st.download_button(
                    label="Baixar Dados de NFe (Excel)",
                    data=excel_buffer,
                    file_name=f"nfe_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Erro ao gerar Excel: {e}")
    else:
        st.info("Nenhum dado de NFe disponível para exportação.")
    
    # NFSe Export
    if nfse_file and os.path.isfile(nfse_file):
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV Export
            with open(nfse_file, 'rb') as f:
                st.download_button(
                    label="Baixar Dados de NFSe (CSV)",
                    data=f,
                    file_name=f"nfse_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Excel Export
            try:
                import io
                df_nfse = pd.read_csv(nfse_file)
                excel_buffer = io.BytesIO()
                df_nfse.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)
                
                st.download_button(
                    label="Baixar Dados de NFSe (Excel)",
                    data=excel_buffer,
                    file_name=f"nfse_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Erro ao gerar Excel: {e}")
    else:
        st.info("Nenhum dado de NFSe disponível para exportação.")
