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

# Custom Styling for modern premium UI
st.markdown("""
<style>
    .reportview-container {
        background-color: #0e1117;
    }
    .main-header {
        font-family: 'Outfit', 'Inter', sans-serif;
        color: #1E3A8A;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .status-badge-connected {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.3rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-badge-offline {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.3rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .kun-card {
        border-left: 4px solid #3B82F6;
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.8rem;
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

# Sidebar - Graph Info and Parameters
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b8/International_Judo_Federation_logo.svg", width=120)
    st.title("Gobernanza del Grafo")
    
    # Connection status indicator
    if is_connected:
        st.markdown('<span class="status-badge-connected">🟢 Modo Conectado (LLM Gemini)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-offline">🟡 Modo Offline (Simulado)</span>', unsafe_allow_html=True)
        
    st.write("---")
    
    # Graph Metrics Display
    st.subheader("📊 Métricas de la Línea Base v1.0")
    st.metric("Total KUNs (Nodos)", kg_metrics['nodes_count'])
    st.metric("Relaciones Semánticas", kg_metrics['edges_count'])
    st.metric("Conectividad Promedio", f"{kg_metrics['avg_degree']:.2f}")
    
    st.write("---")
    
    # Retrieval Tuning Params
    st.subheader("⚙️ Parámetros de Consulta")
    k_param = st.slider("Resultados Semánticos (K)", 1, 5, 3)
    min_score_param = st.slider("Score de Descarte Mínimo", 0.05, 0.50, 0.10, 0.05)
    
    # Hubs list
    st.write("---")
    st.subheader("🏆 Nodos Hub Centrales")
    for node, deg in kg_metrics['hubs'][:3]:
        st.write(f"- **{node}**: {deg} conexiones")

# Main Header
st.markdown('<div class="main-header">IJF SOR Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Asistente Oficial de Consulta del Reglamento de la Federación Internacional de Judo (Basado en KUNs Certificadas v1.0)</div>', unsafe_allow_html=True)

# Banner de Advertencia para la versión Demo
st.warning("""
### 📢 Versión de Prueba (Demo)
Este asistente se encuentra en **etapa de desarrollo y pruebas**. 

* **Nota importante:** Debido a que el reglamento oficial de la IJF cuenta con cientos de páginas y aún se encuentra en proceso de carga, **las respuestas de esta demo podrían no reflejar la totalidad de la normativa real**.
""")

# Guía interactiva de temas para los usuarios
with st.expander("🔍 ¿Sobre qué puedes preguntar en esta Demo?"):
    st.markdown("""
    Esta versión de prueba cuenta con **77 Unidades de Conocimiento certificadas** sobre los siguientes temas clave del reglamento:
    *   **🥋 Equipamiento y Tatami:** Dimensiones del tatami y zonas de seguridad, colores de judogi, control con Sokuteiki y tecnología Smart Judogi NFC.
    *   **⏱️ Tiempos y Puntuación:** Criterios para otorgar Ippon, Waza-ari y Yuko, duración del combate, y tiempos de inmovilización (Osaekomi).
    *   **🚫 Sanciones (Shidos y Hansoku-make):** Defensa de cabeza (Head Defence), clavado de cabeza (Diving), caídas en puente (Bridge), salirse del tatami y agarres prohibidos.
    *   **🚸 Seguridad en Cadetes:** Reglas de edad, desmayos por estrangulación y prohibición del seoi-nage inverso.
    *   **🏥 Asistencia Médica:** Límites de intervenciones médicas (máximo 2 por combate) y tratamiento de sangrados.

    **💡 Prueba la robustez del sistema:**
    Si realizas una consulta de un tema que **no está en esta lista** (por ejemplo: *'¿Cuál es el peso de cadetes?'* o *'¿Qué pasa si a un competidor se le cae el celular?'*), el asistente responderá honestamente: 
    > *"Lo siento, no tengo esa información certificada en mi base de datos."*
    
    Esto demuestra la seguridad de nuestra arquitectura **RAG Híbrida** para evitar inventar o alucinar respuestas.
    """)


# Chat Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "trazabilidad" in message:
            with st.expander("📚 Ver Trazabilidad y Citas Oficiales"):
                for kun in message["trazabilidad"]:
                    st.markdown(f"**{kun['id_conocimiento']}: {kun['titulo']}**")
                    st.write(f"* Fuente: `{kun['fuente_origen']}` - {kun.get('referencia_especifica', 'Reglamento oficial')}")
                    st.write(f"* Original: *\"{kun.get('contenido_original', kun['contenido_traduccion'])}\"*")
                    st.write(f"* Interpretación: {kun['interpretacion']}")
                    st.write("---")

# User query input
if user_query := st.chat_input("Escribe tu consulta sobre el reglamento (ej. defensa de cabeza, sokuteiki, smart judogi)..."):
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)
        
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Query Engine
    with st.spinner("Buscando en la base de datos certificada y expandiendo contexto..."):
        # Retrieve context & answer
        res = engine.query(user_query, k=k_param, min_score=min_score_param)
        
        # Get raw KUN data for traceability UI
        _, retrieved_kuns = engine.retrieve_context(user_query, k=k_param, min_score=min_score_param)
        
    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(res['answer'])
        
        # Traceability details
        if retrieved_kuns:
            with st.expander("📚 Ver Trazabilidad y Citas Oficiales"):
                for kun in retrieved_kuns:
                    st.markdown(f"**{kun['id_conocimiento']}: {kun['titulo']}**")
                    st.write(f"* Fuente: `{kun['fuente_origen']}` - {kun.get('referencia_especifica', 'Reglamento oficial')}")
                    st.write(f"* Original: *\"{kun.get('contenido_original', kun['contenido_traduccion'])}\"*")
                    st.write(f"* Interpretación: {kun['interpretacion']}")
                    st.write("---")
            
            # Subgraph visualization using Streamlit Graphviz
            # Compile Graphviz DOT code of the retrieved nodes and their connections
            dot_code = "digraph {\n  rankdir=LR;\n  node [shape=box, style=filled, fontname=\"Arial\"];\n"
            
            retrieved_ids = {k['id_conocimiento'] for k in retrieved_kuns}
            
            # Add nodes
            for kun in retrieved_kuns:
                color = "#3B82F6" if kun['tipo'] == 'REG' else "#EF4444" if kun['tipo'] == 'PEN' else "#10B981"
                dot_code += f'  "{kun["id_conocimiento"]}" [fillcolor="{color}", fontcolor="white", label="{kun["id_conocimiento"]}\\n{kun["tipo"]}"];\n'
                
            # Add edges between retrieved nodes
            for kun in retrieved_kuns:
                node_id = kun['id_conocimiento']
                if node_id in engine.kg.edges:
                    for edge in engine.kg.edges[node_id]:
                        dest_id = edge['id_destino']
                        if dest_id in retrieved_ids:
                            dot_code += f'  "{node_id}" -> "{dest_id}" [label="{edge["tipo_relacion"]}"];\n'
            dot_code += "}"
            
            with st.expander("🕸️ Ver Subgrafo de Relaciones"):
                st.graphviz_chart(dot_code)
                
    st.session_state.messages.append({
        "role": "assistant",
        "content": res['answer'],
        "trazabilidad": retrieved_kuns
    })
