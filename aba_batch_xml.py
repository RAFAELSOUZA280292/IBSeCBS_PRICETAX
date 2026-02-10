"""
Aba: Processamento em Lote de XMLs NFe
=======================================

Interface Streamlit para processamento em lote de até 500 XMLs com validação
completa, geração de relatório Excel e integração com data_collector (espião).

Autor: PRICETAX
Data: 06/02/2026
"""

import streamlit as st
import os
import tempfile
import shutil
from datetime import datetime

from batch_xml_processor import (
    extract_zip_to_temp,
    process_batch,
    generate_summary_stats,
    generate_excel_report
)

# Cores PRICETAX
COLOR_GOLD = "#FFDD00"
COLOR_BLUE = "#0056B3"
COLOR_CARD_BG = "#1E1E1E"
COLOR_TEXT_MAIN = "#FFFFFF"
COLOR_TEXT_MUTED = "#AAAAAA"
COLOR_BORDER = "#333333"
COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_ERROR = "#EF4444"


def render_aba_batch_xml():
    """
    Renderiza a aba de Processamento em Lote de XMLs.
    """
    
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
            <h2 style="color: {COLOR_GOLD}; margin: 0 0 0.5rem 0;">
                Processamento em Lote de XMLs NFe
            </h2>
            <p style="color: {COLOR_TEXT_MUTED}; margin: 0; font-size: 0.95rem;">
                Processe até 500 XMLs simultaneamente com validação completa de IBS/CBS,
                relatório Excel profissional e integração automática com Inteligência de Mercado.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Cards de funcionalidades
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div style="
                background: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;"></div>
                <strong style="color: {COLOR_GOLD};">Validação Completa</strong><br>
                <span style="color: {COLOR_TEXT_MUTED}; font-size: 0.85rem;">
                    IBS/CBS, cClassTrib, estrutura XML
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="
                background: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;"></div>
                <strong style="color: {COLOR_GOLD};">Relatório Excel</strong><br>
                <span style="color: {COLOR_TEXT_MUTED}; font-size: 0.85rem;">
                    4 abas profissionais com análise detalhada
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div style="
                background: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 1rem;
                text-align: center;
            ">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;"></div>
                <strong style="color: {COLOR_GOLD};">Processamento Rápido</strong><br>
                <span style="color: {COLOR_TEXT_MUTED}; font-size: 0.85rem;">
                    Até 500 XMLs em poucos minutos
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Seção de upload
    st.markdown(
        f"""
        <div style="
            background: {COLOR_CARD_BG};
            border-left: 4px solid {COLOR_BLUE};
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        ">
            <strong style="color: {COLOR_BLUE};">Upload de XMLs</strong><br>
            <span style="color: {COLOR_TEXT_MUTED}; font-size: 0.9rem;">
                Envie um arquivo ZIP contendo até 500 XMLs ou selecione múltiplos arquivos XML
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Opções de upload
    upload_option = st.radio(
        "Escolha o método de upload:",
        ["Arquivo ZIP (recomendado para grandes volumes)", "Múltiplos XMLs"],
        key="upload_option"
    )
    
    xml_files = []
    temp_dir = None
    
    if "ZIP" in upload_option:
        # Upload de ZIP
        zip_file = st.file_uploader(
            "Selecione o arquivo ZIP",
            type=['zip'],
            key="zip_uploader"
        )
        
        if zip_file:
            try:
                with st.spinner("Extraindo arquivos..."):
                    temp_dir, xml_files = extract_zip_to_temp(zip_file)
                
                st.success(f"{len(xml_files)} XMLs encontrados no ZIP")
            
            except Exception as e:
                st.error(f"Erro ao extrair ZIP: {str(e)}")
    
    else:
        # Upload de múltiplos XMLs
        uploaded_files = st.file_uploader(
            "Selecione os arquivos XML",
            type=['xml'],
            accept_multiple_files=True,
            key="xml_uploader"
        )
        
        if uploaded_files:
            # Salvar em diretório temporário
            temp_dir = tempfile.mkdtemp(prefix="pricetax_batch_")
            
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                xml_files.append(file_path)
            
            st.success(f"{len(xml_files)} XMLs carregados")
    
    # Validar limite
    if len(xml_files) > 500:
        st.error(f"Limite excedido! Máximo de 500 XMLs por lote. Você enviou {len(xml_files)}.")
        xml_files = []
    
    # Configurações
    if xml_files:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Configurações fixas (invisíveis ao usuário)
        save_to_collector = True  # Sempre ativo
        tolerancia = 0.30  # R$ 0,30 fixo
        
        # Botão de processar
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Processar Lote", type="primary", use_container_width=True):
            # Processar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            resultados = []
            
            def update_progress(current, total, filename):
                progress = current / total
                progress_bar.progress(progress)
                status_text.text(f"Processando {current}/{total}: {filename}")
            
            with st.spinner("Processando XMLs..."):
                resultados = process_batch(
                    xml_files,
                    save_to_collector=save_to_collector,
                    progress_callback=update_progress
                )
            
            progress_bar.empty()
            status_text.empty()
            
            # Gerar estatísticas
            stats = generate_summary_stats(resultados)
            
            # Exibir resumo
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, {COLOR_SUCCESS} 0%, #059669 100%);
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin: 1.5rem 0;
                ">
                    <h3 style="color: white; margin: 0 0 1rem 0;">Processamento Concluído</h3>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; color: white;">
                        <div>
                            <div style="font-size: 2rem; font-weight: bold;">{stats['total_xmls']}</div>
                            <div style="font-size: 0.85rem; opacity: 0.9;">XMLs Processados</div>
                        </div>
                        <div>
                            <div style="font-size: 2rem; font-weight: bold;">{stats['xmls_conformes']}</div>
                            <div style="font-size: 0.85rem; opacity: 0.9;">Conformes</div>
                        </div>
                        <div>
                            <div style="font-size: 2rem; font-weight: bold;">{stats['xmls_divergentes']}</div>
                            <div style="font-size: 0.85rem; opacity: 0.9;">Divergentes</div>
                        </div>
                        <div>
                            <div style="font-size: 2rem; font-weight: bold;">{stats['percentual_conformes']:.1f}%</div>
                            <div style="font-size: 0.85rem; opacity: 0.9;">Taxa de Conformidade</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Detalhes adicionais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Itens", f"{stats['total_itens']:,}")
            
            with col2:
                st.metric("Itens Conformes", f"{stats['itens_conformes']:,}")
            
            with col3:
                st.metric("Valor Total", f"R$ {stats['valor_total']:,.2f}")
            
            # DASHBOARDS DE GOVERNANÇA FISCAL IBS/CBS
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style="
                    background: {COLOR_CARD_BG};
                    border-left: 4px solid {COLOR_GOLD};
                    padding: 1.5rem;
                    border-radius: 8px;
                    margin-bottom: 1.5rem;
                ">
                    <h3 style="color: {COLOR_GOLD}; margin: 0 0 0.5rem 0;">
                        📈 Dashboards de Governança Fiscal IBS/CBS
                    </h3>
                    <p style="color: {COLOR_TEXT_MUTED}; margin: 0; font-size: 0.9rem;">
                        Análise visual de conformidade e distribuição de itens
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Cards de métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, {COLOR_SUCCESS} 0%, #059669 100%);
                        padding: 1.5rem;
                        border-radius: 8px;
                        text-align: center;
                        color: white;
                    ">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">
                            {stats['itens_conformes']:,}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">
                            Itens Conformes
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.5rem;">
                            {(stats['itens_conformes']/stats['total_itens']*100) if stats['total_itens'] > 0 else 0:.1f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, {COLOR_ERROR} 0%, #DC2626 100%);
                        padding: 1.5rem;
                        border-radius: 8px;
                        text-align: center;
                        color: white;
                    ">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">
                            {stats['itens_divergentes']:,}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">
                            Itens Divergentes
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.5rem;">
                            {(stats['itens_divergentes']/stats['total_itens']*100) if stats['total_itens'] > 0 else 0:.1f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col3:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, {COLOR_BLUE} 0%, #0047AB 100%);
                        padding: 1.5rem;
                        border-radius: 8px;
                        text-align: center;
                        color: white;
                    ">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">
                            {stats['xmls_conformes']}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">
                            NFes Conformes
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.5rem;">
                            {stats['percentual_conformes']:.1f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col4:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, {COLOR_WARNING} 0%, #D97706 100%);
                        padding: 1.5rem;
                        border-radius: 8px;
                        text-align: center;
                        color: white;
                    ">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem;">
                            {stats['xmls_divergentes']}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">
                            NFes Divergentes
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.5rem;">
                            {(100 - stats['percentual_conformes']):.1f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Gráficos de conformidade
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de pizza - Conformidade de Itens
                import plotly.graph_objects as go
                
                fig_itens = go.Figure(data=[go.Pie(
                    labels=['Conformes', 'Divergentes'],
                    values=[stats['itens_conformes'], stats['itens_divergentes']],
                    hole=0.4,
                    marker=dict(
                        colors=[COLOR_SUCCESS, COLOR_ERROR],
                        line=dict(color='#000000', width=2)
                    ),
                    textinfo='label+percent',
                    textfont=dict(size=14, color='white'),
                    hovertemplate='<b>%{label}</b><br>%{value:,} itens<br>%{percent}<extra></extra>'
                )])
                
                fig_itens.update_layout(
                    title=dict(
                        text='Conformidade de Itens',
                        font=dict(size=18, color=COLOR_GOLD, family='Arial Black')
                    ),
                    paper_bgcolor=COLOR_CARD_BG,
                    plot_bgcolor=COLOR_CARD_BG,
                    font=dict(color=COLOR_TEXT_MAIN),
                    showlegend=True,
                    legend=dict(
                        bgcolor=COLOR_CARD_BG,
                        bordercolor=COLOR_BORDER,
                        borderwidth=1
                    ),
                    height=400
                )
                
                st.plotly_chart(fig_itens, use_container_width=True)
            
            with col2:
                # Gráfico de pizza - Conformidade de NFes
                fig_nfes = go.Figure(data=[go.Pie(
                    labels=['Conformes', 'Divergentes'],
                    values=[stats['xmls_conformes'], stats['xmls_divergentes']],
                    hole=0.4,
                    marker=dict(
                        colors=[COLOR_BLUE, COLOR_WARNING],
                        line=dict(color='#000000', width=2)
                    ),
                    textinfo='label+percent',
                    textfont=dict(size=14, color='white'),
                    hovertemplate='<b>%{label}</b><br>%{value:,} NFes<br>%{percent}<extra></extra>'
                )])
                
                fig_nfes.update_layout(
                    title=dict(
                        text='Conformidade de NFes',
                        font=dict(size=18, color=COLOR_GOLD, family='Arial Black')
                    ),
                    paper_bgcolor=COLOR_CARD_BG,
                    plot_bgcolor=COLOR_CARD_BG,
                    font=dict(color=COLOR_TEXT_MAIN),
                    showlegend=True,
                    legend=dict(
                        bgcolor=COLOR_CARD_BG,
                        bordercolor=COLOR_BORDER,
                        borderwidth=1
                    ),
                    height=400
                )
                
                st.plotly_chart(fig_nfes, use_container_width=True)
            
            # Tabelas de itens conformes e divergentes
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Separar itens conformes e divergentes
            itens_conformes_lista = []
            itens_divergentes_lista = []
            
            for resultado in resultados:
                if resultado['status'] == 'sucesso':
                    for item in resultado.get('itens_conformes', []):
                        itens_conformes_lista.append({
                            'NFe': os.path.basename(resultado['arquivo']),
                            'Item': item['item'],
                            'NCM': item['ncm'],
                            'Descrição': item['descricao'][:50] + '...' if len(item['descricao']) > 50 else item['descricao'],
                            'Valor (R$)': f"R$ {item['valor']:,.2f}",
                            'IBS XML (R$)': f"R$ {item['ibs_xml']:.2f}",
                            'CBS XML (R$)': f"R$ {item['cbs_xml']:.2f}"
                        })
                    
                    for item in resultado.get('itens_divergentes', []):
                        itens_divergentes_lista.append({
                            'NFe': os.path.basename(resultado['arquivo']),
                            'Item': item['item'],
                            'NCM': item['ncm'],
                            'Descrição': item['descricao'][:50] + '...' if len(item['descricao']) > 50 else item['descricao'],
                            'Valor (R$)': f"R$ {item['valor']:,.2f}",
                            'IBS Dif (R$)': f"R$ {item['diff_ibs']:.2f}",
                            'CBS Dif (R$)': f"R$ {item['diff_cbs']:.2f}"
                        })
            
            # Tabs para conformes e divergentes
            tab1, tab2 = st.tabs([f"✅ Itens Conformes ({len(itens_conformes_lista)})", f"⚠️ Itens Divergentes ({len(itens_divergentes_lista)})"])
            
            with tab1:
                if itens_conformes_lista:
                    import pandas as pd
                    df_conformes = pd.DataFrame(itens_conformes_lista)
                    st.dataframe(
                        df_conformes,
                        use_container_width=True,
                        height=400
                    )
                else:
                    st.info("Nenhum item conforme encontrado.")
            
            with tab2:
                if itens_divergentes_lista:
                    import pandas as pd
                    df_divergentes = pd.DataFrame(itens_divergentes_lista)
                    st.dataframe(
                        df_divergentes,
                        use_container_width=True,
                        height=400
                    )
                else:
                    st.success("Nenhum item divergente encontrado! Todos os itens estão conformes.")
            
            # Gerar Excel
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.spinner("Gerando relatório Excel..."):
                excel_file = generate_excel_report(resultados)
            
            # Download
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"relatorio_lote_pricetax_{timestamp}.xlsx"
            
            st.download_button(
                label="📥 Download Relatório Excel",
                data=excel_file,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # Informações sobre o relatório
            st.markdown(
                f"""
                <div style="
                    background: {COLOR_CARD_BG};
                    border: 1px solid {COLOR_BORDER};
                    padding: 1rem;
                    border-radius: 4px;
                    margin-top: 1rem;
                ">
                    <strong style="color: {COLOR_GOLD};">📊 Conteúdo do Relatório Excel</strong><br><br>
                    <ul style="color: {COLOR_TEXT_MUTED}; font-size: 0.9rem; margin: 0;">
                        <li><strong>Aba "Resumo":</strong> Estatísticas gerais do processamento</li>
                        <li><strong>Aba "Validação":</strong> Lista completa de todos os XMLs processados</li>
                        <li><strong>Aba "Divergências":</strong> Apenas XMLs com problemas detectados</li>
                        <li><strong>Aba "Dados Completos":</strong> Detalhamento item por item com validação IBS/CBS</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Salvar resultados na sessão para consulta
            st.session_state['batch_results'] = resultados
            st.session_state['batch_stats'] = stats
    
    # Limpar diretório temporário ao final
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
    
    # Rodapé informativo
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown(
        f"""
        <div style="
            background: {COLOR_CARD_BG};
            border-top: 1px solid {COLOR_BORDER};
            padding: 1rem;
            border-radius: 4px;
            text-align: center;
            color: {COLOR_TEXT_MUTED};
            font-size: 0.85rem;
        ">
            <strong style="color: {COLOR_GOLD};">💡 Dica:</strong> 
            Para grandes volumes, comprima seus XMLs em um arquivo ZIP antes do upload.
            O processamento é mais rápido e eficiente!
        </div>
        """,
        unsafe_allow_html=True
    )
