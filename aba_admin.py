"""
Módulo de Administração - Visualização de Logs de Autenticação

Acesso restrito ao usuário PriceADM.
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from excel_exporter import exportar_dataframe_para_excel
from user_manager import (
    carregar_usuarios_status,
    salvar_usuarios_status,
    verificar_acesso_usuario,
    obter_info_usuario,
    atualizar_usuario,
    adicionar_usuario,
    remover_usuario,
    listar_usuarios,
    contar_usuarios_por_status,
    verificar_vencimentos_proximos
)


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
        st.error("Acesso Negado")
        st.warning("Esta área é restrita ao administrador do sistema. Apenas o usuário PriceADM tem acesso aos logs de autenticação.")
        return
    
    # Header
    st.markdown("### Painel Administrativo")
    st.markdown("---")
    
    # Tabs para diferentes seções
    tab_users, tab_logs, tab_market = st.tabs([
        "Gestão de Usuários",
        "Logs de Autenticação",
        "Inteligência de Mercado"
    ])
    
    # =========================================================================
    # TAB: GESTÃO DE USUÁRIOS
    # =========================================================================
    with tab_users:
        render_user_management_section()
    
    # =========================================================================
    # TAB: LOGS DE AUTENTICAÇÃO
    # =========================================================================
    with tab_logs:
        render_auth_logs_section()
    
    # =========================================================================
    # TAB: INTELIGÊNCIA DE MERCADO
    # =========================================================================
    with tab_market:
        from market_intelligence_v2 import render_market_intelligence_dashboard
        render_market_intelligence_dashboard()


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
    st.markdown("#### Filtros")
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
            st.markdown("#### Logins por Status")
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
            st.markdown("#### Logins por Usuário")
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
        st.markdown("#### Linha do Tempo de Autenticações")
        
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
    st.markdown("#### Registros Detalhados")
    
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
        excel_bytes = exportar_dataframe_para_excel(
            df_display,
            nome_aba="Logs de Autenticação"
        )
        st.download_button(
            label="Exportar Excel",
            data=excel_bytes,
            file_name=f"logs_autenticacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Informações adicionais
    st.markdown("---")
    st.markdown("##### Informações")
    st.info(f"""
    **Arquivo de log:** `{log_file}`  
    **Total de registros:** {len(df_filtrado)} (filtrados) / {len(df_logs)} (total)  
    **Último acesso:** {df_logs['timestamp'].max().strftime('%d/%m/%Y %H:%M:%S') if not df_logs.empty else 'N/A'}
    """)



def render_user_management_section():
    """Renderiza seção de gestão de usuários."""
    st.markdown("## Gestão de Usuários")
    
    # Carregar usuários
    usuarios = listar_usuarios()
    contagem = contar_usuarios_por_status()
    vencimentos_proximos = verificar_vencimentos_proximos(dias=15)
    
    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Usuários", len(usuarios))
    
    with col2:
        st.metric("Usuários Ativos", contagem.get("ativo", 0), delta="Ativos")
    
    with col3:
        st.metric("Inadimplentes", contagem.get("inadimplente", 0), delta="-Bloqueados", delta_color="inverse")
    
    with col4:
        st.metric("Vencimentos Próximos", len(vencimentos_proximos), delta="15 dias")
    
    st.markdown("---")
    
    # Alertas de vencimentos próximos
    if vencimentos_proximos:
        with st.expander(f"⚠️ Alertas de Vencimento ({len(vencimentos_proximos)} usuários)", expanded=True):
            for user in vencimentos_proximos:
                dias = user["dias_restantes"]
                cor = "🔴" if dias <= 3 else "🟡" if dias <= 7 else "🟢"
                st.warning(f"{cor} **{user['username']}** - Vence em {dias} dia(s) ({user['data_vencimento']})")
    
    st.markdown("---")
    
    # Tabs de ações
    tab_lista, tab_editar, tab_adicionar = st.tabs([
        "Lista de Usuários",
        "Editar Usuário",
        "Adicionar Usuário"
    ])
    
    # =========================================================================
    # TAB: LISTA DE USUÁRIOS
    # =========================================================================
    with tab_lista:
        st.markdown("### Lista Completa de Usuários")
        
        # Filtros
        col_filtro1, col_filtro2 = st.columns(2)
        
        with col_filtro1:
            filtro_status = st.multiselect(
                "Filtrar por Status",
                options=["ativo", "bloqueado", "inadimplente"],
                default=["ativo", "bloqueado", "inadimplente"]
            )
        
        with col_filtro2:
            filtro_tipo = st.multiselect(
                "Filtrar por Tipo",
                options=["administrador", "equipe", "cliente"],
                default=["administrador", "equipe", "cliente"]
            )
        
        # Aplicar filtros
        usuarios_filtrados = [
            u for u in usuarios
            if u.get("status", "ativo") in filtro_status
            and u.get("tipo", "cliente") in filtro_tipo
        ]
        
        if not usuarios_filtrados:
            st.info("Nenhum usuário encontrado com os filtros selecionados.")
        else:
            # Preparar DataFrame
            df_usuarios = pd.DataFrame(usuarios_filtrados)
            
            # Calcular dias restantes
            def calcular_dias_restantes(data_vencimento_str):
                if not data_vencimento_str:
                    return "N/A"
                try:
                    data_vencimento = datetime.strptime(data_vencimento_str, "%Y-%m-%d").date()
                    dias = (data_vencimento - date.today()).days
                    if dias < 0:
                        return f"Vencido há {abs(dias)} dias"
                    return f"{dias} dias"
                except:
                    return "N/A"
            
            df_usuarios["dias_restantes"] = df_usuarios["data_vencimento"].apply(calcular_dias_restantes)
            
            # Formatar datas
            df_usuarios["data_cadastro"] = pd.to_datetime(df_usuarios["data_cadastro"], errors="coerce").dt.strftime("%d/%m/%Y")
            df_usuarios["data_vencimento"] = df_usuarios["data_vencimento"].fillna("N/A")
            
            # Mapear status para ícones
            status_icons = {
                "ativo": "✅",
                "bloqueado": "🚫",
                "inadimplente": "⚠️"
            }
            df_usuarios["status_icon"] = df_usuarios["status"].map(status_icons)
            
            # Selecionar e renomear colunas
            df_display = df_usuarios[[
                "username",
                "status_icon",
                "status",
                "tipo",
                "data_cadastro",
                "data_vencimento",
                "dias_restantes",
                "observacoes"
            ]].copy()
            
            df_display.columns = [
                "Usuário",
                "",
                "Status",
                "Tipo",
                "Data Cadastro",
                "Vencimento",
                "Dias Restantes",
                "Observações"
            ]
            
            # Exibir tabela
            st.dataframe(
                df_display,
                use_container_width=True,
                height=500,
                hide_index=True
            )
            
            # Botão de exportação
            excel_bytes = exportar_dataframe_para_excel(
                df_display,
                nome_aba="Usuários"
            )
            st.download_button(
                label="📥 Exportar para Excel",
                data=excel_bytes,
                file_name=f"usuarios_pricetax_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=False
            )
    
    # =========================================================================
    # TAB: EDITAR USUÁRIO
    # =========================================================================
    with tab_editar:
        st.markdown("### Editar Usuário Existente")
        
        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
        else:
            # Selecionar usuário
            usernames = [u["username"] for u in usuarios]
            selected_user = st.selectbox(
                "Selecione o usuário",
                options=usernames,
                key="edit_user_select"
            )
            
            if selected_user:
                user_data = obter_info_usuario(selected_user)
                
                if user_data:
                    st.markdown(f"#### Editando: **{selected_user}**")
                    
                    col_edit1, col_edit2 = st.columns(2)
                    
                    with col_edit1:
                        novo_status = st.selectbox(
                            "Status",
                            options=["ativo", "bloqueado", "inadimplente"],
                            index=["ativo", "bloqueado", "inadimplente"].index(user_data.get("status", "ativo")),
                            key="edit_status"
                        )
                        
                        novo_tipo = st.selectbox(
                            "Tipo",
                            options=["administrador", "equipe", "cliente"],
                            index=["administrador", "equipe", "cliente"].index(user_data.get("tipo", "cliente")),
                            key="edit_tipo"
                        )
                    
                    with col_edit2:
                        # Data de vencimento
                        data_vencimento_atual = user_data.get("data_vencimento")
                        if data_vencimento_atual:
                            try:
                                data_vencimento_date = datetime.strptime(data_vencimento_atual, "%Y-%m-%d").date()
                            except:
                                data_vencimento_date = None
                        else:
                            data_vencimento_date = None
                        
                        nova_data_vencimento = st.date_input(
                            "Data de Vencimento",
                            value=data_vencimento_date,
                            key="edit_vencimento"
                        )
                        
                        # Checkbox para remover vencimento
                        sem_vencimento = st.checkbox(
                            "Sem vencimento (usuário permanente)",
                            value=(data_vencimento_atual is None),
                            key="edit_sem_vencimento"
                        )
                    
                    novas_observacoes = st.text_area(
                        "Observações",
                        value=user_data.get("observacoes", ""),
                        key="edit_observacoes"
                    )
                    
                    col_btn1, col_btn2 = st.columns([1, 4])
                    
                    with col_btn1:
                        if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                            dados_atualizados = {
                                "status": novo_status,
                                "tipo": novo_tipo,
                                "data_vencimento": None if sem_vencimento else nova_data_vencimento.strftime("%Y-%m-%d"),
                                "observacoes": novas_observacoes
                            }
                            
                            if atualizar_usuario(selected_user, dados_atualizados):
                                st.success(f"✅ Usuário **{selected_user}** atualizado com sucesso!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao atualizar usuário.")
    
    # =========================================================================
    # TAB: ADICIONAR USUÁRIO
    # =========================================================================
    with tab_adicionar:
        st.markdown("### Adicionar Novo Usuário")
        
        st.info("⚠️ **Atenção:** Você precisará adicionar a senha do usuário manualmente no arquivo `secrets.toml` no Streamlit Cloud.")
        
        novo_username = st.text_input(
            "E-mail do Usuário",
            placeholder="usuario@empresa.com.br",
            key="add_username"
        )
        
        col_add1, col_add2 = st.columns(2)
        
        with col_add1:
            novo_tipo_add = st.selectbox(
                "Tipo",
                options=["cliente", "equipe", "administrador"],
                key="add_tipo"
            )
        
        with col_add2:
            nova_data_vencimento_add = st.date_input(
                "Data de Vencimento",
                value=date.today() + timedelta(days=30),
                key="add_vencimento"
            )
            
            sem_vencimento_add = st.checkbox(
                "Sem vencimento (usuário permanente)",
                value=False,
                key="add_sem_vencimento"
            )
        
        novas_observacoes_add = st.text_area(
            "Observações",
            placeholder="Ex: Cliente da empresa XYZ",
            key="add_observacoes"
        )
        
        if st.button("➕ Adicionar Usuário", type="primary", use_container_width=False):
            if not novo_username:
                st.error("❌ Por favor, informe o e-mail do usuário.")
            else:
                # Verificar se usuário já existe
                if obter_info_usuario(novo_username):
                    st.error(f"❌ Usuário **{novo_username}** já existe no sistema.")
                else:
                    data_venc = None if sem_vencimento_add else nova_data_vencimento_add.strftime("%Y-%m-%d")
                    
                    if adicionar_usuario(
                        username=novo_username,
                        tipo=novo_tipo_add,
                        data_vencimento=data_venc,
                        observacoes=novas_observacoes_add
                    ):
                        st.success(f"✅ Usuário **{novo_username}** adicionado com sucesso!")
                        st.warning("⚠️ **Próximo passo:** Adicione a senha do usuário no arquivo `secrets.toml` no Streamlit Cloud.")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao adicionar usuário.")
