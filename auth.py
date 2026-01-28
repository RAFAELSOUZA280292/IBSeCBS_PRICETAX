"""
Módulo de autenticação para o sistema PRICETAX.

Implementa autenticação segura com hash SHA-256 e interface elegante.
"""

import hashlib
import streamlit as st
from datetime import datetime, timezone, timedelta
import os


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
                st.session_state["password_correct"] = True
                st.session_state["authenticated_user"] = username
                st.session_state["login_attempts"] = 0
                
                # Registrar login no log
                log_login(username, success=True)
                return
        
        # Credenciais inválidas
        st.session_state["password_correct"] = False
        st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
        
        # Registrar tentativa falha no log
        log_login(username if username else "[vazio]", success=False)
    
    # Verificar se já está autenticado
    if st.session_state.get("password_correct", False):
        return True
    
    # CSS Premium PRICETAX - Identidade Visual Oficial
    st.markdown("""
    <style>
    /* Ocultar elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Eliminar skeleton/placeholder do Streamlit */
    .element-container:empty {display: none !important;}
    .stMarkdown:empty {display: none !important;}
    div[data-testid="stVerticalBlock"] > div:empty {display: none !important;}
    div[data-testid="stVerticalBlock"] > div[style*="height"] {
        height: 0 !important;
        min-height: 0 !important;
    }
    
    .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    section[data-testid="stSidebar"] {display: none !important;}
    
    /* Background PRICETAX - Escuro profissional */
    .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    }
    
    /* Container de login - Estilo PRICETAX */
    .login-container {
        max-width: 480px;
        margin: 60px auto;
        padding: 50px 45px;
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        border: 2px solid rgba(255, 221, 0, 0.3);
    }
    
    /* Logo container */
    .logo-container {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .logo-container img {
        max-width: 350px;
        height: auto;
        margin-bottom: 20px;
        filter: drop-shadow(0 4px 12px rgba(255, 221, 0, 0.3));
    }
    
    /* Título PRICETAX - Amarelo oficial */
    .login-title {
        text-align: center;
        color: #1a1a1a;
        font-size: 42px;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 8px;
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        text-transform: uppercase;
    }
    
    .login-title-highlight {
        color: #FFDD00;
        text-shadow: 0 2px 8px rgba(255, 221, 0, 0.3);
    }
    
    /* Subtítulo - Estilo PRICETAX */
    .login-subtitle {
        text-align: center;
        color: #4a4a4a;
        font-size: 15px;
        font-weight: 400;
        margin-bottom: 35px;
        line-height: 1.6;
    }
    
    /* Inputs - Foco amarelo PRICETAX */
    .stTextInput > div > div > input {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px 20px;
        font-size: 15px;
        transition: all 0.3s ease;
        background: #fafafa;
        color: #1a1a1a;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #FFDD00;
        background: #ffffff;
        box-shadow: 0 0 0 4px rgba(255, 221, 0, 0.15);
        outline: none;
    }
    
    .stTextInput > label {
        color: #1a1a1a;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    /* Botão ENTRAR - Amarelo PRICETAX */
    .stButton > button {
        background: #FFDD00;
        color: #1a1a1a;
        border: none;
        border-radius: 30px;
        padding: 16px 32px;
        font-size: 17px;
        font-weight: 700;
        letter-spacing: 1px;
        width: 100%;
        margin-top: 25px;
        transition: all 0.3s ease;
        box-shadow: 0 6px 20px rgba(255, 221, 0, 0.4);
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(255, 221, 0, 0.5);
        background: #FACC15;
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Mensagens de erro */
    .stAlert {
        border-radius: 12px;
        border-left: 4px solid #ef4444;
        background: #fef2f2;
        padding: 14px 18px;
        margin-top: 20px;
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
        color: #999999;
        font-size: 12px;
        margin-top: 30px;
        padding-top: 25px;
        border-top: 1px solid #e0e0e0;
    }
    
    /* Animação de entrada */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .login-container {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .login-container {
            margin: 30px 20px;
            padding: 40px 30px;
        }
        
        .login-title {
            font-size: 32px;
        }
        
        .logo-container img {
            max-width: 280px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Container de login
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Logo "O X da Questão"
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    try:
        import base64
        with open("logo_x_questao.png", "rb") as img_file:
            logo_data = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{logo_data}" alt="O X da Questão">',
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        pass
    
    st.markdown('<div class="login-title"><span class="login-title-highlight">PRICE</span>TAX</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="login-subtitle">Soluções para transição inteligente na Reforma Tributária</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    
    # Exibir erro se credenciais inválidas
    if st.session_state.get("password_correct") == False:
        attempts = st.session_state.get("login_attempts", 0)
        st.error(f"Usuário ou senha incorretos. Tentativa {attempts}.")
    
    # Botão WhatsApp para solicitar acesso
    st.markdown(
        '''
        <a href="https://wa.me/5541998924080" target="_blank" class="whatsapp-button">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
            </svg>
            Solicitar Acesso
        </a>
        ''',
        unsafe_allow_html=True
    )
    
    # Rodapé
    st.markdown(
        '<div class="login-footer">Sistema protegido por autenticação SHA-256</div>',
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
        if st.button("🚪 Sair", key="logout_button", help=f"Desconectar ({authenticated_user})"):
            # Limpar session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
