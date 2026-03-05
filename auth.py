"""
Módulo de autenticação para o sistema PRICETAX.

Implementa autenticação segura com hash SHA-256 e interface elegante.
"""

import hashlib
import streamlit as st
from datetime import datetime, timezone, timedelta
import os
from user_manager import verificar_acesso_usuario


def log_login(username: str, success: bool):
    """
    Registra tentativa de login em arquivo de log.
    
    Args:
        username: Nome do usuário que tentou fazer login
        success: True se login bem-sucedido, False se falhou
    """
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, "auth_log.txt")
        # Ajustar para fuso horário de Brasília (GMT-3)
        brasilia_tz = timezone(timedelta(hours=-3))
        timestamp = datetime.now(brasilia_tz).strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCESSO" if success else "FALHA"
        
        log_entry = f"[{timestamp}] {status} - Usuário: {username}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        # Não interromper o fluxo se houver erro no log
        print(f"Erro ao registrar log: {e}")


def get_password_hash(password: str) -> str:
    """
    Gera hash SHA-256 de uma senha.
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Hash SHA-256 da senha em hexadecimal
    """
    return hashlib.sha256(password.encode()).hexdigest()


def check_password() -> bool:
    """
    Verifica credenciais do usuário e exibe tela de login elegante.
    
    Returns:
        True se autenticado, False caso contrário
    """
    
    def password_entered():
        """Callback executado quando o usuário tenta fazer login."""
        username = st.session_state.get("username", "").strip()
        password = st.session_state.get("password", "")
        
        # Verificar se secrets está configurado
        if "passwords" not in st.secrets:
            st.error("Erro de configuração: credenciais não encontradas.")
            return
        
        # Verificar credenciais
        if username in st.secrets["passwords"]:
            password_hash = get_password_hash(password)
            if password_hash == st.secrets["passwords"][username]:
                # Verificar status do usuário (mensalidade, bloqueio, etc)
                pode_acessar, mensagem_erro = verificar_acesso_usuario(username)
                
                if not pode_acessar:
                    # Usuário bloqueado ou inadimplente
                    st.session_state["password_correct"] = False
                    st.session_state["access_denied_message"] = mensagem_erro
                    log_login(username, success=False)
                    return
                
                # Credenciais válidas e usuário ativo
                st.session_state["password_correct"] = True
                st.session_state["authenticated_user"] = username
                st.session_state["login_attempts"] = 0
                st.session_state["access_denied_message"] = None
                
                # Registrar login no log
                log_login(username, success=True)
                st.rerun()  # Força atualização imediata da interface
                return
        
        # Credenciais inválidas
        st.session_state["password_correct"] = False
        st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
        
        # Registrar tentativa falha no log
        log_login(username if username else "[vazio]", success=False)
        st.session_state["access_denied_message"] = None
    
    # Verificar se já está autenticado
    if st.session_state.get("password_correct", False):
        return True
    
    # CSS Premium PRICETAX 3.0 - Layout Split Screen (Referências Or Capital + Impostograma)
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    
    /* Ocultar elementos padrão do Streamlit */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* CORRIGIR: Remover retângulo cinza acima do logo */
    .stMarkdown > div {
        background: transparent !important;
        padding: 0 !important;
        border-radius: 0 !important;
        margin: 0 !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Remover TODOS os elementos vazios do Streamlit */
    .element-container:empty,
    .stMarkdown:empty,
    div[data-testid="stVerticalBlock"] > div:empty {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Forçar fundo transparente em containers do Streamlit */
    div[data-testid="stVerticalBlock"],
    div[data-testid="column"],
    .block-container {
        background: transparent !important;
    }
    .stDeployButton {display: none;}
    
    /* Eliminar skeleton/placeholder do Streamlit */
    .element-container:empty {display: none !important;}
    .stMarkdown:empty {display: none !important;}
    div[data-testid="stVerticalBlock"] > div:empty {display: none !important;}
    div[data-testid="stVerticalBlock"] > div[style*="height"] {
        height: 0 !important;
        min-height: 0 !important;
    }
    
    /* Remover TODOS os espaços e elementos brancos do topo */
    .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Forçar remoção de qualquer elemento branco/vazio */
    .stApp > header {
        display: none !important;
    }
    
    div[data-testid="stAppViewContainer"] > section:first-child {
        padding-top: 0 !important;
    }
    
    section[data-testid="stSidebar"] {display: none !important;}
    
    /* Background PRICETAX 2.0 - Preto Profundo com Gradiente Radial */
    .stApp {
        background: #000000;
        background: radial-gradient(circle at top right, #1A1A1A 0%, #000000 100%);
        font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* =========================================================
       LAYOUT SPLIT SCREEN - PRICETAX 3.0
       Lado esquerdo: Proposta de valor + Features + Social Proof
       Lado direito: Formulário de login
    ========================================================= */
    
    /* Forçar scroll para o topo */
    .stApp {
        overflow-y: auto !important;
    }
    
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    
    /* Coluna esquerda - Proposta de valor */
    .login-left {
        background: linear-gradient(145deg, #111111 0%, #0A0A0A 60%, #1A1200 100%);
        min-height: 100vh;
        padding: 3rem 3rem 3rem 3.5rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border-right: 1px solid rgba(255, 221, 0, 0.08);
        position: relative;
        overflow: hidden;
    }
    
    /* Efeito de brilho sutil no fundo esquerdo */
    .login-left::before {
        content: '';
        position: absolute;
        top: -200px;
        right: -200px;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(255, 221, 0, 0.06) 0%, transparent 70%);
        pointer-events: none;
    }
    
    .login-left::after {
        content: '';
        position: absolute;
        bottom: -150px;
        left: -150px;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(255, 221, 0, 0.04) 0%, transparent 70%);
        pointer-events: none;
    }
    
    /* Logo container */
    .logo-container {
        margin-bottom: 2.5rem;
    }
    
    .logo-container img {
        max-width: 200px;
        height: auto;
        filter: drop-shadow(0 4px 16px rgba(255, 221, 0, 0.4));
    }
    
    /* Headline principal */
    .login-headline {
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 1rem;
        font-family: 'Poppins', sans-serif;
        color: #FFFFFF;
    }
    
    .login-headline span {
        color: #FFDD00;
    }
    
    /* Subtítulo */
    .login-subtitle {
        color: #AAAAAA;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 2.5rem;
        line-height: 1.7;
        font-family: 'Poppins', sans-serif;
        max-width: 420px;
    }
    
    /* Lista de features */
    .feature-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin-bottom: 2.5rem;
    }
    
    .feature-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.875rem 1.25rem;
        background: rgba(255, 221, 0, 0.04);
        border: 1px solid rgba(255, 221, 0, 0.1);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .feature-item:hover {
        background: rgba(255, 221, 0, 0.08);
        border-color: rgba(255, 221, 0, 0.25);
        transform: translateX(4px);
    }
    
    .feature-icon {
        width: 40px;
        height: 40px;
        min-width: 40px;
        background: rgba(255, 221, 0, 0.12);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(255, 221, 0, 0.2);
    }
    
    .feature-icon svg {
        width: 18px;
        height: 18px;
        fill: #FFDD00;
    }
    
    .feature-text {
        color: #DDDDDD;
        font-size: 0.9rem;
        font-weight: 500;
        font-family: 'Poppins', sans-serif;
        line-height: 1.4;
    }
    
    /* Faixa de social proof */
    .social-proof {
        display: flex;
        gap: 1.5rem;
        flex-wrap: wrap;
    }
    
    .proof-item {
        display: flex;
        flex-direction: column;
    }
    
    .proof-number {
        color: #FFDD00;
        font-size: 1.5rem;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        line-height: 1;
    }
    
    .proof-label {
        color: #777777;
        font-size: 0.75rem;
        font-weight: 400;
        font-family: 'Poppins', sans-serif;
        margin-top: 2px;
    }
    
    .proof-divider {
        width: 1px;
        background: rgba(255, 255, 255, 0.1);
        align-self: stretch;
    }
    
    /* Coluna direita - Formulário */
    .login-right {
        background: #0D0D0D;
        min-height: 100vh;
        padding: 3rem 3rem 3rem 3.5rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Título do formulário */
    .login-title {
        color: #FFFFFF;
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-family: 'Poppins', sans-serif;
    }
    
    .login-form-subtitle {
        color: #777777;
        font-size: 0.875rem;
        font-weight: 400;
        margin-bottom: 2rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Card de formulário - Flutuante e compacto */
    .stTextInput,
    .stButton {
        background: #1A1A1A;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 221, 0, 0.15);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    }
    
    /* Inputs - Estilo C6 Premium */
    .stTextInput > div > div > input {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        background: #2A2A2A;
        color: #FFFFFF;
        font-family: 'Poppins', sans-serif;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #FFDD00;
        background: #2A2A2A;
        box-shadow: 0 0 0 3px rgba(255, 221, 0, 0.15);
        outline: none;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #666666;
    }
    
    .stTextInput > label {
        color: #999999;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Botão ENTRAR - Estilo C6 Premium */
    .stButton > button {
        background: #FFDD00;
        color: #000000;
        border: none;
        border-radius: 24px;
        padding: 1rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        width: 100%;
        margin-top: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 24px rgba(255, 221, 0, 0.4);
        text-transform: uppercase;
        font-family: 'Poppins', sans-serif;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(255, 221, 0, 0.5);
        background: #E6C700;
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Mensagens de erro - Estilo C6 */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid #EF4444;
        background: rgba(239, 68, 68, 0.1);
        padding: 1rem 1.25rem;
        margin-top: 1.5rem;
        color: #EF4444;
        font-family: 'Poppins', sans-serif;
        font-size: 0.875rem;
    }
    
    /* Botão WhatsApp - Verde oficial */
    .whatsapp-button {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        background: #25D366;
        color: #ffffff;
        border: none;
        border-radius: 30px;
        padding: 14px 28px;
        font-size: 15px;
        font-weight: 600;
        text-decoration: none;
        width: 100%;
        margin-top: 15px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(37, 211, 102, 0.3);
        cursor: pointer;
    }
    
    .whatsapp-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(37, 211, 102, 0.4);
        background: #20BA5A;
        text-decoration: none;
        color: #ffffff;
    }
    
    .whatsapp-button svg {
        width: 22px;
        height: 22px;
        fill: #ffffff;
    }
    
    /* Rodapé */
    .login-footer {
        text-align: center;
        color: #666666;
        font-size: 0.75rem;
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        font-family: 'Poppins', sans-serif;
    }
    
    /* Animação de entrada - Estilo C6 */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(40px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes glow {
        0%, 100% {
            opacity: 0.5;
        }
        50% {
            opacity: 1;
        }
    }
    
    .login-container {
        animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .login-container::before {
        animation: glow 3s ease-in-out infinite;
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .login-container {
            padding: 2rem 1.5rem;
            min-height: 100vh;
        }
        
        .login-title {
            font-size: 2rem;
        }
        
        .logo-container img {
            max-width: 220px;
        }
        
        .stButton > button {
            padding: 0.875rem 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Layout Split Screen: duas colunas Streamlit
    col_left, col_right = st.columns([1.1, 0.9])
    
    # ---- COLUNA ESQUERDA: Proposta de valor ----
    with col_left:
        st.markdown('<div class="login-left">', unsafe_allow_html=True)
        
        # Logo
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        try:
            import base64
            with open("logo_x_questao.png", "rb") as img_file:
                logo_data = base64.b64encode(img_file.read()).decode()
            st.markdown(
                f'<img src="data:image/png;base64,{logo_data}" alt="PRICETAX">',
                unsafe_allow_html=True
            )
        except FileNotFoundError:
            st.markdown('<div class="login-title" style="font-size:2rem;text-align:left;">PRICETAX</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Headline
        st.markdown(
            '''
            <div class="login-headline">
                Inteligência Tributária<br>
                para a <span>Reforma</span>
            </div>
            <div class="login-subtitle">
                Soluções para a transição inteligente na Reforma Tributária.
                Parametrize, analise e decida com precisão.
            </div>
            ''',
            unsafe_allow_html=True
        )
        
        # Features com ícones SVG circulares dourados
        st.markdown(
            '''
            <div class="feature-list">
                <div class="feature-item">
                    <div class="feature-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke="#FFDD00" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span class="feature-text">Milhares de NCMs com CST de IBS e CBS mapeados</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" stroke="#FFDD00" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span class="feature-text">Regimes especiais, monofásico e reduções de alíquota</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="#FFDD00" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span class="feature-text">Operações internas, interestaduais e exportação</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" stroke="#FFDD00" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span class="feature-text">Base legal LC 214/2025 — Cesta Básica, isenções e benefícios</span>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="#FFDD00" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span class="feature-text">Análise de EFD SPED com ranking de impacto tributário</span>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
        
        # Social proof
        st.markdown(
            '''
            <div class="social-proof">
                <div class="proof-item">
                    <span class="proof-number">+5.000</span>
                    <span class="proof-label">Empresas atendidas</span>
                </div>
                <div class="proof-divider"></div>
                <div class="proof-item">
                    <span class="proof-number">+600</span>
                    <span class="proof-label">CFOPs mapeados</span>
                </div>
                <div class="proof-divider"></div>
                <div class="proof-item">
                    <span class="proof-number">LC 214</span>
                    <span class="proof-label">Reforma 2026</span>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ---- COLUNA DIREITA: Formulário ----
    with col_right:
        st.markdown('<div class="login-right">', unsafe_allow_html=True)
        
        st.markdown(
            '''
            <div class="login-title">Acessar plataforma</div>
            <div class="login-form-subtitle">Insira suas credenciais para continuar</div>
            ''',
            unsafe_allow_html=True
        )
        
        # Formulário de login
        st.text_input(
            "Usuário",
            key="username",
            placeholder="Digite seu usuário",
            label_visibility="visible"
        )
        
        st.text_input(
            "Senha",
            type="password",
            key="password",
            placeholder="Digite sua senha",
            label_visibility="visible"
        )
        
        # Botão de login
        if st.button("Entrar", type="primary", use_container_width=True):
            password_entered()
        
        # Exibir erro se credenciais inválidas ou acesso negado
        if st.session_state.get("password_correct") == False:
            access_denied_msg = st.session_state.get("access_denied_message")
            if access_denied_msg:
                st.error(access_denied_msg)
            else:
                attempts = st.session_state.get("login_attempts", 0)
                st.error(f"Usuário ou senha incorretos. Tentativa {attempts}.")
        
        # Botão WhatsApp para solicitar acesso
        st.markdown(
            '''
            <a href="https://wa.me/5541998924080" target="_blank" class="whatsapp-button">
                <svg width="22" height="22" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                </svg>
                Solicitar Acesso
            </a>
            ''',
            unsafe_allow_html=True
        )
        
        # Rodapé
        st.markdown(
            '<div class="login-footer">Autenticação segura com criptografia de padrão internacional e conformidade com LGPD</div>',
            unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False


def show_logout_button():
    """Exibe botão de logout no canto superior direito."""
    authenticated_user = st.session_state.get("authenticated_user", "Usuário")
    
    # CSS para botão de logout no canto superior direito
    st.markdown("""
    <style>
    /* Container do botão de logout */
    .logout-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 12px;
        background: #ffffff;
        padding: 10px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    .logout-user {
        color: #334155;
        font-size: 14px;
        font-weight: 600;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .logout-btn {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25);
    }
    
    .logout-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35);
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
    }
    
    /* Responsivo para mobile */
    @media (max-width: 768px) {
        .logout-container {
            top: 10px;
            right: 10px;
            padding: 8px 14px;
            gap: 8px;
        }
        
        .logout-user {
            font-size: 12px;
        }
        
        .logout-btn {
            padding: 6px 14px;
            font-size: 12px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Criar container com botão de logout
    col1, col2 = st.columns([6, 1])
    
    with col2:
        if st.button("Sair", key="logout_button", help=f"Desconectar ({authenticated_user})"):
            # Limpar session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
