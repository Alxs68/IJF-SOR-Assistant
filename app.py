import streamlit as st
import os
import sys
import base64

from dotenv import load_dotenv

# Carga de variables de entorno desde .env (exclusivamente para desarrollo local si el archivo existe)
# En producción, se depende únicamente del entorno inyectado por systemd (EnvironmentFile=/etc/ijf-assistant.env)
if os.path.exists('.env'):
    load_dotenv()

# Add src to system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from rag_engine import RagEngine

# Catálogo oficial con detalles y URLs directas a los PDF/páginas de reglas de la IJF
RESOURCE_DETAILS = {
    "DOC-001": {
        "name": "Reglamento SOR 2026 (Sport and Organisation Rules)",
        "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf"
    },

    "DOC-004": {
        "name": "Manual Médico de Judo (PDF)",
        "url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/Medical_Manual_for_Judo_2026-1768917812.pdf"
    },
    "PAG-001": {
        "name": "Portal de Reglas Interactivas de la IJF",
        "url": "https://rules.ijf.org"
    },
    "PAG-002": {
        "name": "Portal de Reglas IJF: Sección Kumikata (Agarres)",
        "url": "https://rules.ijf.org/gripping"
    },
    "PAG-003": {
        "name": "Portal de Reglas IJF: Sección Scoring (Puntuaciones)",
        "url": "https://rules.ijf.org/scoring"
    },
    "PAG-004": {
        "name": "Portal de Reglas IJF: Sección Penalties (Faltas)",
        "url": "https://rules.ijf.org/penalties"
    },
    "PAG-005": {
        "name": "Portal Oficial de Arbitraje IJF",
        "url": "https://referee.ijf.org"
    },
    "VID-001": {
        "name": "Videoteca de Reglas y Seminarios de Arbitraje IJF",
        "url": "https://www.ijf.org/referee-videos"
    },
    "VID-002": {
        "name": "Video de Arbitraje IJF: Demostración de Agarre (Kumikata)",
        "url": "https://rules.ijf.org/gripping"
    },
    "VID-003": {
        "name": "Video de Arbitraje IJF: Criterio de Caídas Yuko",
        "url": "https://rules.ijf.org/scoring"
    },
    "VID-004": {
        "name": "Video de Arbitraje IJF: Seguridad en Ushiro-Sankaku-Gatame",
        "url": "https://rules.ijf.org/penalties"
    },
    "VID-005": {
        "name": "Video de Arbitraje IJF: Evasión y Pérdida de Tiempo",
        "url": "https://rules.ijf.org/penalties"
    },
    "PPT-001": {
        "name": "Presentación del Congreso de Tecnología",
        "url": "https://www.ijf.org/ijf/documents"
    },
    "PPT-002": {
        "name": "Presentación del Seminario de Arbitraje 2026",
        "url": "https://www.ijf.org/referee-commission"
    },
    "NEW-001": {
        "name": "Comunicado Oficial: Reglas de Arbitraje LA28 (Noticias IJF)",
        "url": "https://www.ijf.org/news"
    },
    "NEW-002": {
        "name": "Congreso IJF 2025: Evolución de Tecnología y Reglas (Noticias IJF)",
        "url": "https://www.ijf.org/news/show/ijf-congress-2025-tech-and-rule-evolution"
    },
    "NEW-003": {
        "name": "Reglas Confirmadas para la Temporada 2026 (Noticias IJF)",
        "url": "https://www.ijf.org/news/show/rules-confirmed-ahead-of-the-2026-season"
    },
    "IMG-001": {
        "name": "Diagrama Oficial del Área de Competencia y Tatami",
        "url": "https://www.ijf.org/ijf/documents"
    }
}

# Automatic logo downloader on startup to ensure offline rendering on OCI
logo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
logo_path = os.path.join(logo_dir, 'logo.png')
if not os.path.exists(logo_path):
    try:
        os.makedirs(logo_dir, exist_ok=True)
        import urllib.request
        req = urllib.request.Request(
            'https://7769528.fs1.hubspotusercontent-na1.net/hubfs/7769528/ijf-logo.png',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            with open(logo_path, 'wb') as f:
                f.write(response.read())
    except Exception:
        pass

# Page configuration for a premium, clean look
st.set_page_config(
    page_title="IJF SOR Assistant - MVP",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern premium UI with smaller typography and metric sizing
st.markdown("""
<style>
    /* Adjust Streamlit main page top padding to raise content */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1.5rem !important;
    }
    
    .status-badge-connected {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.2rem 0.4rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-badge-offline {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.2rem 0.4rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .kun-card {
        border-left: 3px solid #3B82F6;
        background-color: #F9FAFB;
        padding: 0.6rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
    }
    /* Metric styling adjustments */
    [data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: #4B5563 !important;
    }
    /* Compact sidebar padding */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        padding-top: 0.15rem !important;
        padding-bottom: 0.15rem !important;
    }
    /* General element spacing */
    .element-container {
        margin-bottom: 0.4rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load logo image as Base64 for inline HTML rendering
def get_base64_logo(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception:
            return None
    return None

# Initialize Engine
@st.cache_resource
def get_rag_engine():
    brain_path = os.path.dirname(os.path.abspath(__file__))
    return RagEngine(brain_path)

try:
    engine = get_rag_engine()
    kg_metrics = engine.kg.get_metrics()
except Exception as e:
    st.error(f"Error initializing RAG Engine: {e}")
    st.stop()

# Environment Credentials Check
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
is_connected = api_key is not None

# Chat/Query Session State Initialization
if "history" not in st.session_state:
    st.session_state.history = []  # List of dicts: {"query": str, "answer": str, "trazabilidad": list, "dot_code": str}
if "active_index" not in st.session_state:
    st.session_state.active_index = -1

# Sidebar - Graph Info and Parameters (Condensed Layout)
with st.sidebar:
    st.markdown("### 🥋 Gobernanza del Grafo")
    
    if is_connected:
        st.markdown('<span class="status-badge-connected">🟢 Modo Conectado (Gemini)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-offline">🟡 Modo Offline (Simulado)</span>', unsafe_allow_html=True)
        
    st.write("---")
    
    # Graph Metrics Display (Condensed columns)
    st.markdown("**📈 Módulos de Conocimiento**")
    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.metric("Total KUNs", kg_metrics['nodes_count'])
    with mcol2:
        st.metric("Relaciones", kg_metrics['edges_count'])
    st.metric("Grado Promedio", f"{kg_metrics['avg_degree']:.2f}")
    
    st.write("---")
    
    # Retrieval Tuning Params (Tightened spacing)
    st.markdown("**🧭 Ajustes de Búsqueda**")
    k_param = st.slider(
        "Cantidad de Reglas a Consultar", 
        1, 5, 3,
        help="Es como elegir cuántos libros abrir en la biblioteca. Un número bajo (1 o 2) busca rápido la regla directa. Un número alto (4 o 5) consulta más artículos relacionados para darte una respuesta más completa."
    )
    min_score_param = st.slider(
        "Filtro Anti-Distracciones", 
        0.05, 0.50, 0.10, 0.05,
        help="El 'guardián' del chatbot. Evita que te conteste cosas que no tengan que ver con el Judo (como recetas o fútbol). Si lo subes, el asistente será más estricto y no responderá a menos que esté muy seguro."
    )
    
    # Hubs list
    st.write("---")
    st.markdown("**🕸️ Nodos Hub**")
    for node, deg in kg_metrics['hubs'][:2]:
        st.markdown(f"- `{node}` ({deg} enlaces)", unsafe_allow_html=True)

    # History Selector (Brought to sidebar)
    if len(st.session_state.history) > 0:
        st.write("---")
        st.markdown("**📚 Historial**")
        options = [f"#{i+1}: {item['query'][:15]}..." for i, item in enumerate(st.session_state.history)]
        selected_option = st.selectbox(
            "Revisar consulta:",
            options,
            index=st.session_state.active_index
        )
        new_active = options.index(selected_option)
        if new_active != st.session_state.active_index:
            st.session_state.active_index = new_active
            st.rerun()

# --- Main Page Header Box (Defined Area, Text on Left, Logo on Right) ---
base64_logo = get_base64_logo(logo_path)

if base64_logo:
    # Premium Header Container with logo on the left side and slate background (Sticky at the top)
    st.markdown(f"""
    <div style="
        position: sticky;
        top: 2.875rem;
        z-index: 99;
        display: flex;
        align-items: center;
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1.4rem 1.5rem;
        margin-bottom: 1rem;
        width: 100%;
    ">
        <div style="flex-shrink: 0; display: flex; align-items: center; margin-right: 1.5rem;">
            <img src="data:image/png;base64,{base64_logo}" style="width: 85px; height: 85px; border-radius: 50%; border: 2.5px solid #3b82f6; object-fit: cover;" />
        </div>
        <div style="flex-grow: 1;">
            <h1 style="font-family: 'Outfit', sans-serif; color: #3b82f6; font-size: 1.6rem; margin: 0; font-weight: 700; line-height: 1.2;">
                IJF SOR Assistant
            </h1>
            <p style="font-family: 'Inter', sans-serif; color: #94a3b8; font-size: 0.88rem; margin: 0.2rem 0 0 0; line-height: 1.3;">
                Asistente de Consulta del Reglamento de la Federación Internacional de Judo (KUNs v1.0)
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Fallback header if logo not found (Sticky at the top)
    st.markdown("""
    <div style="
        position: sticky;
        top: 2.875rem;
        z-index: 99;
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 1rem;
        width: 100%;
    ">
        <h1 style="font-family: 'Outfit', sans-serif; color: #3b82f6; font-size: 1.6rem; margin: 0; font-weight: 700;">
            IJF SOR Assistant
        </h1>
        <p style="font-family: 'Inter', sans-serif; color: #94a3b8; font-size: 0.88rem; margin: 0.2rem 0 0 0;">
            Asistente de Consulta del Reglamento de la Federación Internacional de Judo (KUNs v1.0)
        </p>
    </div>
    """, unsafe_allow_html=True)


# Initialize session states
if "search_query_input_widget" not in st.session_state:
    st.session_state.search_query_input_widget = ""
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# --- Custom Premium CSS for search input and active card ---
st.markdown("""
<style>
    /* Styling search input wrapper */
    div[data-testid="stTextInput"] {
        margin-top: -0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    /* Input field itself */
    div[data-testid="stTextInput"] input {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.05rem !important;
        padding: 0.75rem 1rem 0.75rem 2.8rem !important; /* Left padding for search icon */
        border-radius: 10px !important;
        border: 2px solid #334155 !important;
        background-color: #0f172a !important;
        color: #f8fafc !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        background-color: #1e293b !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3) !important;
    }
    /* Custom magnifying glass icon inside input */
    div[data-testid="stTextInput"] > div::before {
        content: "🔍";
        position: absolute;
        left: 0.9rem;
        top: 0.75rem;
        z-index: 10;
        font-size: 1.1rem;
        opacity: 0.7;
    }
    /* Style search button */
    div.stButton > button[type="primary"] {
        background-color: #3b82f6 !important;
        border-color: #3b82f6 !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3) !important;
    }
    div.stButton > button[type="primary"]:hover {
        background-color: #2563eb !important;
        box-shadow: 0 6px 12px -1px rgba(59, 130, 246, 0.5) !important;
        transform: translateY(-1px);
    }
    /* Custom Active Query Card */
    .active-query-card {
        background-color: #1e293b;
        border-left: 5px solid #3b82f6;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-top: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Callback to safely load example question before widgets are drawn
def load_example():
    sel = st.session_state.get("example_select_widget")
    if sel and sel != "Elige una pregunta para consultar...":
        st.session_state.search_query_input_widget = sel

# Main Query Panel (Centered and prominent)
st.markdown('<div style="font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.6rem; font-family: \'Outfit\', sans-serif; display: flex; align-items: center; gap: 0.5rem;">🥋 <span>Realiza tu pregunta sobre el Reglamento 2026:</span></div>', unsafe_allow_html=True)

scol1, scol2 = st.columns([5, 1.2])
with scol1:
    user_input = st.text_input(
        "Consulta",
        placeholder="Ej: ¿Cómo se sanciona el puente de cabeza? o ¿Cuál es la tolerancia de peso?",
        label_visibility="collapsed",
        key="search_query_input_widget"
    )
with scol2:
    buscar_btn = st.button("Buscar Regla", use_container_width=True, type="primary")

# --- 💡 Preguntas de Ejemplo - Placed inside a beautiful native card to separate areas ---
with st.container(border=True):
    st.markdown('<div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">💡 O selecciona una consulta de demostración predefinida:</div>', unsafe_allow_html=True)
    
    preguntas_ejemplo = [
        "Elige una pregunta para consultar...",
        "¿Se permite la defensa con la cabeza?",
        "¿Cuáles son las dimensiones del tatami?",
        "¿Cuántas intervenciones médicas se permiten por combate?",
        "¿Qué es la tecnología Smart Judogi con chip NFC?",
        "¿Cómo se sanciona el abrazo de oso (bear hug)?",
        "¿Cómo se sanciona el reverse seoi-nage en cadetes?",
        "¿Qué sucede si un competidor se desmaya por estrangulación (shime-waza)?",
        "¿Qué es el Sokuteiki y cómo se usa?",
        "¿Cuáles son las reglas de color de Judogi (blanco y azul)?"
    ]
    
    col_sel, col_btn = st.columns([5, 1.2])
    with col_sel:
        seleccionada = st.selectbox("Selecciona una pregunta predefinida para probar de inmediato:", preguntas_ejemplo, label_visibility="collapsed", key="example_select_widget")
    with col_btn:
        trigger_ejemplo = st.button("Probar Ejemplo", use_container_width=True, on_click=load_example)

st.write("")

# Query validation trigger logic
query_to_run = None
if user_input and (buscar_btn or user_input != st.session_state.get("last_query", "")):
    query_to_run = user_input
    st.session_state.last_query = user_input

# Run query and append to history
if query_to_run:
    with st.spinner("Buscando en la base de datos y consultando modelo..."):
        res = engine.query(query_to_run, k=k_param, min_score=min_score_param)
        _, retrieved_kuns = engine.retrieve_context(query_to_run, k=k_param, min_score=min_score_param)
        
        # Compile Graphviz DOT code
        dot_code = "digraph {\n  rankdir=LR;\n  node [shape=box, style=filled, fontname=\"Arial\", fontsize=10];\n"
        retrieved_ids = {k['id_conocimiento'] for k in retrieved_kuns}
        for kun in retrieved_kuns:
            color = "#3B82F6" if kun['tipo'] == 'REG' else "#EF4444" if kun['tipo'] == 'PEN' else "#10B981"
            dot_code += f'  "{kun["id_conocimiento"]}" [fillcolor="{color}", fontcolor="white", label="{kun["id_conocimiento"]}\\n{kun["tipo"]}"];\n'
        for kun in retrieved_kuns:
            node_id = kun['id_conocimiento']
            if node_id in engine.kg.edges:
                for edge in engine.kg.edges[node_id]:
                    dest_id = edge['id_destino']
                    if dest_id in retrieved_ids:
                        dot_code += f'  "{node_id}" -> "{dest_id}" [label="{edge["tipo_relacion"]}", fontsize=8];\n'
        dot_code += "}"
        
        st.session_state.history.append({
            "query": query_to_run,
            "answer": res['answer'],
            "trazabilidad": retrieved_kuns,
            "dot_code": dot_code
        })
        st.session_state.active_index = len(st.session_state.history) - 1

# Render only the ACTIVE query-answer pair
if st.session_state.active_index >= 0:
    active_item = st.session_state.history[st.session_state.active_index]
    
    # Styled active query card
    st.markdown(f"""
    <div class="active-query-card">
        <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: 700; margin-bottom: 0.3rem;">
            ❓ Consulta Activa
        </div>
        <div style="font-size: 1.1rem; color: #f8fafc; font-weight: 600;">
            {active_item['query']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(active_item['answer'])
    
    # Hide citations and graph if it's a fallback "not found" answer
    is_fallback = "lo siento" in active_item['answer'].lower()
    
    if not is_fallback and active_item['trazabilidad']:
        with st.expander("📚 Ver Trazabilidad y Citas Oficiales"):
            for kun in active_item['trazabilidad']:
                st.markdown(f"**{kun['id_conocimiento']}: {kun['titulo']}**")
                
                source_id = kun['fuente_origen']
                ref_spec = kun.get('referencia_especifica', 'Reglamento')
                
                # Render source as clickable link with friendly name and specific article
                source_link = f"`{source_id}` - {ref_spec}"
                if source_id in RESOURCE_DETAILS:
                    details = RESOURCE_DETAILS[source_id]
                    url = details["url"]
                    name = details["name"]
                    
                    # Extract page number for PDFs to open directly at the correct page (e.g. #page=124)
                    import re
                    page_match = re.search(r'(?:pág|página|page)\.?\s*(\d+)', ref_spec, re.IGNORECASE)
                    if page_match and url.endswith(".pdf"):
                        page_num = page_match.group(1)
                        url = f"{url}#page={page_num}"
                        
                    # Extract timestamp for YouTube videos if applicable
                    ts_match = re.search(r'(\d{1,2}):(\d{2})', ref_spec)
                    if ts_match and "youtube.com" in url:
                        mins = int(ts_match.group(1))
                        secs = int(ts_match.group(2))
                        total_secs = mins * 60 + secs
                        url = f"{url}&t={total_secs}s"
                        
                    source_link = f"[{name} ({ref_spec})]({url})"
                
                st.markdown(f"* **Fuente:** {source_link}")
                st.write(f"* Original: *\"{kun.get('contenido_original', kun['contenido_traduccion'])}\"*")
                st.write(f"* Interpretación: {kun['interpretacion']}")
                st.write("---")
                
        with st.expander("🕸️ Ver Subgrafo de Relaciones"):
            st.graphviz_chart(active_item['dot_code'])
else:
    st.info("💡 Escribe una pregunta en el panel superior o selecciona un ejemplo de arriba para iniciar la consulta.")

# Scope explanation moved to the bottom to keep the core action prominent
st.write("---")
with st.expander("📝 Alcance de la Demo & Temas Disponibles"):
    st.markdown("""
    Esta demo cuenta con **841 Unidades de Conocimiento certificadas** sobre los siguientes temas clave del SOR 2026:
    *   **🥋 Equipamiento e Instalaciones:** Área de combate (tatami), control de judogi con Sokuteiki y tecnología de uniformes Smart Judogi NFC.
    *   **⏱️ Sistemas y Pesaje:** Sistemas de llaves, repechajes, sorteo de cabezas de serie y reglamento de pesaje oficial y aleatorio.
    *   **🚫 Arbitraje y Sanciones:** Puntuaciones (Ippon, Waza-ari, Yuko) e infracciones (puente, defensa de cabeza, diving, no-combatividad, oso).
    *   **🏥 Manual Médico:** Atención médica, desmayos por shime-waza, conmociones (7 días de inhabilitación), código de vestimenta de médicos y dopaje.
    """)
