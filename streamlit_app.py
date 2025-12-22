import streamlit as st
import os
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv
import json
##cambio de nombre a streamlit_app.py

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Asistente Mecatrónico", page_icon="🏭", layout="wide")

# Cargar llaves
load_dotenv()
try:
    cliente_db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    client_ia = Groq(api_key=os.getenv("GROQ_API_KEY"))
    MODELO_IA = "llama-3.3-70b-versatile"
except Exception as e:
    st.error(f"❌ Error crítico de conexión: {e}")
    st.stop()

# --- 2. BARRA LATERAL (KPIs y DEBUG) ---
with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/robot-3.png", width=80)
    st.title("Panel de Control")
    
    # KPI: CONTADOR REAL DE PRODUCTOS
    try:
        # Consultamos a la DB cuántos productos existen realmente
        count_res = cliente_db.table('productos').select("SKU", count='exact', head=True).execute()
        TOTAL_PRODUCTOS = count_res.count
        st.metric(label="📦 Catálogo Total", value=f"{TOTAL_PRODUCTOS} Productos")
    except:
        TOTAL_PRODUCTOS = 500 # Valor por defecto si falla la conexión
        st.metric(label="📦 Catálogo", value="Error Conexión")

    st.divider()
    
    # HERRAMIENTA: MODO RAYOS X
    st.write("🔧 **Ingeniería**")
    debug_mode = st.toggle("Activar Rayos X (Debug)", value=False)
    
    if st.button("🗑️ Borrar Memoria"):
        st.session_state.messages = [{"role": "assistant", "content": "Memoria reiniciada. ¿En qué proyecto te puedo ayudar hoy?"}]
        st.rerun()

# Inicializar Memoria del Chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy tu Asistente Técnico. ¿Buscas algún componente o necesitas asesoría?"}]

# --- 3. LÓGICA INTELIGENTE (EL CEREBRO OPTIMIZADO) ---

def pensar_busqueda(texto_usuario):
    """Detecta intención. Si es charla o confirmación, no gasta recursos buscando."""
    texto = texto_usuario.lower()
    
    # Palabras que indican que NO hay que buscar en base de datos
    no_buscar = ['si', 'no', 'claro', 'gracias', 'ok', 'esta bien', 'ese', 'precio', 'detalles']
    
    # Si la frase es corta y contiene esas palabras, es SEGUIMIENTO
    if any(p in texto for p in no_buscar) and len(texto.split()) < 8:
        return "SEGUIMIENTO_PURO"

    try:
        # Prompt para extraer solo el producto clave
        prompt = f"""
        Tu trabajo es extraer el NOMBRE DEL PRODUCTO de esta frase: '{texto_usuario}'.
        1. Si es charla social o confirmación ("hola", "gracias", "sí"), responde 'SEGUIMIENTO_PURO'.
        2. Si busca un producto, responde SOLO EL NOMBRE (ej: "plc delta").
        """
        completion = client_ia.chat.completions.create(
            model=MODELO_IA,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=15
        )
        return completion.choices[0].message.content.strip()
    except:
        return texto_usuario

def buscar_en_supabase(palabra_clave):
    """Busca en DB con lógica 'Rayos X' para reportar qué pasa."""
    if palabra_clave == "SEGUIMIENTO_PURO" or len(palabra_clave) < 2:
        return [], 0, "🧠 Memoria (No se buscó en DB)"

    termino = palabra_clave.split('\n')[0].replace('.', '').strip()
    
    try:
        # 1. Búsqueda amplia
        query = cliente_db.table('productos').select("*").or_(
            f"Nombre.ilike.%{termino}%,Descripcion_HTML.ilike.%{termino}%,Categoria_Final.ilike.%{termino}%"
        ).limit(15)
        
        resultados_crudos = query.execute().data
        total_encontrados = len(resultados_crudos)

        # 2. Filtro Lógico (Anti-Basura)
        datos_limpios = []
        log_filtro = "✅ Sin filtros agresivos"
        
        # Regla: Si buscas "PLC", ignoramos tapas o botones baratos
        if "plc" in termino.lower():
            log_filtro = "⚠️ Filtro PLC activo (Eliminando tapas/conectores)"
            palabras_prohibidas = ["tapa", "boton", "conector", "receptaculo", "marco"]
            for p in resultados_crudos:
                # Si cuesta menos de 500 y no dice "PLC" explícitamente, lo borramos
                if p['Precio'] < 500 and "plc" not in p['Nombre'].lower():
                    continue 
                if any(mal in p['Nombre'].lower() for mal in palabras_prohibidas):
                    continue
                datos_limpios.append(p)
        else:
            datos_limpios = resultados_crudos

        # Seguridad: Si el filtro borró todo, mostramos los crudos para no decir "no hay nada"
        if len(datos_limpios) == 0 and total_encontrados > 0:
             log_filtro = "🚨 ALERTA: Filtro demasiado estricto. Mostrando datos crudos."
             datos_limpios = resultados_crudos

        return datos_limpios, total_encontrados, log_filtro
    except Exception as e:
        return [], 0, f"Error DB: {e}"

def generar_respuesta_ia(usuario_input, productos_encontrados, historial):
    """
    VERSIÓN GOLD: Fusión de Consultor Técnico + Protocolo de Seguridad.
    """
    info_stock = ""
    if productos_encontrados:
        productos_lite = []
        for p in productos_encontrados:
            productos_lite.append({
                "Nombre": p.get("Nombre"),
                "Precio": p.get("Precio"),
                "SKU": p.get("SKU"),
                "URL": p.get("URL_Web"),
                "FOTO": p.get("URL_Imagen"),
                # ESTO ES IMPORTANTE: Le damos un poco de la descripción técnica a la IA
                "Desc_Tecnica": p.get("Descripcion_HTML", "")[:300] 
            })
        info_stock = json.dumps(productos_lite, ensure_ascii=False)
    
    mensajes = [
        {"role": "system", "content": f"""
            Eres el Asistente Técnico Virtual de 'Soluciones Mecatrónicas'.
            INVENTARIO: Tienes acceso a {TOTAL_PRODUCTOS} productos.
            
            🚨 1. PROTOCOLO DE SEGURIDAD (PRIORIDAD MÁXIMA):
            - TU ÚNICO PROPÓSITO: Asistencia en ingeniería y automatización.
            - NO eres un vendedor que intenta cerrar una venta a la fuerza. NO tomes pedidos reales.
            - PROHIBIDO: Opinar sobre celebridades, política, religión o temas personales.
            - Si preguntan algo fuera de lugar: "Lo siento, mi programación se limita a soporte técnico industrial."
            
            🤝 2. PERSONALIDAD: "EL EXPERTO ACCESIBLE" (UNIVERSAL):
            - TU META: Que CUALQUIER persona entienda (desde una secretaria hasta un experto).
            - TONO: Amable, paciente, claro y servicial.
            - LENGUAJE: Evita jerga técnica compleja a menos que sea necesaria. Explica fácil.
            
            🛠️ 3. LÓGICA DE ASESORÍA:
            - SI ES UN PROYECTO (ej: "Quiero una banda transportadora"): Analiza qué componentes lógicos necesita (Motor, Sensor, PLC) y busca en el JSON qué le sirve.
            - SI CONFIRMAN ("sí", "ese quiero"): Di "Perfecto. ¿Tienes alguna duda técnica sobre la conexión o voltaje antes de cerrar?" (Cierre suave).
            
            📸 4. FORMATO VISUAL:
            - Siempre muestra FOTO: ![Nombre](URL_Imagen)
            - Precio, SKU y Link.
        """}
    ]
    
    # Agregar historial reciente (Formato Streamlit)
    for msg in historial[-5:]:
        mensajes.append({"role": msg["role"], "content": msg["content"]})
    
    prompt = f"Consulta: {usuario_input}"
    if info_stock:
        prompt += f"\n[DATOS TÉCNICOS ENCONTRADOS: {info_stock}]"
    else:
        prompt += "\n[SISTEMA: No hay búsqueda nueva. Usa tu memoria, respeta el protocolo de seguridad y asesora.]"
    
    mensajes.append({"role": "user", "content": prompt})

    try:
        completion = client_ia.chat.completions.create(model=MODELO_IA, messages=mensajes)
        return completion.choices[0].message.content
    except Exception as e:
        return "Lo siento, tuve un error de conexión con mi cerebro digital."

# --- 4. INTERFAZ GRÁFICA ---

st.title("🏭 Soluciones Mecatrónicas")
st.caption("Asistente Técnico v6.2 (Web)")

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input usuario
if prompt := st.chat_input("Escribe tu consulta..."):
    # Guardar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Procesamiento
    keyword = pensar_busqueda(prompt)
    resultados, count_raw, log_filtro = buscar_en_supabase(keyword)
    
    # VISOR DE RAYOS X (DEBUG)
    if debug_mode:
        with st.status("🔍 Procesando datos...", expanded=True):
            st.write(f"**Intención:** `{keyword}`")
            st.write(f"**Supabase:** {count_raw} encontrados.")
            st.write(f"**Filtro:** {log_filtro}")

    # Respuesta IA
    with st.chat_message("assistant"):
        with st.spinner("Consultando manuales..."):
            respuesta = generar_respuesta_ia(prompt, resultados, st.session_state.messages)
            st.markdown(respuesta)
            
    st.session_state.messages.append({"role": "assistant", "content": respuesta})
