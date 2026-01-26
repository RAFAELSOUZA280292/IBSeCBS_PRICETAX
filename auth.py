"""
Módulo de autenticação para o sistema PRICETAX.

Implementa autenticação segura com hash SHA-256 e interface elegante.
"""

import hashlib
import streamlit as st


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
                return
        
        # Credenciais inválidas
        st.session_state["password_correct"] = False
        st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
    
    # Verificar se já está autenticado
    if st.session_state.get("password_correct", False):
        return True
    
    # CSS Premium para tela de login
    st.markdown("""
    <style>
    /* Ocultar elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Eliminar completamente skeleton/placeholder do Streamlit */
    .element-container:empty {
        display: none !important;
    }
    
    .stMarkdown:empty {
        display: none !important;
    }
    
    div[data-testid="stVerticalBlock"] > div:empty {
        display: none !important;
    }
    
    div[data-testid="stVerticalBlock"] > div[style*="height"] {
        height: 0 !important;
        min-height: 0 !important;
    }
    
    /* Forçar remoção de espaçamentos superiores */
    .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Background com gradiente sutil */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
    }
    
    /* Container de login elegante */
    .login-container {
        max-width: 480px;
        margin: 80px auto;
        padding: 50px 45px;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    /* Logo container */
    .logo-container {
        text-align: center;
        margin-bottom: 35px;
    }
    
    .logo-container img {
        max-width: 400px;
        height: auto;
        margin-bottom: 25px;
        filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.1));
    }
    
    /* Título PRICETAX */
    .login-title {
        text-align: center;
        color: #1a202c;
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 12px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Subtítulo */
    .login-subtitle {
        text-align: center;
        color: #64748b;
        font-size: 15px;
        font-weight: 400;
        margin-bottom: 40px;
        line-height: 1.6;
    }
    
    /* Estilo dos inputs */
    .stTextInput > div > div > input {
        border: 1.5px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        font-size: 15px;
        transition: all 0.3s ease;
        background: #f8fafc;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #f59e0b;
        background: #ffffff;
        box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
    }
    
    /* Labels dos inputs */
    .stTextInput > label {
        color: #334155;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    /* Botão de login elegante */
    .stButton > button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 16px 32px;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.5px;
        width: 100%;
        margin-top: 25px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(245, 158, 11, 0.35);
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Mensagens de erro elegantes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #ef4444;
        background: #fef2f2;
        padding: 14px 18px;
        margin-top: 20px;
    }
    
    /* Rodapé sutil */
    .login-footer {
        text-align: center;
        color: #94a3b8;
        font-size: 13px;
        margin-top: 30px;
        padding-top: 25px;
        border-top: 1px solid #e2e8f0;
    }
    
    /* Animação suave de entrada */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .login-container {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Botão WhatsApp elegante */
    .whatsapp-button {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        background: #25D366;
        color: #ffffff;
        border: none;
        border-radius: 10px;
        padding: 14px 24px;
        font-size: 15px;
        font-weight: 600;
        text-decoration: none;
        width: 100%;
        margin-top: 15px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(37, 211, 102, 0.25);
        cursor: pointer;
    }
    
    .whatsapp-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.35);
        background: #20BA5A;
    }
    
    .whatsapp-button svg {
        width: 20px;
        height: 20px;
        fill: #ffffff;
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
    
    st.markdown('<div class="login-title">PRICETAX</div>', unsafe_allow_html=True)
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
    """Exibe botão de logout no sidebar."""
    with st.sidebar:
        st.markdown("---")
        authenticated_user = st.session_state.get("authenticated_user", "Usuário")
        st.markdown(f"**Conectado como:** {authenticated_user}")
        
        if st.button("Sair", type="secondary", use_container_width=True):
            # Limpar session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
