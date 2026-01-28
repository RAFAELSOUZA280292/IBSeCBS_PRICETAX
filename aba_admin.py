"""
Módulo de Administração - Visualização de Logs de Autenticação

Acesso restrito ao usuário PriceADM.
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go


def parse_log_file(log_file_path: str) -> pd.DataFrame:
    """
    Parse do arquivo de log para DataFrame.
    
    Args:
        log_file_path: Caminho do arquivo de log
        
    Returns:
        DataFrame com colunas: timestamp, status, usuario
    """
    if not os.path.exists(log_file_path):
        return pd.DataFrame(columns=["timestamp", "status", "usuario"])
    
    logs = []
    
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Formato: [2026-01-26 16:45:23] SUCESSO - Usuário: PriceADM
                try:
                    # Extrair timestamp
                    timestamp_str = line[1:20]  # [YYYY-MM-DD HH:MM:SS]
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    
                    # Extrair status
                    if "SUCESSO" in line:
                        status = "SUCESSO"
                    elif "FALHA" in line:
                        status = "FALHA"
                    else:
                        continue
                    
                    # Extrair usuário
                    usuario = line.split("Usuário: ")[1].strip()
                    
                    logs.append({
                        "timestamp": timestamp,
                        "status": status,
                        "usuario": usuario
                    })
                except Exception as e:
                    print(f"Erro ao parsear linha: {line} - {e}")
                    continue
    except Exception as e:
        st.error(f"Erro ao ler arquivo de log: {e}")
        return pd.DataFrame(columns=["timestamp", "status", "usuario"])
    
    if not logs:
        return pd.DataFrame(columns=["timestamp", "status", "usuario"])
    
    df = pd.DataFrame(logs)
    df = df.sort_values("timestamp", ascending=False)
    
    return df


def render_admin_tab():
    """Renderiza a aba administrativa de logs."""
    
    # Verificar se usuário é PriceADM
    authenticated_user = st.session_state.get("authenticated_user", "")
    
    if authenticated_user != "PriceADM":
        st.error("🔒 Acesso Negado")
        st.warning("Esta área é restrita ao administrador do sistema.")
        st.info("Apenas o usuário **PriceADM** pode acessar os logs de autenticação.")
        return
    
    # Header
    st.markdown("### Painel Administrativo")
    st.markdown("---")
    
    # Tabs para diferentes seções
    tab_logs, tab_market = st.tabs([
        "Logs de Autenticação",
        "Inteligência de Mercado"
    ])
    
    # =========================================================================
    # TAB: LOGS DE AUTENTICAÇÃO
    # =========================================================================
    with tab_logs:
        render_auth_logs_section()
    
    # =========================================================================
    # TAB: INTELIGÊNCIA DE MERCADO
    # =========================================================================
    with tab_market:
        from market_intelligence import render_market_intelligence_tab
        render_market_intelligence_tab()


def render_auth_logs_section():
    """Renderiza seção de logs de autenticação."""
    st.markdown("## Logs de Autenticação")
    
    # Carregar logs
    log_file = "logs/auth_log.txt"
    df_logs = parse_log_file(log_file)
    
    if df_logs.empty:
        st.info("Nenhum registro de autenticação encontrado.")
        st.markdown("Os logs serão gerados automaticamente quando usuários fizerem login.")
        return
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    total_logins = len(df_logs)
    sucessos = len(df_logs[df_logs["status"] == "SUCESSO"])
    falhas = len(df_logs[df_logs["status"] == "FALHA"])
    taxa_sucesso = (sucessos / total_logins * 100) if total_logins > 0 else 0
    
    with col1:
        st.metric("Total de Tentativas", total_logins)
    
    with col2:
        st.metric("Logins Bem-Sucedidos", sucessos, delta=f"{taxa_sucesso:.1f}%")
    
    with col3:
        st.metric("Tentativas Falhas", falhas, delta=f"-{100-taxa_sucesso:.1f}%", delta_color="inverse")
    
    with col4:
        usuarios_unicos = df_logs[df_logs["status"] == "SUCESSO"]["usuario"].nunique()
        st.metric("Usuários Ativos", usuarios_unicos)
    
    st.markdown("---")
    
    # Filtros
    st.markdown("#### 🔍 Filtros")
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        filtro_status = st.multiselect(
            "Status",
            options=["SUCESSO", "FALHA"],
            default=["SUCESSO", "FALHA"]
        )
    
    with col_filtro2:
        usuarios_disponiveis = sorted(df_logs["usuario"].unique().tolist())
        filtro_usuario = st.multiselect(
            "Usuário",
            options=usuarios_disponiveis,
            default=usuarios_disponiveis
        )
    
    with col_filtro3:
        periodo = st.selectbox(
            "Período",
            options=["Todos", "Últimas 24h", "Últimos 7 dias", "Últimos 30 dias"],
            index=0
        )
    
    # Aplicar filtros
    df_filtrado = df_logs.copy()
    
    if filtro_status:
        df_filtrado = df_filtrado[df_filtrado["status"].isin(filtro_status)]
    
    if filtro_usuario:
        df_filtrado = df_filtrado[df_filtrado["usuario"].isin(filtro_usuario)]
    
    if periodo != "Todos":
        now = datetime.now()
        if periodo == "Últimas 24h":
            limite = now - timedelta(hours=24)
        elif periodo == "Últimos 7 dias":
            limite = now - timedelta(days=7)
        elif periodo == "Últimos 30 dias":
            limite = now - timedelta(days=30)
        
        df_filtrado = df_filtrado[df_filtrado["timestamp"] >= limite]
    
    st.markdown("---")
    
    # Gráficos
    if not df_filtrado.empty:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("#### 📊 Logins por Status")
            status_counts = df_filtrado["status"].value_counts()
            
            fig_status = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                marker=dict(colors=["#10b981", "#ef4444"]),
                hole=0.4
            )])
            
            fig_status.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True
            )
            
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col_graf2:
            st.markdown("#### 👥 Logins por Usuário")
            usuario_counts = df_filtrado["usuario"].value_counts().head(10)
            
            fig_usuarios = go.Figure(data=[go.Bar(
                x=usuario_counts.values,
                y=usuario_counts.index,
                orientation='h',
                marker=dict(color='#f59e0b')
            )])
            
            fig_usuarios.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Tentativas",
                yaxis_title="Usuário"
            )
            
            st.plotly_chart(fig_usuarios, use_container_width=True)
        
        # Gráfico de linha temporal
        st.markdown("#### 📈 Linha do Tempo de Autenticações")
        
        df_timeline = df_filtrado.copy()
        df_timeline["data"] = df_timeline["timestamp"].dt.date
        timeline_data = df_timeline.groupby(["data", "status"]).size().reset_index(name="count")
        
        fig_timeline = px.line(
            timeline_data,
            x="data",
            y="count",
            color="status",
            color_discrete_map={"SUCESSO": "#10b981", "FALHA": "#ef4444"},
            markers=True
        )
        
        fig_timeline.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Data",
            yaxis_title="Quantidade",
            legend_title="Status"
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.markdown("---")
    
    # Tabela de logs
    st.markdown("#### 📋 Registros Detalhados")
    
    # Preparar DataFrame para exibição
    df_display = df_filtrado.copy()
    df_display["Data/Hora"] = df_display["timestamp"].dt.strftime("%d/%m/%Y %H:%M:%S")
    df_display["Status"] = df_display["status"]
    df_display["Usuário"] = df_display["usuario"]
    
    df_display = df_display[["Data/Hora", "Status", "Usuário"]]
    
    # Exibir tabela com estilo
    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
        hide_index=True
    )
    
    # Botão de exportação
    col_export1, col_export2 = st.columns([1, 5])
    
    with col_export1:
        csv = df_display.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Exportar CSV",
            data=csv,
            file_name=f"logs_autenticacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Informações adicionais
    st.markdown("---")
    st.markdown("##### ℹ️ Informações")
    st.info(f"""
    **Arquivo de log:** `{log_file}`  
    **Total de registros:** {len(df_filtrado)} (filtrados) / {len(df_logs)} (total)  
    **Último acesso:** {df_logs['timestamp'].max().strftime('%d/%m/%Y %H:%M:%S') if not df_logs.empty else 'N/A'}
    """)
