import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path

st.set_page_config(
    page_title="PriceTax — Nova Plataforma",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Remove padding e barra lateral do Streamlit
st.markdown("""
<style>
    #MainMenu, footer, header, [data-testid="stToolbar"] { visibility: hidden !important; }
    .stApp { background: #0A0A0A !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    section[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# Carrega logo em base64
logo_path = Path(__file__).parent / "logo_pricetax.png"
logo_tag = ""
if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_tag = f'<img src="data:image/png;base64,{logo_b64}" alt="PriceTax" style="width:220px;margin-bottom:8px;">'
else:
    logo_tag = '<div style="font-size:2rem;font-weight:900;color:#fff;letter-spacing:-1px;">Price<span style="color:#F5C400;">Tax</span></div>'

# Página completa renderizada via componente HTML isolado
html_page = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', sans-serif;
    background: #0A0A0A;
    color: #f3f4f6;
    min-height: 100vh;
  }}

  /* ── HERO ── */
  .hero {{
    background: linear-gradient(160deg, #111111 0%, #0A0A0A 55%, #1a1400 100%);
    border-bottom: 1px solid #2a2a2a;
    padding: 48px 24px 40px;
    text-align: center;
  }}

  .badge {{
    display: inline-block;
    background: rgba(245,196,0,.12);
    border: 1px solid rgba(245,196,0,.4);
    color: #F5C400;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding: 5px 14px;
    border-radius: 100px;
    margin: 16px 0 20px;
  }}

  .hero h1 {{
    font-size: clamp(22px, 4vw, 36px);
    font-weight: 800;
    color: #ffffff;
    line-height: 1.2;
    margin-bottom: 14px;
    letter-spacing: -0.5px;
  }}

  .hero h1 span {{ color: #F5C400; }}

  .hero p {{
    font-size: 16px;
    color: #9ca3af;
    max-width: 480px;
    margin: 0 auto 28px;
    line-height: 1.65;
  }}

  .btn-primary {{
    display: inline-block;
    background: linear-gradient(135deg, #F5C400, #e6b800);
    color: #0A0A0A;
    font-weight: 800;
    font-size: 15px;
    padding: 14px 40px;
    border-radius: 8px;
    text-decoration: none;
    box-shadow: 0 4px 24px rgba(245,196,0,.4);
    transition: box-shadow .2s, transform .2s;
  }}

  .btn-primary:hover {{
    box-shadow: 0 6px 32px rgba(245,196,0,.6);
    transform: translateY(-1px);
  }}

  .cta-hint {{
    font-size: 12px;
    color: #6b7280;
    margin-top: 10px;
  }}

  /* ── CONTENT ── */
  .content {{
    max-width: 720px;
    margin: 0 auto;
    padding: 32px 20px 0;
  }}

  /* ── FEATURES ── */
  .features {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }}

  .feat {{
    background: #111;
    border: 1px solid #1f1f1f;
    border-radius: 10px;
    padding: 18px 12px;
    text-align: center;
  }}

  .feat-icon {{
    font-size: 22px;
    margin-bottom: 8px;
  }}

  .feat-title {{
    font-size: 13px;
    font-weight: 700;
    color: #e5e7eb;
    margin-bottom: 4px;
  }}

  .feat-desc {{
    font-size: 11px;
    color: #6b7280;
    line-height: 1.4;
  }}

  /* ── INFO CARD ── */
  .card {{
    background: #111;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 28px 28px;
    margin-bottom: 20px;
  }}

  .card-label {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #F5C400;
    margin-bottom: 20px;
  }}

  .row {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 18px;
  }}

  .row:last-child {{ margin-bottom: 0; }}

  .row-icon {{
    width: 38px;
    height: 38px;
    min-width: 38px;
    background: rgba(245,196,0,.1);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }}

  .row-body strong {{
    display: block;
    font-size: 14px;
    font-weight: 600;
    color: #f3f4f6;
    margin-bottom: 3px;
  }}

  .row-body span {{
    font-size: 13px;
    color: #9ca3af;
    line-height: 1.55;
  }}

  .row-body a {{
    color: #F5C400;
    text-decoration: none;
    font-weight: 600;
  }}

  /* ── DIVIDER ── */
  hr {{
    border: none;
    border-top: 1px solid #1f1f1f;
    margin: 8px 0 18px;
  }}

  .section-label {{
    text-align: center;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4b5563;
    margin-bottom: 14px;
  }}

  /* ── WHATSAPP ── */
  .btn-whatsapp {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: #111;
    border: 1px solid #25d366;
    color: #25d366;
    font-weight: 700;
    font-size: 14px;
    padding: 14px 28px;
    border-radius: 8px;
    text-decoration: none;
    max-width: 380px;
    margin: 0 auto;
    transition: background .2s;
  }}

  .btn-whatsapp:hover {{ background: rgba(37,211,102,.08); }}

  /* ── FOOTER ── */
  .footer {{
    text-align: center;
    padding: 28px 16px;
    border-top: 1px solid #1a1a1a;
    margin-top: 24px;
    font-size: 12px;
    color: #374151;
  }}
</style>
</head>
<body>

<!-- HERO -->
<div class="hero">
  {logo_tag}
  <div class="badge">&#9679; Plataforma Atualizada</div>
  <h1>Bem-vindo à nova era<br>da <span>gestão tributária</span></h1>
  <p>Nossa plataforma foi completamente renovada. Acesse agora a nova versão com mais velocidade, estabilidade e recursos avançados.</p>
  <a href="https://xclass.pricetax.com.br/" target="_blank" class="btn-primary">Acessar Nova Plataforma &rarr;</a>
  <p class="cta-hint">xclass.pricetax.com.br &nbsp;|&nbsp; Acesso imediato</p>
</div>

<!-- CONTENT -->
<div class="content">

  <!-- FEATURES -->
  <div class="features">
    <div class="feat">
      <div class="feat-icon">&#9889;</div>
      <div class="feat-title">Mais Rápida</div>
      <div class="feat-desc">Performance superior em todas as operações</div>
    </div>
    <div class="feat">
      <div class="feat-icon">&#9646;</div>
      <div class="feat-title">Mais Estável</div>
      <div class="feat-desc">Infraestrutura robusta e sem interrupções</div>
    </div>
    <div class="feat">
      <div class="feat-icon">&#10024;</div>
      <div class="feat-title">Melhorada</div>
      <div class="feat-desc">Novas funcionalidades e UX aprimorada</div>
    </div>
  </div>

  <!-- INFO CARD -->
  <div class="card">
    <div class="card-label">&#9679;&nbsp; Como acessar</div>

    <div class="row">
      <div class="row-icon">&#128279;</div>
      <div class="row-body">
        <strong>Novo endereço da plataforma</strong>
        <span><a href="https://xclass.pricetax.com.br/" target="_blank">https://xclass.pricetax.com.br/</a></span>
      </div>
    </div>

    <div class="row">
      <div class="row-icon">&#128274;</div>
      <div class="row-body">
        <strong>Suas credenciais continuam as mesmas</strong>
        <span>Utilize o mesmo login e senha da versão anterior. Nenhuma ação adicional é necessária.</span>
      </div>
    </div>

    <div class="row">
      <div class="row-icon">&#128202;</div>
      <div class="row-body">
        <strong>Dados preservados</strong>
        <span>Todo o seu histórico e configurações foram migrados automaticamente para a nova plataforma.</span>
      </div>
    </div>
  </div>

  <!-- WHATSAPP -->
  <hr>
  <p class="section-label">Suporte &amp; Atendimento</p>
  <a href="https://wa.me/5541998924080?text=Ol%C3%A1%20tenho%20interesse%20no%20TINTAX" target="_blank" class="btn-whatsapp">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="#25d366" xmlns="http://www.w3.org/2000/svg">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
    </svg>
    Falar com nossa equipe no WhatsApp
  </a>

  <!-- FOOTER -->
  <div class="footer">&copy; 2026 PriceTax &mdash; Todos os direitos reservados</div>

</div>
</body>
</html>
"""

components.html(html_page, height=1100, scrolling=False)
