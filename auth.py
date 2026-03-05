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
    try:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "auth_log.txt")
        brasilia_tz = timezone(timedelta(hours=-3))
        timestamp = datetime.now(brasilia_tz).strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCESSO" if success else "FALHA"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {status} - Usuário: {username}\n")
    except Exception as e:
        print(f"Erro ao registrar log: {e}")


def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def check_password() -> bool:

    def password_entered():
        username = st.session_state.get("username", "").strip()
        password = st.session_state.get("password", "")

        if "passwords" not in st.secrets:
            st.error("Erro de configuração: credenciais não encontradas.")
            return

        if username in st.secrets["passwords"]:
            password_hash = get_password_hash(password)
            if password_hash == st.secrets["passwords"][username]:
                pode_acessar, mensagem_erro = verificar_acesso_usuario(username)
                if not pode_acessar:
                    st.session_state["password_correct"] = False
                    st.session_state["access_denied_message"] = mensagem_erro
                    log_login(username, success=False)
                    return
                st.session_state["password_correct"] = True
                st.session_state["authenticated_user"] = username
                st.session_state["login_attempts"] = 0
                st.session_state["access_denied_message"] = None
                log_login(username, success=True)
                st.rerun()
                return

        st.session_state["password_correct"] = False
        st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
        log_login(username if username else "[vazio]", success=False)
        st.session_state["access_denied_message"] = None

    if st.session_state.get("password_correct", False):
        return True

    # ------------------------------------------------------------------
    # Logo em base64
    # ------------------------------------------------------------------
    import base64 as _b64

    logo_html = '<span style="color:#FFDD00;font-size:1.6rem;font-weight:800;letter-spacing:3px;font-family:Poppins,sans-serif;">PRICETAX</span>'
    try:
        with open("logo_x_questao.png", "rb") as _f:
            _logo_data = _b64.b64encode(_f.read()).decode()
        logo_html = (
            '<img src="data:image/png;base64,' + _logo_data + '" '
            'alt="PRICETAX" style="max-width:180px;height:auto;'
            'filter:drop-shadow(0 4px 16px rgba(255,221,0,0.4));">'
        )
    except FileNotFoundError:
        pass

    # Faixa de logos parceiros em base64
    parceiros_html = ''
    try:
        with open("logos_parceiros.png", "rb") as _f:
            _parceiros_data = _b64.b64encode(_f.read()).decode()
        parceiros_html = (
            '<div class="partners-bar">'
            '<img src="data:image/png;base64,' + _parceiros_data + '" '
            'alt="Parceiros PRICETAX" style="max-width:100%;height:auto;">'
            '</div>'
        )
    except FileNotFoundError:
        pass

    # ------------------------------------------------------------------
    # Mensagem de erro (se houver)
    # ------------------------------------------------------------------
    error_html = ""
    if st.session_state.get("password_correct") is False:
        access_denied_msg = st.session_state.get("access_denied_message")
        if access_denied_msg:
            error_html = (
                '<div style="background:rgba(239,68,68,0.12);border-left:3px solid #EF4444;'
                'border-radius:6px;padding:0.75rem 1rem;color:#EF4444;font-size:0.8rem;'
                'font-family:Poppins,sans-serif;margin-bottom:0.75rem;">'
                + access_denied_msg + "</div>"
            )
        else:
            attempts = st.session_state.get("login_attempts", 0)
            error_html = (
                '<div style="background:rgba(239,68,68,0.12);border-left:3px solid #EF4444;'
                'border-radius:6px;padding:0.75rem 1rem;color:#EF4444;font-size:0.8rem;'
                'font-family:Poppins,sans-serif;margin-bottom:0.75rem;">'
                "Usuário ou senha incorretos. Tentativa " + str(attempts) + ".</div>"
            )

    # ------------------------------------------------------------------
    # 1) CSS — string normal (sem f-string, sem interpolação)
    # ------------------------------------------------------------------
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

header, footer, #MainMenu, .stDeployButton,
section[data-testid="stSidebar"] { display: none !important; }

html, body, .stApp { background: #000 !important; margin: 0 !important; padding: 0 !important; }

.block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }

.login-overlay {
    position: fixed; top: 0; left: 0;
    width: 100vw; height: 100vh;
    display: flex; z-index: 999;
    font-family: 'Poppins', sans-serif; overflow: hidden;
}

.login-left {
    flex: 1.1;
    background: linear-gradient(145deg, #111111 0%, #0A0A0A 60%, #1A1200 100%);
    padding: 2rem 2rem 2rem 2.5rem;
    display: flex; flex-direction: column; justify-content: center;
    border-right: 1px solid rgba(255,221,0,0.08);
    overflow-y: auto; box-sizing: border-box; position: relative;
}
.login-left::before {
    content: ''; position: absolute; top: -150px; right: -150px;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(255,221,0,0.07) 0%, transparent 70%);
    pointer-events: none;
}

.login-right {
    flex: 0.9; background: #0D0D0D;
    padding: 2rem 2.5rem 2rem 2rem;
    display: flex; flex-direction: column; justify-content: center;
    overflow-y: auto; box-sizing: border-box;
}

.logo-wrap { margin-bottom: 1.25rem; }

.login-headline { font-size: 1.9rem; font-weight: 800; line-height: 1.2; color: #fff; margin-bottom: 0.5rem; }
.login-headline span { color: #FFDD00; }

.login-subtitle { color: #AAAAAA; font-size: 0.85rem; line-height: 1.6; margin-bottom: 1.25rem; max-width: 400px; }

.feature-list { display: flex; flex-direction: column; gap: 0.45rem; margin-bottom: 1.25rem; }
.feature-item {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.55rem 0.9rem;
    background: rgba(255,221,0,0.04); border: 1px solid rgba(255,221,0,0.1); border-radius: 8px;
}
.feature-icon {
    width: 34px; height: 34px; min-width: 34px;
    background: rgba(255,221,0,0.1); border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid rgba(255,221,0,0.2);
}
.feature-icon svg { width: 16px; height: 16px; }
.feature-text { color: #DDDDDD; font-size: 0.82rem; font-weight: 500; line-height: 1.3; }

.social-proof { display: flex; gap: 1.25rem; flex-wrap: wrap; align-items: center; }
.proof-item { display: flex; flex-direction: column; }
.proof-number { color: #FFDD00; font-size: 1.3rem; font-weight: 700; line-height: 1; }
.proof-label { color: #666; font-size: 0.7rem; margin-top: 2px; }
.proof-divider { width: 1px; height: 32px; background: rgba(255,255,255,0.1); }

.form-title { color: #fff; font-size: 1.6rem; font-weight: 700; margin-bottom: 0.3rem; }
.form-subtitle { color: #666; font-size: 0.8rem; margin-bottom: 1.25rem; }

.stTextInput > div > div > input {
    border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important;
    padding: 0.75rem 1rem !important; font-size: 0.9rem !important;
    background: #1E1E1E !important; color: #FFFFFF !important;
    font-family: 'Poppins', sans-serif !important; transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #FFDD00 !important; box-shadow: 0 0 0 2px rgba(255,221,0,0.15) !important; outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #555 !important; }
.stTextInput > label { color: #999 !important; font-size: 0.8rem !important; font-weight: 500 !important; font-family: 'Poppins', sans-serif !important; }

.stButton > button {
    background: #FFDD00 !important; color: #000 !important; border: none !important;
    border-radius: 24px !important; padding: 0.75rem 2rem !important;
    font-size: 0.95rem !important; font-weight: 700 !important; width: 100% !important;
    margin-top: 1rem !important; text-transform: uppercase !important; letter-spacing: 0.5px !important;
    font-family: 'Poppins', sans-serif !important; box-shadow: 0 6px 20px rgba(255,221,0,0.35) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: #E6C700 !important; box-shadow: 0 8px 28px rgba(255,221,0,0.5) !important; transform: translateY(-1px) !important;
}

.wa-btn {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    background: #25D366; color: #fff; border-radius: 24px;
    padding: 0.7rem 1.5rem; font-size: 0.85rem; font-weight: 600;
    text-decoration: none; width: 100%; margin-top: 0.75rem;
    box-sizing: border-box; font-family: 'Poppins', sans-serif;
    box-shadow: 0 4px 14px rgba(37,211,102,0.3); transition: all 0.2s ease;
}
.wa-btn:hover { background: #20BA5A; text-decoration: none; color: #fff; transform: translateY(-1px); }
.wa-btn svg { fill: #fff; }

.login-footer {
    color: #444; font-size: 0.7rem; text-align: center;
    margin-top: 1.25rem; padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.07); font-family: 'Poppins', sans-serif;
}

/* Faixa de parceiros */
.partners-bar {
    position: fixed;
    bottom: 0; left: 0;
    width: 100vw;
    background: #3A3F4B;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    z-index: 1001;
    line-height: 0;
}
.partners-bar img {
    width: 100%;
    height: auto;
    display: block;
    max-height: 80px;
    object-fit: cover;
}

/* ===== WIDGETS STREAMLIT ACIMA DO OVERLAY =====
   O overlay tem z-index 999. Os widgets precisam de z-index > 999
   e position relative/absolute para ficarem visiveis. */

/* Container geral do Streamlit - acima do overlay */
div[data-testid="stVerticalBlock"],
div[data-testid="column"],
.element-container,
.stTextInput,
.stButton,
.stMarkdown {
    position: relative !important;
    z-index: 1000 !important;
}

/* Coluna da direita (col_form) precisa ter background para cobrir o overlay */
div[data-testid="column"]:last-child {
    background: #0D0D0D !important;
    padding: 2rem 2.5rem !important;
    min-height: 100vh !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}

/* Coluna da esquerda (spacer) - transparente */
div[data-testid="column"]:first-child {
    background: transparent !important;
    pointer-events: none !important;
}
</style>
""", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # 2) HTML do overlay — construído por concatenação de strings Python
    #    (sem triple-quote com chaves que conflitem com CSS)
    # ------------------------------------------------------------------
    overlay_html = (
        '<div class="login-overlay">'

        # Coluna esquerda
        '<div class="login-left">'
        '<div class="logo-wrap">' + logo_html + '</div>'
        '<div class="login-headline">Inteligência Tributária<br>para a <span>Reforma</span></div>'
        '<div class="login-subtitle">Soluções para a transição inteligente na Reforma Tributária.<br>'
        'Parametrize, analise e decida com precisão.</div>'

        '<div class="feature-list">'

        '<div class="feature-item"><div class="feature-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="#FFDD00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg></div>'
        '<span class="feature-text">Milhares de NCMs com CST de IBS e CBS mapeados</span></div>'

        '<div class="feature-item"><div class="feature-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="#FFDD00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg></div>'
        '<span class="feature-text">Regimes especiais, monofásico e reduções de alíquota</span></div>'

        '<div class="feature-item"><div class="feature-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="#FFDD00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg></div>'
        '<span class="feature-text">Operações internas, interestaduais e exportação</span></div>'

        '<div class="feature-item"><div class="feature-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="#FFDD00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg></div>'
        '<span class="feature-text">Base legal LC 214/2025 — Cesta Básica, isenções e benefícios</span></div>'

        '<div class="feature-item"><div class="feature-icon">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="#FFDD00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></div>'
        '<span class="feature-text">Análise de EFD SPED com ranking de impacto tributário</span></div>'

        '</div>'  # feature-list

        '<div class="social-proof">'
        '<div class="proof-item"><span class="proof-number">+5.000</span><span class="proof-label">Empresas atendidas</span></div>'
        '<div class="proof-divider"></div>'
        '<div class="proof-item"><span class="proof-number">+600</span><span class="proof-label">CFOPs mapeados</span></div>'
        '<div class="proof-divider"></div>'
        '<div class="proof-item"><span class="proof-number">LC 214</span><span class="proof-label">Reforma 2026</span></div>'
        '</div>'  # social-proof

        '</div>'  # login-left

        # Coluna direita — apenas título e erro; inputs vêm do Streamlit
        '<div class="login-right">'
        '<div class="form-title">Acessar plataforma</div>'
        '<div class="form-subtitle">Insira suas credenciais para continuar</div>'
        + error_html +
        '</div>'  # login-right

        # Faixa de parceiros — rodapé fixo abaixo das duas colunas
        + parceiros_html +

        '</div>'  # login-overlay
    )

    st.markdown(overlay_html, unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # Inputs e botão do Streamlit — coluna direita via st.columns
    # ------------------------------------------------------------------
    col_spacer, col_form = st.columns([1.1, 0.9])

    with col_form:
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

        if st.button("Entrar", type="primary", use_container_width=True):
            password_entered()

        st.markdown(
            '<a href="https://wa.me/5541998924080" target="_blank" class="wa-btn">'
            '<svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15'
            '-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475'
            '-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52'
            '.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207'
            '-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372'
            '-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 '
            '5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 '
            '1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347'
            'm-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648'
            '-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 '
            '5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884'
            'm8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 '
            '4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 '
            '11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>'
            '</svg>Solicitar Acesso</a>'
            '<div class="login-footer">Autenticação segura com criptografia de padrão internacional e conformidade com LGPD</div>',
            unsafe_allow_html=True
        )

    return False


def show_logout_button():
    """Exibe botão de logout no canto superior direito."""
    authenticated_user = st.session_state.get("authenticated_user", "Usuário")

    st.markdown("""
<style>
.logout-container {
    position: fixed; top: 20px; right: 20px; z-index: 9999;
    display: flex; align-items: center; gap: 12px;
    background: #ffffff; padding: 10px 20px; border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid rgba(0,0,0,0.05);
}
.logout-user { color: #334155; font-size: 14px; font-weight: 600; }
.logout-btn {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: #fff; border: none; border-radius: 8px; padding: 8px 18px;
    font-size: 14px; font-weight: 600; cursor: pointer;
    transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(239,68,68,0.25);
}
.logout-btn:hover { transform: translateY(-2px); background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); }
</style>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Sair", key="logout_button", help=f"Desconectar ({authenticated_user})"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
