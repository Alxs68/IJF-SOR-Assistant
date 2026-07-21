import streamlit as st
import os
import sys

from dotenv import load_dotenv

# Carga de variables de entorno desde .env
load_dotenv()

# Add src to system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from rag_engine import RagEngine

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
    .reportview-container {
        background-color: #0e1117;
    }
    .main-header {
        font-family: 'Outfit', sans-serif;
        color: #1E3A8A;
        font-weight: 700;
        font-size: 1.45rem !important;
        margin-bottom: 0.1rem;
        padding-top: 0rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        color: #4B5563;
        font-size: 0.85rem !important;
        margin-bottom: 0.8rem;
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
    # Render local logo file if downloaded successfully
    if os.path.exists(logo_path):
        st.image(logo_path, width=80)
    else:
        # Fallback to standard text placeholder to prevent broken image boxes
        st.markdown("### 🥋 IJF SOR")
        
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
    k_param = st.slider("Resultados (K)", 1, 5, 3)
    min_score_param = st.slider("Score Mínimo", 0.05, 0.50, 0.10, 0.05)
    
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

# Main Header (Concise & Elegant)
st.markdown('<div class="main-header">IJF SOR Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Asistente de Consulta del Reglamento de la Federación Internacional de Judo (KUNs v1.0)</div>', unsafe_allow_html=True)

# 💡 Preguntas de Ejemplo - Placed at the very top for high visibility
st.markdown("### 💡 Preguntas de Ejemplo")
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
seleccionada = st.selectbox("Selecciona una pregunta predefinida para probar de inmediato:", preguntas_ejemplo, label_visibility="collapsed")
trigger_ejemplo = st.button("🚀 Consultar Ejemplo")

st.write("---")

# User query input (Floating at the bottom, or standard input)
user_input = st.chat_input("Escribe tu pregunta sobre el reglamento...")

query_to_run = None
if user_input:
    query_to_run = user_input
elif trigger_ejemplo and seleccionada != "Elige una pregunta para consultar...":
    query_to_run = seleccionada

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
    
    st.markdown(f"**❓ Consulta activa:** {active_item['query']}")
    st.markdown(active_item['answer'])
    
    # Expander for citations
    if active_item['trazabilidad']:
        with st.expander("📚 Ver Trazabilidad y Citas Oficiales"):
            for kun in active_item['trazabilidad']:
                st.markdown(f"**{kun['id_conocimiento']}: {kun['titulo']}**")
                st.write(f"* Fuente: `{kun['fuente_origen']}` - {kun.get('referencia_specifica', 'Reglamento')}")
                st.write(f"* Original: *\"{kun.get('contenido_original', kun['contenido_traduccion'])}\"*")
                st.write(f"* Interpretación: {kun['interpretacion']}")
                st.write("---")
                
        with st.expander("🕸️ Ver Subgrafo de Relaciones"):
            st.graphviz_chart(active_item['dot_code'])
else:
    st.info("💡 Escribe una pregunta en el chat inferior o selecciona un ejemplo de arriba para iniciar la consulta.")

# Scope explanation moved to the bottom to keep the core action prominent
st.write("---")
with st.expander("📝 Alcance de la Demo & Temas Disponibles"):
    st.markdown("""
    Esta demo cuenta con **77 Unidades de Conocimiento certificadas** sobre los siguientes temas clave del SOR 2026:
    *   **🥋 Equipamiento:** Dimensiones del tatami, control con Sokuteiki y tecnología Smart Judogi NFC.
    *   **⏱️ Puntuación:** Criterios para Ippon, Waza-ari y Yuko, y tiempos de inmovilización (Osaekomi).
    *   **🚫 Sanciones:** Defensa de cabeza (Head Defence), clavado de cabeza (Diving), caídas en puente, salirse del tatami y agarres prohibidos.
    *   **🚸 Seguridad:** Reglas de Cadetes, desmayos por estrangulación y prohibición del seoi-nage inverso.
    *   **🏥 Asistencia Médica:** Intervenciones médicas máximas (2 por combate) y sangrados.
    """)
