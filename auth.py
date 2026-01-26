"""
Módulo de Autenticação para PRICETAX
Implementa login seguro com hash SHA-256
"""

import streamlit as st
import hashlib


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
    Verifica credenciais de login e gerencia session state.
    
    Returns:
        True se autenticado, False caso contrário
    """
    
    def password_entered():
        """Callback executado quando o usuário submete o formulário de login."""
        username = st.session_state.get("username", "")
        password = st.session_state.get("password", "")
        
        # Verificar se as credenciais estão configuradas
        if "passwords" not in st.secrets:
            st.error("Erro de configuração: credenciais não encontradas.")
            st.session_state["password_correct"] = False
            return
        
        # Verificar usuário e senha
        if username in st.secrets["passwords"]:
            password_hash = get_password_hash(password)
            if password_hash == st.secrets["passwords"][username]:
                st.session_state["password_correct"] = True
                st.session_state["authenticated_user"] = username
                # Limpar senha da memória
                if "password" in st.session_state:
                    del st.session_state["password"]
                return
        
        # Credenciais inválidas
        st.session_state["password_correct"] = False
        st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
    
    # Verificar se já está autenticado
    if st.session_state.get("password_correct", False):
        return True
    
    # Exibir tela de login
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .login-title {
        text-align: center;
        color: #1f2937;
        font-size: 28px;
        font-weight: 600;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Logo "O X da Questão"
    try:
        import base64
        with open("logo_x_questao.png", "rb") as img_file:
            logo_data = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f'<div style="text-align: center; margin-bottom: 20px;"><img src="data:image/png;base64,{logo_data}" style="max-width: 300px; height: auto;" alt="O X da Questão"></div>',
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        pass  # Se o logo não existir, continua sem ele
    
    st.markdown('<div class="login-title">PRICETAX</div>', unsafe_allow_html=True)
    st.markdown("### Autenticação Necessária")
    
    # Formulário de login
    st.text_input("Usuário", key="username", placeholder="Digite seu usuário")
    st.text_input("Senha", type="password", key="password", placeholder="Digite sua senha")
    
    # Botão de login
    if st.button("Entrar", type="primary", use_container_width=True):
        password_entered()
    
    # Exibir erro se credenciais inválidas
    if st.session_state.get("password_correct") == False:
        attempts = st.session_state.get("login_attempts", 0)
        st.error(f"Usuário ou senha incorretos. Tentativa {attempts}.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return False


def logout():
    """Realiza logout do usuário, limpando o session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def show_logout_button():
    """Exibe botão de logout no sidebar."""
    with st.sidebar:
        st.markdown("---")
        if "authenticated_user" in st.session_state:
            st.caption(f"Usuário: **{st.session_state['authenticated_user']}**")
        if st.button("Sair", type="secondary", use_container_width=True):
            logout()
