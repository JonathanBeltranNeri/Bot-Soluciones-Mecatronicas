import streamlit as st
import os
import json
import unicodedata
import re
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# --- IMPORTAMOS EL DISEÑO SM ---
import style

# 1. CONFIGURACIÓN
st.set_page_config(page_title="SM Automatización", page_icon="⚙️", layout="wide")
load_dotenv()

# INYECTAR CSS PREMIUM
style.cargar_estilos_premium()

# 2. CONEXIONES
@st.cache_resource
def init_connections():
    try:
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return supabase, groq, model
    except Exception as e:
        st.error(f"❌ Error conexión: {e}")
        return None, None, None

client_db, client_ia, model_embedding = init_connections()

# 3. LÓGICA (CEREBRO)

def analizar_filtro_precio(texto):
    """
    Analiza si el usuario quiere filtrar por precio.
    Retorna:
    - 'barato': Ordenar asc
    - 'caro': Ordenar desc
    - ('especifico', 4000): Buscar precio cercano a 4000
    - None: Búsqueda normal
    """
    texto = texto.lower()
    
    # 1. Detección de número específico (ej: "de 4000 pesos", "unos 500")
    # Buscamos números mayores a 50 (para evitar confundir con modelos o cantidades pequeñas)
    numeros = re.findall(r'\d+', texto.replace(',', '').replace('$', ''))
    numeros = [int(n) for n in numeros if int(n) > 50]
    
    if numeros:
        return ('especifico', numeros[0]) # Retorna el primer precio grande que encuentre

    # 2. Detección de Barato/Caro
    if any(x in texto for x in ["barato", "económico", "economico", "menor precio", "menos cuesta", "bajo costo"]):
        return "barato"
    if any(x in texto for x in ["caro", "costoso", "mayor precio", "mejor calidad", "premium", "top"]):
        return "caro"
    
    return None

def buscar_productos_vectorial(query_usuario, n_resultados=3):
    """
    Convierte texto a vector y pide a Supabase.
    n_resultados es dinámico: Pedimos más si vamos a filtrar por precio.
    """
    try:
        vector = model_embedding.encode(query_usuario).tolist()
        response = client_db.rpc(
            'buscar_productos', 
            {
                'query_embedding': vector,
                'match_threshold': 0.25, 
                'match_count': n_resultados 
            }
        ).execute()
        return response.data
    except Exception as e:
        st.error(f"Error en búsqueda: {e}")
        return []

def contextualizar_consulta(query_actual, historial_mensajes):
    if len(query_actual.split()) > 12: return query_actual
    ultimo_msg_usuario = ""
    for msg in reversed(historial_mensajes):
        if msg["role"] == "user" and msg["content"] != query_actual:
            ultimo_msg_usuario = msg["content"]; break
    if not ultimo_msg_usuario: return query_actual

    prompt_rewrite = f"""
    Contexto: "{ultimo_msg_usuario}". Usuario: "{query_actual}".
    TU MISIÓN: Generar la frase de búsqueda TÉCNICA ideal para una base de datos vectorial.
    
    REGLAS DE RAZONAMIENTO:
    1. DETECTAR CAMBIO: Si el usuario dice "también", "ahora", "y un", "además" o pide un producto totalmente distinto (ej: pasas de Sensor a Cable), OLVIDA el contexto anterior. Busca solo lo nuevo.
    2. DETECTAR REFINAMIENTO: Si el usuario sigue hablando de lo mismo (ej: "¿y pnp?", "¿de 24v?", "¿el más barato?"), COMBINA con el contexto anterior.
    3. LIMPIEZA: ELIMINA palabras de venta como "barato", "caro", "precio", "costo", "económico", "mejor". Deja solo el nombre técnico del producto.
    
    EJEMPLOS:
    - Contexto="Busco PLC", Usuario="cual es el mas barato" -> Salida="PLC" (Refinamiento + Limpieza)
    - Contexto="Sensor", Usuario="tambien ocupo cable" -> Salida="Cable" (Cambio de tema)
    - Contexto="Fuente 24v", Usuario="y de 10 amperes" -> Salida="Fuente 24v 10 amperes" (Refinamiento)
    
    Respuesta (Solo la frase final limpia):
    """
    try:
        chat = client_ia.chat.completions.create(messages=[{"role": "system", "content": prompt_rewrite}], model="llama-3.3-70b-versatile", temperature=0.1, max_tokens=50)
        return chat.choices[0].message.content.strip().replace('"', '')
    except: return query_actual

def generar_charla_social(mensaje_usuario):
    try:
        chat = client_ia.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres el Asistente Técnico de SM Automatización. Breve y profesional."},
                {"role": "user", "content": mensaje_usuario}
            ],
            model="llama-3.3-70b-versatile", temperature=0.6, max_tokens=80
        )
        return chat.choices[0].message.content
    except: return "Bienvenido a SM Automatización. ¿En qué le puedo apoyar?"

def generar_respuesta_tecnica(query_usuario, productos):
    if not productos: return "No encontré coincidencias exactas."

    contexto_json = []
    for p in productos:
        contexto_json.append({
            "nombre": p['nombre'], "precio": p['precio'], "sku": p.get('sku', 'S/N'),
            "url_link": p['url_web'], "url_foto": p['url_imagen'], "descripcion": p['descripcion'][:250]
        })
    
    datos_str = json.dumps(contexto_json, indent=2)
    total = len(productos)

    system_prompt = f"""
            Eres el Asistente Técnico de 'SM Automatización'. INVENTARIO: {datos_str}
            PROTOCOLO: Solo recomienda del JSON.
            🚨 1. PROTOCOLO DE SEGURIDAD (PRIORIDAD MÁXIMA):
            - TU ÚNICO PROPÓSITO: Asistencia en ingeniería y automatización.
            - NO eres un vendedor que intenta cerrar una venta a la fuerza. NO tomes pedidos reales.
            - PROHIBIDO: Opinar sobre celebridades, política, religión o temas personales.
            - Si preguntan algo fuera de lugar: "Lo siento, mi programación se limita a soporte técnico industrial."
            - REGLA DE ORO: Solo habla de los productos listados arriba en el JSON.
            
            🤝 2. PERSONALIDAD: "EL EXPERTO ACCESIBLE" (UNIVERSAL):
            - TU META: Que CUALQUIER persona entienda (desde una secretaria hasta un experto).
            - TONO: Amable, paciente, claro y servicial.
            - LENGUAJE: Evita jerga técnica compleja a menos que sea necesaria. Explica fácil.
            
            🛠️ 3. LÓGICA DE ASESORÍA:
            - SI ES UN PROYECTO (ej: "Quiero una banda transportadora"): Analiza qué componentes lógicos necesita (Motor, Sensor, PLC) y busca en el JSON qué le sirve.
            - SI CONFIRMAN ("sí", "ese quiero"): Di "Perfecto. ¿Tienes alguna duda técnica sobre la conexión o voltaje antes de cerrar?" (Cierre suave).
            - FLEXIBILIDAD TÉCNICA: Si piden un modelo específico y no está, pero hay uno equivalente en el JSON, ofrécelo como solución técnica viable.
            
            
            📸 FORMATO VISUAL OBLIGATORIO:
            <div class="producto-card">
                <img src="{{url_foto}}" class="producto-img">
                <div class="card-title">{{nombre}}</div>
                <div class="sku-text">SKU: {{sku}}</div>
                <div class="price-text">${{precio}} MXN</div>
                <a href="{{url_link}}" target="_blank" class="btn-link">Ver Ficha Técnica</a>
            </div>
    """
    try:
        chat = client_ia.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": query_usuario}], model="llama-3.3-70b-versatile", temperature=0.1, max_tokens=900)
        return chat.choices[0].message.content
    except Exception as e: return f"Error IA: {e}"

def es_saludo_simple(texto):
    triggers = ["hola", "ola", "buenos", "buenas", "que tal", "saludos"]
    return any(t in unicodedata.normalize('NFD', texto.lower()) for t in triggers) and len(texto.split()) < 6

# --- 4. UI PRINCIPAL ---

# CAMBIO AQUÍ: Usamos el header limpio
style.mostrar_header_limpio()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Bienvenido a SM Automatización. ¿En qué podemos ayudarle hoy?"}]

for msg in st.session_state.messages:
    # Los avatares ahora se cargan desde las rutas definidas en style.py
    avatar = style.ICONO_BOT if msg["role"] == "assistant" else style.ICONO_USER
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"], unsafe_allow_html=True)

# 5. BUCLE
if prompt := st.chat_input("Escriba su consulta..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Tu avatar será el logo SM
    with st.chat_message("user", avatar=style.ICONO_USER): st.markdown(prompt)

    with st.chat_message("assistant", avatar=style.ICONO_BOT):
        if es_saludo_simple(prompt):
            resp = generar_charla_social(prompt)
            st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})
        else:
            with st.spinner("Procesando..."):
                filtro = analizar_filtro_precio(prompt)
                query = contextualizar_consulta(prompt, st.session_state.messages)
                top_k = 12 if filtro else 3
                prods = buscar_productos_vectorial(query, top_k)
                
                if prods and filtro:
                    if filtro == "barato": prods.sort(key=lambda x: x['precio'])
                    elif filtro == "caro": prods.sort(key=lambda x: x['precio'], reverse=True)
                    elif isinstance(filtro, tuple): prods.sort(key=lambda x: abs(x['precio'] - filtro[1]))
                    prods = prods[:3]
                
                resp = generar_respuesta_tecnica(query, prods)
                st.markdown(resp, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": resp})