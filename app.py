import streamlit as st
import base64
from pathlib import Path

st.set_page_config(
    page_title="PriceTax — Nova Plataforma",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def get_logo_base64():
    logo_path = Path(__file__).parent / "logo_pricetax.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="PriceTax" style="width:260px; margin-bottom:0.5rem;">' if logo_b64 else '<span style="font-size:2.5rem;font-weight:900;color:#fff;letter-spacing:-1px;">Price<span style="color:#F5C400;">Tax</span></span>'

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* Reset Streamlit padrão */
    .stApp {{
        background: #0A0A0A;
    }}

    #MainMenu, footer, header {{
        visibility: hidden;
    }}

    .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}

    /* ===== HERO SECTION ===== */
    .hero {{
        background: linear-gradient(160deg, #111111 0%, #0A0A0A 60%, #1a1400 100%);
        border-bottom: 1px solid #2a2a2a;
        padding: 3rem 2rem 2.5rem;
        text-align: center;
    }}

    .badge {{
        display: inline-block;
        background: rgba(245, 196, 0, 0.12);
        border: 1px solid rgba(245, 196, 0, 0.35);
        color: #F5C400;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        padding: 0.35rem 1rem;
        border-radius: 100px;
        margin-bottom: 1.8rem;
    }}

    .hero-title {{
        font-size: clamp(1.6rem, 4vw, 2.6rem);
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1.2;
        margin: 1.2rem 0 0.8rem;
        letter-spacing: -0.5px;
    }}

    .hero-title span {{
        color: #F5C400;
    }}

    .hero-subtitle {{
        font-size: 1.05rem;
        color: #9ca3af;
        font-weight: 400;
        max-width: 520px;
        margin: 0 auto 2rem;
        line-height: 1.6;
    }}

    /* ===== MAIN CTA BUTTON ===== */
    .cta-primary {{
        display: inline-block;
        background: linear-gradient(135deg, #F5C400 0%, #e6b800 100%);
        color: #0A0A0A !important;
        font-weight: 800;
        font-size: 1rem;
        letter-spacing: 0.3px;
        padding: 1rem 2.8rem;
        border-radius: 8px;
        text-decoration: none;
        transition: all 0.2s ease;
        box-shadow: 0 4px 24px rgba(245, 196, 0, 0.35);
        margin-bottom: 0.8rem;
    }}

    .cta-primary:hover {{
        box-shadow: 0 6px 32px rgba(245, 196, 0, 0.55);
        transform: translateY(-1px);
    }}

    .cta-hint {{
        font-size: 0.78rem;
        color: #6b7280;
        margin-top: 0.5rem;
    }}

    /* ===== CONTENT SECTION ===== */
    .content-section {{
        max-width: 720px;
        margin: 0 auto;
        padding: 2.5rem 2rem;
    }}

    /* ===== INFO CARD ===== */
    .info-card {{
        background: #111111;
        border: 1px solid #222222;
        border-radius: 12px;
        padding: 2rem 2.2rem;
        margin-bottom: 1.5rem;
    }}

    .info-card-title {{
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #F5C400;
        margin-bottom: 1.2rem;
    }}

    .info-row {{
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1.1rem;
    }}

    .info-row:last-child {{
        margin-bottom: 0;
    }}

    .info-icon {{
        width: 36px;
        height: 36px;
        min-width: 36px;
        background: rgba(245, 196, 0, 0.1);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }}

    .info-text {{
        flex: 1;
    }}

    .info-text strong {{
        display: block;
        color: #f3f4f6;
        font-size: 0.92rem;
        font-weight: 600;
        margin-bottom: 0.15rem;
    }}

    .info-text span {{
        color: #9ca3af;
        font-size: 0.85rem;
        line-height: 1.5;
    }}

    .info-text a {{
        color: #F5C400;
        text-decoration: none;
        font-weight: 600;
    }}

    /* ===== FEATURES GRID ===== */
    .features-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }}

    .feature-card {{
        background: #111111;
        border: 1px solid #1f1f1f;
        border-radius: 10px;
        padding: 1.2rem 1rem;
        text-align: center;
    }}

    .feature-icon {{
        font-size: 1.4rem;
        margin-bottom: 0.5rem;
    }}

    .feature-label {{
        font-size: 0.78rem;
        font-weight: 600;
        color: #e5e7eb;
        margin-bottom: 0.2rem;
    }}

    .feature-desc {{
        font-size: 0.72rem;
        color: #6b7280;
    }}

    /* ===== DIVIDER ===== */
    .section-divider {{
        border: none;
        border-top: 1px solid #1f1f1f;
        margin: 0.5rem 0 1.5rem;
    }}

    .section-label {{
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #4b5563;
        text-align: center;
        margin-bottom: 1rem;
    }}

    /* ===== WHATSAPP BUTTON ===== */
    .cta-whatsapp {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.7rem;
        background: #111111;
        border: 1px solid #25d366;
        color: #25d366 !important;
        font-weight: 700;
        font-size: 0.95rem;
        padding: 0.9rem 2rem;
        border-radius: 8px;
        text-decoration: none;
        transition: all 0.2s ease;
        max-width: 360px;
        margin: 0 auto;
    }}

    .cta-whatsapp:hover {{
        background: rgba(37, 211, 102, 0.08);
    }}

    /* ===== FOOTER ===== */
    .footer {{
        text-align: center;
        padding: 2rem;
        border-top: 1px solid #1a1a1a;
        margin-top: 1rem;
    }}

    .footer span {{
        font-size: 0.75rem;
        color: #374151;
    }}

    /* ===== RESPONSIVE ===== */
    @media (max-width: 600px) {{
        .features-grid {{
            grid-template-columns: repeat(3, 1fr);
            gap: 0.6rem;
        }}
        .hero {{
            padding: 2.5rem 1.2rem 2rem;
        }}
        .content-section {{
            padding: 2rem 1.2rem;
        }}
    }}
</style>

<!-- HERO -->
<div class="hero">
    {logo_html}
    <div class="badge">&#9679; Plataforma Atualizada</div>
    <h1 class="hero-title">
        Bem-vindo à nova era<br>da <span>gestão tributária</span>
    </h1>
    <p class="hero-subtitle">
        Nossa plataforma foi completamente renovada. Acesse agora a nova versão com mais velocidade, estabilidade e recursos avançados.
    </p>
    <div>
        <a href="https://xclass.pricetax.com.br/" target="_blank" class="cta-primary">
            Acessar Nova Plataforma &rarr;
        </a>
        <p class="cta-hint">xclass.pricetax.com.br &nbsp;|&nbsp; Acesso imediato</p>
    </div>
</div>

<!-- CONTENT -->
<div class="content-section">

    <!-- FEATURES -->
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">&#9889;</div>
            <div class="feature-label">Mais Rápida</div>
            <div class="feature-desc">Performance superior em todas as operações</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">&#9646;</div>
            <div class="feature-label">Mais Estável</div>
            <div class="feature-desc">Infraestrutura robusta e sem interrupções</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">&#10024;</div>
            <div class="feature-label">Melhorada</div>
            <div class="feature-desc">Novas funcionalidades e UX aprimorada</div>
        </div>
    </div>

    <!-- INFO CARD -->
    <div class="info-card">
        <div class="info-card-title">&#9679; &nbsp;Como acessar</div>

        <div class="info-row">
            <div class="info-icon">&#128279;</div>
            <div class="info-text">
                <strong>Novo endereço da plataforma</strong>
                <span><a href="https://xclass.pricetax.com.br/" target="_blank">https://xclass.pricetax.com.br/</a></span>
            </div>
        </div>

        <div class="info-row">
            <div class="info-icon">&#128274;</div>
            <div class="info-text">
                <strong>Suas credenciais continuam as mesmas</strong>
                <span>Utilize o mesmo login e senha da versão anterior. Nenhuma ação adicional é necessária.</span>
            </div>
        </div>

        <div class="info-row">
            <div class="info-icon">&#128202;</div>
            <div class="info-text">
                <strong>Dados preservados</strong>
                <span>Todo o seu histórico e configurações foram migrados automaticamente para a nova plataforma.</span>
            </div>
        </div>
    </div>

    <!-- DIVIDER -->
    <hr class="section-divider">
    <p class="section-label">Suporte &amp; Atendimento</p>

    <!-- WHATSAPP -->
    <a href="https://wa.me/5541998924080?text=Ol%C3%A1%20tenho%20interesse%20no%20TINTAX" target="_blank" class="cta-whatsapp">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="#25d366" xmlns="http://www.w3.org/2000/svg">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
        Falar com nossa equipe no WhatsApp
    </a>

</div>

<!-- FOOTER -->
<div class="footer">
    <span>&copy; 2026 PriceTax &mdash; Todos os direitos reservados</span>
</div>
""", unsafe_allow_html=True)
