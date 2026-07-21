import streamlit as st
import os
import sys

from dotenv import load_dotenv

# Carga de variables de entorno desde .env
load_dotenv()

# Add src to system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from rag_engine import RagEngine

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
        font-family: 'Outfit', 'Inter', sans-serif;
        color: #1E3A8A;
        font-weight: 700;
        font-size: 1.8rem !important;
        margin-bottom: 0.1rem;
        padding-top: 0rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        color: #6B7280;
        font-size: 0.95rem !important;
        margin-bottom: 1.2rem;
    }
    .status-badge-connected {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-badge-offline {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .kun-card {
        border-left: 4px solid #3B82F6;
        background-color: #F3F4F6;
        padding: 0.8rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.6rem;
        font-size: 0.9rem;
    }
    /* Metric styling adjustments */
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #4B5563 !important;
    }
    /* Expander header font size */
    .streamlit-expanderHeader {
        font-size: 0.9rem !important;
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

# Sidebar - Graph Info and Parameters
with st.sidebar:
    # Stable PNG logo of the IJF from Wikimedia Commons
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/International_Judo_Federation_logo.svg/240px-International_Judo_Federation_logo.svg.png", width=100)
    st.title("Gobernanza del Grafo")
    
    # Connection status indicator
    if is_connected:
        st.markdown('<span class="status-badge-connected">🟢 Modo Conectado (LLM Gemini)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-offline">🟡 Modo Offline (Simulado)</span>', unsafe_allow_html=True)
        
    st.write("---")
    
    # Graph Metrics Display (Smaller Font Sizes applied via CSS)
    st.subheader("📈 Métricas de la Base v1.0")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total KUNs", kg_metrics['nodes_count'])
    with col2:
        st.metric("Relaciones", kg_metrics['edges_count'])
    st.metric("Conectividad Promedio", f"{kg_metrics['avg_degree']:.2f}")
    
    st.write("---")
    
    # Retrieval Tuning Params
    st.subheader("🧭 Ajustes del Motor")
    k_param = st.slider("Resultados Semánticos (K)", 1, 5, 3)
    min_score_param = st.slider("Score de Descarte Mínimo", 0.05, 0.50, 0.10, 0.05)
    
    # Hubs list
    st.write("---")
    st.subheader("🕸️ Nodos Centrales")
    for node, deg in kg_metrics['hubs'][:2]:
        st.write(f"- **{node}**: {deg} conexiones")

    # History Selector
    if len(st.session_state.history) > 0:
        st.write("---")
        st.subheader("📚 Historial de Consultas")
        options = [f"Consulta #{i+1}: {item['query'][:20]}..." for i, item in enumerate(st.session_state.history)]
        selected_option = st.selectbox(
            "Selecciona una consulta pasada para verla:",
            options,
            index=st.session_state.active_index
        )
        # Update active query index
        new_active = options.index(selected_option)
        if new_active != st.session_state.active_index:
            st.session_state.active_index = new_active
            st.rerun()

# Main Header
st.markdown('<div class="main-header">IJF SOR Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Asistente de Consulta del Reglamento de la Federación Internacional de Judo (Basado en KUNs Certificadas v1.0)</div>', unsafe_allow_html=True)

# Expander explaining the scope
with st.expander("🥋 Alcance de la Demo & Temas Disponibles"):
    st.markdown("""
    Esta demo cuenta con **77 Unidades de Conocimiento certificadas** sobre los siguientes temas clave del SOR 2026:
    *   **🥋 Equipamiento:** Dimensiones del tatami, control con Sokuteiki y tecnología Smart Judogi NFC.
    *   **⏱️ Puntuación:** Criterios para Ippon, Waza-ari y Yuko, y tiempos de inmovilización (Osaekomi).
    *   **🚫 Sanciones:** Defensa de cabeza (Head Defence), clavado de cabeza (Diving), caídas en puente, salirse del tatami y agarres prohibidos.
    *   **🚸 Seguridad:** Reglas de Cadetes, desmayos por estrangulación y prohibición del seoi-nage inverso.
    *   **🏥 Asistencia Médica:** Intervenciones médicas máximas (2 por combate) y sangrados.
    """)

# Interactive guide of questions right on the main page for high visibility
st.markdown("### 💡 Preguntas de Ejemplo (Demo)")
preguntas_ejemplo = [
    "Selecciona una pregunta de la lista...",
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
seleccionada = st.selectbox("Elige una consulta predefinida para probar el asistente de inmediato:", preguntas_ejemplo)
trigger_ejemplo = st.button("🚀 Consultar Ejemplo")

st.write("---")

# User query inputs
user_input = st.chat_input("Escribe tu consulta personalizada aquí (ej. osae-komi, puente de cabeza, sangrado)...")

query_to_run = None
if user_input:
    query_to_run = user_input
elif trigger_ejemplo and seleccionada != "Selecciona una pregunta de la lista...":
    query_to_run = seleccionada

# Run query and append to history if new
if query_to_run:
    with st.spinner("Buscando en la base de datos certificada y expandiendo contexto..."):
        # Retrieve context & answer
        res = engine.query(query_to_run, k=k_param, min_score=min_score_param)
        # Get raw KUN data for traceability UI
        _, retrieved_kuns = engine.retrieve_context(query_to_run, k=k_param, min_score=min_score_param)
        
        # Compile Graphviz DOT code of the retrieved nodes and their connections
        dot_code = "digraph {\n  rankdir=LR;\n  node [shape=box, style=filled, fontname=\"Arial\"];\n"
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
                        dot_code += f'  "{node_id}" -> "{dest_id}" [label="{edge["tipo_relacion"]}"];\n'
        dot_code += "}"
        
        # Append query to history state
        st.session_state.history.append({
            "query": query_to_run,
            "answer": res['answer'],
            "trazabilidad": retrieved_kuns,
            "dot_code": dot_code
        })
        st.session_state.active_index = len(st.session_state.history) - 1

# Render only the ACTIVE query-answer pair to keep the screen clean and header visible
if st.session_state.active_index >= 0:
    active_item = st.session_state.history[st.session_state.active_index]
    
    st.markdown(f"**❓ Consulta activa:** {active_item['query']}")
    
    st.markdown("### 🤖 Respuesta del Asistente")
    st.markdown(active_item['answer'])
    
    # Expander for citations
    if active_item['trazabilidad']:
        with st.expander("📚 Ver Trazabilidad y Citas Oficiales"):
            for kun in active_item['trazabilidad']:
                st.markdown(f"**{kun['id_conocimiento']}: {kun['titulo']}**")
                st.write(f"* Fuente: `{kun['fuente_origen']}` - {kun.get('referencia_especifica', 'Reglamento oficial')}")
                st.write(f"* Original: *\"{kun.get('contenido_original', kun['contenido_traduccion'])}\"*")
                st.write(f"* Interpretación: {kun['interpretacion']}")
                st.write("---")
                
        with st.expander("🕸️ Ver Subgrafo de Relaciones"):
            st.graphviz_chart(active_item['dot_code'])
else:
    st.info("💡 Escribe una pregunta en la barra inferior o selecciona un ejemplo de arriba para iniciar la consulta.")
