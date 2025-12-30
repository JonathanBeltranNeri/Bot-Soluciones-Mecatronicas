import streamlit as st
import base64
import os

# --- PALETA SM AUTOMATIZACIÓN (Minimalista) ---
COLOR_NAVY = "#14213D"
COLOR_ORANGE = "#FCA311"
COLOR_BG = "#FAFBFC"
COLOR_CONTAINER_BG = "#FFFFFF"
COLOR_TEXT = "#1F2937"
COLOR_TEXT_MUTED = "#6B7280"
COLOR_BORDER = "#E5E7EB"
COLOR_BORDER_LIGHT = "#F3F4F6"

# --- MANEJO DE IMÁGENES ---
LOGO_PATH_LOCAL = "images/SM.png"

def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

LOGO_B64 = get_image_base64(LOGO_PATH_LOCAL)

# --- AVATARES DE CHAT ---
ICONO_BOT = LOGO_PATH_LOCAL
ICONO_USER = "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"

def cargar_estilos_premium():
    st.markdown(f"""
        <style>
        /* --- TIPOGRAFÍA MINIMALISTA --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        :root {{
            --navy: {COLOR_NAVY};
            --orange: {COLOR_ORANGE};
            --bg: {COLOR_BG};
            --text: {COLOR_TEXT};
            --text-muted: {COLOR_TEXT_MUTED};
            --border: {COLOR_BORDER};
            --border-light: {COLOR_BORDER_LIGHT};
        }}

        /* --- RESET Y BASE --- */
        .stApp {{
            background: linear-gradient(180deg, {COLOR_BG} 0%, #F1F3F5 100%);
        }}
        
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text);
            -webkit-font-smoothing: antialiased;
        }}

        /* Ocultar elementos de Streamlit */
        #MainMenu, footer, header {{ visibility: hidden; }}
        [data-testid="stSidebar"] {{ display: none; }}
        [data-testid="stToolbar"] {{ display: none; }}

        /* --- CONTENEDOR PRINCIPAL --- */
        .block-container {{
            background-color: {COLOR_CONTAINER_BG};
            max-width: 800px;
            padding: 2rem 2.5rem 3rem;
            border-radius: 24px;
            border: 1px solid var(--border);
            box-shadow: 
                0 1px 3px rgba(0,0,0,0.02),
                0 8px 24px rgba(0,0,0,0.04);
            margin: 24px auto 48px;
        }}

        /* --- AVATARES MINIMALISTAS --- */
        .stChatMessage [data-testid="stChatMessageAvatar"] {{
            width: 36px !important;
            height: 36px !important;
        }}
        
        .stChatMessage .stAvatar {{
            border-radius: 12px !important;
            border: none !important;
            background: var(--border-light) !important;
            padding: 0 !important;
            overflow: hidden;
        }}
        
        .stChatMessage .stAvatar img {{
            border-radius: 10px !important;
            padding: 6px !important;
        }}
        
        /* Bot Avatar - Acento sutil */
        [data-testid="chatAvatarIcon-assistant"] {{
            background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%) !important;
        }}
        
        /* User Avatar */
        [data-testid="chatAvatarIcon-user"] {{
            background: var(--border-light) !important;
        }}

        /* --- MENSAJES DE CHAT --- */
        .stChatMessage {{
            background: transparent !important;
            border: none !important;
            padding: 16px 0 !important;
            margin: 0 !important;
        }}
        
        .stChatMessage:not(:last-child) {{
            border-bottom: 1px solid var(--border-light) !important;
        }}
        
        /* Contenido del mensaje */
        .stChatMessage [data-testid="stMarkdownContainer"] {{
            line-height: 1.6;
        }}
        
        .stChatMessage [data-testid="stMarkdownContainer"] p {{
            margin: 0 0 0.5rem;
            font-size: 0.95rem;
        }}

        /* --- TARJETAS DE PRODUCTO (Minimalista) --- */
        .producto-card {{
            background: white;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin: 16px 0;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .producto-card:hover {{
            border-color: var(--navy);
            transform: translateY(-2px);
            box-shadow: 0 12px 24px -8px rgba(20, 33, 61, 0.12);
        }}
        
        .producto-img {{
            width: 100%;
            height: 140px;
            object-fit: contain;
            margin-bottom: 16px;
            border-radius: 8px;
            background: var(--border-light);
            padding: 12px;
        }}
        
        .card-title {{
            color: var(--navy);
            font-size: 1rem;
            font-weight: 600;
            margin: 0 0 8px;
            letter-spacing: -0.01em;
        }}
        
        .sku-text {{
            font-size: 0.75rem;
            color: var(--text-muted);
            background: var(--border-light);
            padding: 4px 10px;
            border-radius: 6px;
            display: inline-block;
            font-weight: 500;
        }}
        
        .price-text {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--navy);
            margin: 12px 0;
            letter-spacing: -0.02em;
        }}

        /* --- BOTONES MINIMALISTAS --- */
        .btn-link {{
            display: block;
            text-align: center;
            background: transparent;
            color: var(--navy) !important;
            border: 1.5px solid var(--border);
            padding: 12px 16px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }}
        
        .btn-link:hover {{
            background: var(--navy);
            color: white !important;
            border-color: var(--navy);
        }}
        
        .btn-primary {{
            background: var(--navy);
            color: white !important;
            border-color: var(--navy);
        }}
        
        .btn-primary:hover {{
            background: #0D1627;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(20, 33, 61, 0.25);
        }}

        /* --- INPUT DE CHAT --- */
        .stChatInput {{
            padding: 0 0 24px;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .stChatInput > div {{
            background: white !important;
            border-radius: 16px !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
            padding: 4px !important;
        }}
        
        .stChatInput textarea {{
            border: none !important;
            border-radius: 12px !important;
            padding: 14px 16px !important;
            font-size: 0.95rem !important;
            resize: none !important;
            background: transparent !important;
        }}
        
        .stChatInput textarea:focus {{
            box-shadow: none !important;
            outline: none !important;
        }}
        
        .stChatInput textarea::placeholder {{
            color: var(--text-muted) !important;
        }}
        
        /* Botón de enviar */
        .stChatInput button {{
            background: var(--navy) !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 10px 14px !important;
            margin: 4px !important;
            transition: all 0.2s ease !important;
        }}
        
        .stChatInput button:hover {{
            background: #0D1627 !important;
            transform: scale(1.02);
        }}
        
        .stChatInput button svg {{
            fill: white !important;
        }}

        /* --- SCROLLBAR MINIMALISTA --- */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 3px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}

        /* --- ANIMACIONES SUTILES --- */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .stChatMessage {{
            animation: fadeIn 0.3s ease-out;
        }}

        /* --- ESTADOS VACÍOS --- */
        .empty-state {{
            text-align: center;
            padding: 48px 24px;
            color: var(--text-muted);
        }}
        
        .empty-state-icon {{
            font-size: 3rem;
            margin-bottom: 16px;
            opacity: 0.5;
        }}
        
        .empty-state-text {{
            font-size: 0.95rem;
            line-height: 1.5;
        }}

        /* --- BADGES/TAGS --- */
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 0.75rem;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 6px;
            background: var(--border-light);
            color: var(--text-muted);
        }}
        
        .badge-success {{
            background: #ECFDF5;
            color: #059669;
        }}
        
        .badge-warning {{
            background: #FEF3C7;
            color: #D97706;
        }}

        </style>
    """, unsafe_allow_html=True)

def mostrar_header_limpio():
    """Header minimalista con logo centrado."""
    if LOGO_B64:
        st.markdown(f"""
            <div style="
                text-align: center;
                padding: 8px 0 24px;
            ">
                <img 
                    src="data:image/png;base64,{LOGO_B64}" 
                    style="
                        height: 64px;
                        margin-bottom: 12px;
                        opacity: 0.95;
                    "
                    alt="SM Automatización"
                >
                <div style="
                    height: 2px;
                    width: 32px;
                    background: {COLOR_ORANGE};
                    margin: 0 auto;
                    border-radius: 1px;
                "></div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="
                text-align: center;
                padding: 8px 0 24px;
            ">
                <h2 style="
                    color: {COLOR_NAVY};
                    font-weight: 700;
                    font-size: 1.5rem;
                    margin: 0 0 12px;
                    letter-spacing: -0.02em;
                ">SM Automatización</h2>
                <div style="
                    height: 2px;
                    width: 32px;
                    background: {COLOR_ORANGE};
                    margin: 0 auto;
                    border-radius: 1px;
                "></div>
            </div>
        """, unsafe_allow_html=True)

def mostrar_mensaje_bienvenida():
    """Mensaje de bienvenida minimalista."""
    st.markdown(f"""
        <div style="
            text-align: center;
            padding: 32px 16px;
            color: {COLOR_TEXT_MUTED};
        ">
            <div style="
                width: 48px;
                height: 48px;
                background: {COLOR_BORDER_LIGHT};
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 16px;
                font-size: 1.5rem;
            ">💬</div>
            <p style="
                font-size: 0.95rem;
                line-height: 1.6;
                margin: 0;
                max-width: 320px;
                margin: 0 auto;
            ">
                Hola, soy tu asistente de SM Automatización.<br>
                <span style="color: {COLOR_TEXT}; font-weight: 500;">¿En qué puedo ayudarte hoy?</span>
            </p>
        </div>
    """, unsafe_allow_html=True)

def crear_tarjeta_producto(imagen_url, titulo, sku, precio, link):
    """Genera HTML para una tarjeta de producto minimalista."""
    return f"""
        <div class="producto-card">
            <img src="{imagen_url}" class="producto-img" alt="{titulo}">
            <span class="sku-text">{sku}</span>
            <h3 class="card-title">{titulo}</h3>
            <p class="price-text">${precio:,.2f}</p>
            <a href="{link}" target="_blank" class="btn-link">Ver producto</a>
        </div>
    """

# --- EJEMPLO DE USO ---
if __name__ == "__main__":
    st.set_page_config(
        page_title="SM Automatización - Chat",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    cargar_estilos_premium()
    mostrar_header_limpio()
    
    # Inicializar historial de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Mostrar mensaje de bienvenida si no hay mensajes
    if not st.session_state.messages:
        mostrar_mensaje_bienvenida()
    
    # Mostrar mensajes existentes
    for message in st.session_state.messages:
        avatar = ICONO_BOT if message["role"] == "assistant" else ICONO_USER
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"], unsafe_allow_html=True)
    
    # Input del chat
    if prompt := st.chat_input("Escribe tu mensaje..."):
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=ICONO_USER):
            st.markdown(prompt)
        
        # Respuesta del bot (ejemplo)
        with st.chat_message("assistant", avatar=ICONO_BOT):
            response = f"Recibí tu mensaje: **{prompt}**"
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
