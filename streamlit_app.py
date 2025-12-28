import streamlit as st
import os
import json
import unicodedata
import re
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="Asistente Mecatrónico AI", page_icon="🤖", layout="wide")

load_dotenv()

@st.cache_resource
def init_connections():
    try:
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return supabase, groq, model
    except Exception as e:
        st.error(f"❌ Error conectando cerebros: {e}")
        return None, None, None

client_db, client_ia, model_embedding = init_connections()

# --- 2. FUNCIONES DEL CEREBRO (LÓGICA DURA) ---

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
    """Reescribe la consulta usando el historial."""
    # Si es muy larga, asumimos que tiene todo el contexto
    if len(query_actual.split()) > 12:
        return query_actual

    ultimo_msg_usuario = ""
    for msg in reversed(historial_mensajes):
        if msg["role"] == "user" and msg["content"] != query_actual:
            ultimo_msg_usuario = msg["content"]
            break
            
    if not ultimo_msg_usuario:
        return query_actual

    # Prompt reescritura
    prompt_rewrite = f"""
    Contexto anterior: "{ultimo_msg_usuario}"
    Usuario dice ahora: "{query_actual}"
    
    Tu tarea: Reescribe la búsqueda para que sea completa.
    IGNORA PRECIOS o CANTIDADES en la reescritura. Solo me importa QUÉ PRODUCTO ES.
    
    Ej: Contexto="Busco PLC", Usuario="uno de 5000 pesos" -> Salida="PLC"
    Ej: Contexto="Sensor", Usuario="el mas barato" -> Salida="Sensor"
    
    Solo devuelve la frase reescrita.
    """
    try:
        chat = client_ia.chat.completions.create(
            messages=[{"role": "system", "content": prompt_rewrite}],
            model="llama-3.3-70b-versatile",
            temperature=0.1, max_tokens=40
        )
        return chat.choices[0].message.content.strip()
    except:
        return query_actual

def generar_charla_social(mensaje_usuario):
    """Respuesta rápida para saludos."""
    try:
        chat = client_ia.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres el Asistente Técnico de Soluciones Mecatrónicas. Saluda amable y corto. Invita a cotizar."},
                {"role": "user", "content": mensaje_usuario}
            ],
            model="llama-3.3-70b-versatile", temperature=0.6, max_tokens=80
        )
        return chat.choices[0].message.content
    except:
        return "¡Hola! Ingeniero a la orden. ¿Qué buscamos hoy?"

def generar_respuesta_tecnica(query_usuario, productos):
    """Prompt Maestro RAG."""
    if not productos:
        return "🔍 No encontré coincidencias exactas en el inventario. ¿Podrías intentar con otro término o número de parte?"

    contexto_json = []
    for p in productos:
        contexto_json.append({
            "nombre": p['nombre'],
            "precio": p['precio'],
            "sku": p.get('sku', 'S/N'),
            "url": p['url_web'],
            "img": p['url_imagen'],
            "desc": p['descripcion'][:200]
        })
    
    datos_str = json.dumps(contexto_json, indent=2, ensure_ascii=False)
    
    system_prompt = f"""
    Eres el Asistente Técnico de 'Soluciones Mecatrónicas'.
    INVENTARIO RECUPERADO ({len(productos)} opciones):
    {datos_str}
    
    REGLAS:
    1. Solo recomienda lo que está en la lista de arriba.
    2. Si el usuario preguntó por precios (barato/caro/presupuesto), destaca el precio en tu respuesta.
    3. Sé directo y técnico.
    
    FORMATO VISUAL:
    **[Nombre]**
    ![Foto]({{img}})
    - 💰 ${{precio}} | SKU: {{sku}}
    - [🔗 Ver Producto]({{url}})
    """

    try:
        chat = client_ia.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query_usuario}
            ],
            model="llama-3.3-70b-versatile", temperature=0.1, max_tokens=700
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error IA: {e}"

def es_saludo_simple(texto):
    texto_norm = ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')
    palabras = texto_norm.split()
    if len(palabras) > 5: return False 
    triggers = ["hola", "ola", "buenos", "buenas", "que tal", "saludos", "hi", "hello"]
    if any(t in texto_norm for t in triggers): return True
    return False

# --- 3. INTERFAZ GRÁFICA ---

with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/robot-3.png", width=70)
    st.markdown("### 🎛️ Panel de Ingeniería")
    st.success("🟢 Sistema Online")
    debug_mode = st.toggle("Modo Debug (Ver Lógica)", value=False)
    if st.button("Limpiar Chat"):
        st.session_state.messages = []; st.rerun()

st.title("🏭 Soluciones Mecatrónicas AI")
st.caption("Asistente Técnico Especializado")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy tu copiloto de ingeniería. ¿Qué necesitas cotizar hoy?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. LÓGICA PRINCIPAL ---
if prompt := st.chat_input("Escribe aquí..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        
        # A. RUTA SOCIAL
        if es_saludo_simple(prompt):
            respuesta = generar_charla_social(prompt)
            st.markdown(respuesta)
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
        
        # B. RUTA TÉCNICA
        else:
            with st.spinner("🔍 Analizando inventario..."):
                
                # 1. Detectar intención de precio
                filtro_precio = analizar_filtro_precio(prompt)
                
                # 2. Contextualizar (Entender de qué producto hablamos)
                query_optimizada = contextualizar_consulta(prompt, st.session_state.messages)
                
                # 3. Búsqueda Estratégica
                # Si hay filtro de precio, traemos 12 productos para poder ordenar bien.
                # Si no, traemos solo 3.
                top_k = 12 if filtro_precio else 3
                
                productos = buscar_productos_vectorial(query_optimizada, n_resultados=top_k)
                
                # 4. ORDENAMIENTO INTELIGENTE (Python)
                if productos and filtro_precio:
                    
                    if filtro_precio == "barato":
                        # Ordenar menor a mayor
                        productos.sort(key=lambda x: x['precio'])
                        
                    elif filtro_precio == "caro":
                        # Ordenar mayor a menor
                        productos.sort(key=lambda x: x['precio'], reverse=True)
                        
                    elif isinstance(filtro_precio, tuple) and filtro_precio[0] == 'especifico':
                        # Ordenar por cercanía al precio objetivo (Target)
                        target = filtro_precio[1]
                        productos.sort(key=lambda x: abs(x['precio'] - target))
                    
                    # CORTAR: Nos quedamos con los 3 ganadores del ordenamiento
                    productos = productos[:3]

                # DEBUG
                if debug_mode:
                    with st.expander("🧠 Cerebro (Debug)"):
                        st.write(f"**Query:** `{query_optimizada}`")
                        st.write(f"**Filtro Detectado:** `{filtro_precio}`")
                        st.write(f"**Productos Analizados:** {top_k} -> Se mostraron los mejores 3.")
                        st.json(productos)
                
                # 5. Generar respuesta
                respuesta = generar_respuesta_tecnica(query_optimizada, productos)
                
                st.markdown(respuesta)
                st.session_state.messages.append({"role": "assistant", "content": respuesta})