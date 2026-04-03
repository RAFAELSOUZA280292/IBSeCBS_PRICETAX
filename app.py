import streamlit as st

st.set_page_config(
    page_title="Portal Atualizado - PriceTax",
    page_icon="🔄",
    layout="centered"
)

st.markdown(
    """
    <style>
        .main-container {
            max-width: 700px;
            margin: 0 auto;
            padding: 2rem;
            text-align: center;
        }
        .title {
            font-size: 2rem;
            font-weight: bold;
            color: #1a1a2e;
            margin-bottom: 1.5rem;
        }
        .message-box {
            background-color: #f0f4ff;
            border-left: 5px solid #2563eb;
            border-radius: 8px;
            padding: 2rem;
            margin: 1.5rem 0;
            text-align: left;
            font-size: 1.1rem;
            line-height: 1.8;
            color: #1e293b;
        }
        .link-btn {
            display: inline-block;
            background-color: #2563eb;
            color: white !important;
            padding: 0.75rem 2rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1rem;
            margin: 1rem 0;
        }
        .link-btn:hover {
            background-color: #1d4ed8;
        }
        .whatsapp-btn {
            display: inline-block;
            background-color: #25d366;
            color: white !important;
            padding: 0.75rem 2rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1rem;
            margin: 1rem 0;
        }
        .whatsapp-btn:hover {
            background-color: #1ebe5d;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("## 🔄 Nosso portal foi atualizado")

st.markdown(
    """
    <div class="message-box">
        <p>Olá, nosso portal foi atualizado.</p>
        <p>Acesse agora a nova versão em:<br>
        <a href="https://xclass.pricetax.com.br/" target="_blank"><strong>https://xclass.pricetax.com.br/</strong></a></p>
        <p>Utilize o mesmo login e senha da versão anterior.</p>
        <p>A nova plataforma está mais rápida, estável e com melhorias significativas de performance.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align: center; margin: 1.5rem 0;">
        <a href="https://xclass.pricetax.com.br/" target="_blank" class="link-btn">
            🚀 Acessar nova plataforma
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

st.markdown("### 💬 Em caso de dúvidas, fale conosco:")

st.markdown(
    """
    <div style="text-align: center; margin: 1rem 0;">
        <a href="https://wa.me/5541998924080?text=Ol%C3%A1%20tenho%20interesse%20no%20TINTAX" target="_blank" class="whatsapp-btn">
            📲 Falar pelo WhatsApp
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
