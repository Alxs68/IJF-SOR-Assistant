import os
import json
import urllib.request
import urllib.error

# Carga de variables de entorno administrada externamente por systemd en producción
# o por load_dotenv() en app.py en desarrollo local.

# Import our components
from graph_manager import KnowledgeGraph
from vector_store import VectorStore

class RagEngine:
    """Orchestrates Hybrid RAG: semantic search, knowledge graph expansion, and LLM response generation."""
    
    def __init__(self, brain_dir):
        self.brain_dir = brain_dir
        self.kg = KnowledgeGraph()
        self.vs = VectorStore()
        
        # Paths
        self.graph_path = os.path.join(brain_dir, 'scratch', 'knowledge_graph.json')
        self.vector_path = os.path.join(brain_dir, 'scratch', 'vector_store_index.json')
        
        # Load resources
        self.load_resources()

    def load_resources(self):
        """Loads KnowledgeGraph and VectorStore from local serialized files."""
        if os.path.exists(self.graph_path):
            self.kg.load_from_json(self.graph_path)
        else:
            # Fallback compile on the fly
            from graph_manager import compile_graph_from_markdown
            self.kg = compile_graph_from_markdown(self.brain_dir)
            
        if os.path.exists(self.vector_path):
            self.vs.load_index(self.vector_path)
        else:
            # Index on the fly
            self.vs.index_kun_corpus(self.kg.nodes)

    def retrieve_context(self, query, k=3, min_score=0.10, depth=1):
        """Retrieves semantic hits and expands context using graph relations."""
        # 1. Semantic Search
        semantic_hits = self.vs.search(query, k=k)
        
        # Filter by min_score
        seed_ids = [hit['id_conocimiento'] for hit in semantic_hits if hit['score'] >= min_score]
        
        # 2. Graph Expansion
        expanded_ids = set(seed_ids)
        
        if depth > 0:
            for seed in seed_ids:
                # Get direct neighbors (depth 1)
                neighbors = self.kg.get_neighbors(seed)
                for n in neighbors:
                    expanded_ids.add(n['id_destino'])
                    
        # 3. Context Assembly from single source of truth
        retrieved_kuns = []
        for kun_id in sorted(expanded_ids):
            kun_data = self.kg.get_kun(kun_id)
            if kun_data:
                retrieved_kuns.append(kun_data)
                
        # 4. Formulate markdown context text
        context_parts = []
        for kun in retrieved_kuns:
            context_parts.append(
                f"### {kun['id_conocimiento']}: {kun['titulo']} (Tipo: {kun['tipo']})\n"
                f"* **Fuente:** {kun['fuente_origen']} - {kun.get('referencia_especifica', 'Reglamento oficial')}\n"
                f"* **Texto Oficial:** {kun['contenido_traduccion']}\n"
                f"* **Interpretación Oficial:** {kun['interpretacion']}\n"
            )
            
        context_text = "\n".join(context_parts)
        return context_text, retrieved_kuns

    def call_gemini_api(self, prompt):
        """Calls Gemini API via native HTTP request to generate response (zero-dependency)."""
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        print(f"[LOG] [Gemini API Client] Inicializando cliente...")
        if not api_key:
            print(f"[LOG] [Gemini API Client] Error: GEMINI_API_KEY no encontrada en las variables de entorno.")
            return None
            
        masked_key = api_key[:6] + "..." if len(api_key) > 6 else "Invalida"
        print(f"[LOG] [Gemini API Client] Clave API cargada: {masked_key}")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
        
        # Format payload
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        print(f"[LOG] [Gemini API Client] Enviando petición HTTP POST a Gemini...")
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers,
                method='POST'
            )
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                print(f"[LOG] [Gemini API Client] Petición HTTP exitosa. Analizando respuesta...")
                # Extract text response
                candidates = res_data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts:
                        answer = parts[0].get('text', '')
                        print(f"[LOG] [Gemini API Client] Respuesta generada por el modelo ({len(answer)} caracteres).")
                        return answer
                print(f"[LOG] [Gemini API Client] Error: Formato de respuesta JSON inesperado. candidates no encontrados.")
                return None
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"[LOG] [Gemini API Client] Excepción de HTTP Error: Código {e.code} - Detalle: {error_body}")
            return None
        except Exception as e:
            print(f"[LOG] [Gemini API Client] Excepción General en llamada API: {e}")
            import traceback
            traceback.print_exc()
            return None

    def query(self, user_query, k=3, min_score=0.10):
        """Runs the hybrid RAG flow: retrieval, context creation, prompt assembly, and generation."""
        print(f"\n[LOG] [RAG Flow] --- INICIO DE CONSULTA ---")
        print(f"[LOG] [RAG Flow] Consulta recibida: '{user_query}'")
        
        context_text, retrieved_kuns = self.retrieve_context(user_query, k=k, min_score=min_score)
        
        kun_ids = [k['id_conocimiento'] for k in retrieved_kuns]
        print(f"[LOG] [RAG Flow] Recuperación de KUNs exitosa: {kun_ids}")
        
        # Construct Prompt
        prompt = (
            "Eres el asistente oficial del reglamento de la Federación Internacional de Judo (IJF SOR Assistant).\n"
            "Tu misión es responder la pregunta del usuario utilizando exclusivamente la base de conocimiento oficial adjunta.\n\n"
            "--- CONTEXTO DE UNIDADES DE CONOCIMIENTO (KUN) --- \n"
            f"{context_text}\n"
            "--------------------------------------------------\n\n"
            "Instrucciones estrictas:\n"
            "1. Responde de forma clara y profesional en base al contexto provisto.\n"
            "2. Cita siempre las KUNs utilizadas (ej. [KUN-0001]) y sus fuentes oficiales (ej. SOR Artículo 20).\n"
            "3. Si la respuesta no está contenida en el contexto, indica explícitamente: 'Lo siento, no tengo esa información certificada en mi base de datos'. No inventes ni supongas nada.\n\n"
            f"Pregunta del usuario: {user_query}\n"
            "Respuesta:"
        )
        print(f"[LOG] [RAG Flow] Prompt construido ({len(prompt)} caracteres).")
        
        # Call API or fallback to mock offline response
        answer = self.call_gemini_api(prompt)
        
        if not answer:
            print(f"[LOG] [RAG Flow] Fallback: Activando MODO OFFLINE/SIMULADO por fallo en API.")
            # Offline/Mock fallback generator
            answer = self._generate_mock_answer(user_query, retrieved_kuns)
        else:
            print(f"[LOG] [RAG Flow] Respuesta del modelo lista para enviarse a Streamlit.")
            
        print(f"[LOG] [RAG Flow] --- FIN DE CONSULTA ---")
        return {
            'query': user_query,
            'answer': answer,
            'retrieved_kuns': kun_ids,
            'context': context_text
        }

    def _generate_mock_answer(self, query, kuns):
        """Generates a structured offline mock answer based on retrieved KUNs when API key is missing."""
        if not kuns:
            return "Lo siento, no tengo esa información certificada en mi base de datos."
            
        ans = "[MODO OFFLINE/SIMULADO]\n\n"
        ans += f"En base a los datos recuperados, se identifican las siguientes regulaciones oficiales:\n\n"
        
        for k in kuns:
            ans += f"* **{k['id_conocimiento']} ({k['titulo']}):** {k['contenido_traduccion']}\n"
            ans += f"  * *Interpretación:* {k['interpretacion']}\n"
            ans += f"  * *Fuente:* {k['fuente_origen']} - {k.get('referencia_especifica', 'Reglamento oficial')}\n\n"
            
        ans += "Para respuestas más detalladas en lenguaje natural, configure la variable de entorno GEMINI_API_KEY."
        return ans

if __name__ == '__main__':
    brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    engine = RagEngine(brain_path)
    
    test_query = "defensa de cabeza hansoku-make"
    print(f"Querying: '{test_query}'")
    res = engine.query(test_query)
    print("--- ANSWER ---")
    print(res['answer'])
    print("--- RETRIEVED KUNs ---")
    print(res['retrieved_kuns'])
