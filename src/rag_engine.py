import os
import sys
import json
import urllib.request
import urllib.error

# Fix Windows cp1252 encoding for print statements with Unicode
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Carga de variables de entorno administrada externamente por systemd en producción
# o por load_dotenv() en app.py en desarrollo local.

# Import our components
from graph_manager import KnowledgeGraph
from vector_store import VectorStore
from citation_resolver import format_citations
from corpus_config import get_active_corpus_config, EDITION_2026_08
from ada_assistant import ArbitrationDecisionAssistant

class RagEngine:
    """Orchestrates RRE / ADA for SOR 2026-08 and maintains isolated legacy fallback for 2026-01."""

    def __init__(self, brain_dir):
        self.brain_dir = brain_dir

        # Load active edition config
        self.config = get_active_corpus_config()
        self.is_2026_08 = (self.config.get("source_id") == "SOR-2026-08-14-ENG")

        # Load API key
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        # KnowledgeGraph and VectorStore instances (initialized conditionally)
        self.kg = KnowledgeGraph()
        self.vs = None

        # RRE / ADA Active Architecture initialization for 2026-08
        self.ada = None
        if self.is_2026_08:
            ada_base = os.path.join(brain_dir, self.config.get("data_dir", "data/processed/rebuild_2026_08"))
            self.ada = ArbitrationDecisionAssistant(base_dir=ada_base)
            self.rre = self.ada.rre

        # Paths based on active edition
        if self.is_2026_08:
            self.passages_path = os.path.join(brain_dir, self.config["passages_file"])
            self.graph_path = os.path.join(brain_dir, self.config["graph_file"])
            self.vector_path = os.path.join(brain_dir, self.config["vector_file"])
        else:
            self.graph_path = os.path.join(brain_dir, self.config["graph_file"])
            self.vector_path = os.path.join(brain_dir, self.config["vector_file"])

        # Load resources
        self.load_resources()

    def load_resources(self):
        """Loads KnowledgeGraph and VectorStore from candidate 2026-08 or legacy serialized files."""
        if self.is_2026_08:
            print(f"[LOG] [RAG Engine] Activando Corpus Oficial: {self.config['version_label']}")
            if not os.path.exists(self.passages_path) or not os.path.exists(self.graph_path):
                raise FileNotFoundError(f"Artefactos de agosto 2026 no encontrados en {self.config['data_dir']}")

            with open(self.passages_path, 'r', encoding='utf-8') as f:
                passages_data = json.load(f)
            with open(self.graph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)

            self.kg.load_from_passages_and_edges(passages_data, graph_data.get('edges', []))
            print(f"[LOG] [RAG Engine] Grafo de agosto 2026 cargado para inspección UI ({len(self.kg.nodes)} nodos).")
            print(f"[LOG] [RAG Engine] Recuperación activa delegada íntegramente a RRE (Híbrido Denso 384d + Sparse + RRF).")
            return

        # Legacy 2026-01 Loading Path
        self.vs = VectorStore()
        print(f"[LOG] [RAG Engine] Activando Corpus Histórico (Legacy): {self.config['version_label']}")
        cache_outdated = False
        if os.path.exists(self.graph_path):
            cache_mtime = os.path.getmtime(self.graph_path)
            markdown_dir = os.path.join(self.brain_dir, self.config.get('markdown_dir', 'data/markdown'))
            if os.path.exists(markdown_dir):
                for f in os.listdir(markdown_dir):
                    if f.endswith('.md'):
                        fpath = os.path.join(markdown_dir, f)
                        if os.path.getmtime(fpath) > cache_mtime:
                            cache_outdated = True
                            print(f"[LOG] [RAG Engine] Archivo de corpus detectado más reciente que el caché: {f}. Invalidando caché del grafo...")
                            break
        else:
            cache_outdated = True

        if not cache_outdated:
            self.kg.load_from_json(self.graph_path)
        else:
            # Recompile on the fly and save graph
            from graph_manager import compile_graph_from_markdown
            self.kg = compile_graph_from_markdown(self.brain_dir)
            os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
            self.kg.save_to_json(self.graph_path)
            print(f"[LOG] [RAG Engine] Grafo de conocimiento recompilado y guardado en {self.graph_path}")

        if not cache_outdated and os.path.exists(self.vector_path):
            self.vs.load_index(self.vector_path)

            # Check if we need to re-index due to mode mismatch
            needs_reindex = False
            if self.api_key and self.vs.mode == "tfidf":
                print("[LOG] [RAG Engine] API Key detectada pero el índice cargado es TF-IDF. Re-indexando en modo Embeddings...")
                needs_reindex = True
            elif not self.api_key and self.vs.mode == "embeddings":
                print("[LOG] [RAG Engine] Sin API Key pero el índice cargado es Embeddings. Re-indexando en modo TF-IDF...")
                needs_reindex = True

            if needs_reindex:
                self.vs.index_kun_corpus(self.kg.nodes, api_key=self.api_key)
                self.vs.save_index(self.vector_path)
        else:
            # Re-index on the fly if cache was outdated or missing
            print("[LOG] [RAG Engine] Re-indexando buscador local por caché desactualizado o inexistente...")
            self.vs.index_kun_corpus(self.kg.nodes, api_key=self.api_key)
            self.vs.save_index(self.vector_path)

    def retrieve_context(self, query, k=3, min_score=None, depth=1):
        """Retrieves semantic hits and expands context using graph relations, prioritizing direct evidence."""
        if min_score is None:
            min_score = self.config.get("min_relevance_score", 0.10)

        # 1. Semantic Search (Evidencia directa clasificada por ranking)
        semantic_hits = self.vs.search(query, k=k, api_key=self.api_key)
        valid_hits = [hit for hit in semantic_hits if hit['score'] >= min_score]

        # Abstención si no hay evidencia directa suficiente
        if not valid_hits:
            return "", []

        seed_ids = [hit['id_conocimiento'] for hit in valid_hits]

        # 2. Graph Expansion (Acotada a los vecinos de las mejores semillas)
        expanded_ids = set()
        if depth > 0:
            for seed in seed_ids:
                neighbors = self.kg.get_neighbors(seed)
                for n in neighbors:
                    dest = n['id_destino']
                    if dest not in seed_ids:
                        expanded_ids.add(dest)

        # 3. Context Assembly priorizando evidencia directa primero, luego contexto adicional
        retrieved_kuns = []
        # A. Semillas directas en orden de relevancia
        for hit in valid_hits:
            kun_data = self.kg.get_kun(hit['id_conocimiento'])
            if kun_data:
                kd = dict(kun_data)
                kd['relevance_score'] = hit['score']
                kd['is_seed'] = True
                retrieved_kuns.append(kd)

        # B. Vecinos del grafo como contexto de soporte complementario (máximo 2 adicionales)
        for kun_id in sorted(expanded_ids)[:2]:
            kun_data = self.kg.get_kun(kun_id)
            if kun_data:
                kd = dict(kun_data)
                kd['relevance_score'] = 0.0
                kd['is_seed'] = False
                retrieved_kuns.append(kd)

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

    def query(self, user_query, k=3, min_score=None):
        """Runs the active ADA / RRE reasoning flow for 2026-08 or legacy fallback for 2026-01."""
        print(f"\n[LOG] [RAG Flow] --- INICIO DE CONSULTA ---")
        print(f"[LOG] [RAG Flow] Consulta recibida: '{user_query}'")

        # 1. Active Architecture: Arbitration Decision Assistant (ADA) + Reasoning Retrieval Engine (RRE)
        if self.is_2026_08 and self.ada is not None:
            ada_res = self.ada.analyze_situation(user_query, top_k=k)
            retrieved_ids = [e["passage_id"] for e in ada_res.get("evidence", [])]
            print(f"[LOG] [ADA/RRE Flow] Estado: {ada_res['status']} | Evidencias RRE: {retrieved_ids}")

            # Adaptar a contrato compatible con UI
            retrieved_data = []
            for ev in ada_res.get("evidence", []):
                retrieved_data.append({
                    "id_conocimiento": ev["passage_id"],
                    "titulo": ev["title"],
                    "tipo": "REG",
                    "fuente_origen": "SOR-2026-08-14-ENG",
                    "referencia_especifica": f"Art. {ev.get('article_id')} (Pág. {ev.get('page')})",
                    "contenido_traduccion": ev.get("text_original", ""),
                    "interpretacion": f"Capítulo: {ev.get('title')}",
                    "article_id": ev.get("article_id"),
                    "pdf_page_index": ev.get("page"),
                    "source_url": ev.get("source_url")
                })
            for rel in ada_res.get("related_passages", []):
                retrieved_data.append({
                    "id_conocimiento": rel["passage_id"],
                    "titulo": rel["title"],
                    "tipo": "REG",
                    "fuente_origen": "SOR-2026-08-14-ENG",
                    "referencia_especifica": f"Art. {rel.get('article_id')} (Pág. {rel.get('page')})",
                    "contenido_traduccion": rel.get("text_original", ""),
                    "interpretacion": f"Referencia Cruzada: {rel.get('relation')}",
                    "article_id": rel.get("article_id"),
                    "pdf_page_index": rel.get("page"),
                    "source_url": rel.get("source_url")
                })

            print(f"[LOG] [RAG Flow] --- FIN DE CONSULTA (ADA/RRE) ---")
            return {
                'query': user_query,
                'answer': ada_res['analysis'],
                'retrieved_kuns': retrieved_ids,
                'retrieved_kuns_data': retrieved_data,
                'context': ""
            }

        # 2. Legacy RAG Flow for 2026-01
        context_text, retrieved_kuns = self.retrieve_context(user_query, k=k, min_score=min_score)

        # Abstención estricta cuando no hay evidencia recuperada
        if not retrieved_kuns:
            print("[LOG] [RAG Flow] Abstención: sin evidencia normativa suficiente.")
            return {
                'query': user_query,
                'answer': (
                    "Lo siento, no tengo esa información certificada en mi base de datos normativa vigente "
                    f"({self.config['version_label']})."
                ),
                'retrieved_kuns': [],
                'retrieved_kuns_data': [],
                'context': ""
            }

        kun_ids = [k['id_conocimiento'] for k in retrieved_kuns]
        print(f"[LOG] [RAG Flow] Recuperación de pasajes/KUNs exitosa: {kun_ids}")

        # Construct Prompt
        prompt = (
            "Eres el asistente oficial del reglamento de la Federación Internacional de Judo (IJF SOR Assistant).\n"
            f"Edición oficial activa: {self.config['version_label']}.\n"
            "Tu misión es responder la pregunta del usuario utilizando exclusivamente la base de conocimiento oficial adjunta.\n\n"
            "--- CONTEXTO DE PASAJES NORMATIVOS --- \n"
            f"{context_text}\n"
            "--------------------------------------------------\n\n"
            "Instrucciones estrictas:\n"
            "1. Responde de forma clara y profesional en base al contexto provisto.\n"
            "2. Cita siempre los identificadores oficiales (ej. [SOR-2026-08-P188-S212] o [KUN-xxxx]) y sus referencias (ej. SOR Art. 18.1.4, Pág. 188).\n"
            "3. Si la respuesta no está contenida en el contexto, indica explícitamente: 'Lo siento, no tengo esa información certificada en mi base de datos'. No inventes ni supongas nada.\n\n"
            f"Pregunta del usuario: {user_query}\n"
            "Respuesta:"
        )
        print(f"[LOG] [RAG Flow] Prompt construido ({len(prompt)} caracteres).")

        # Call API or fallback to mock offline response
        answer = self.call_gemini_api(prompt)

        if not answer:
            print(f"[LOG] [RAG Flow] Fallback: Activando MODO OFFLINE/LOCAL por ausencia de API externa.")
            answer = self._generate_mock_answer(user_query, retrieved_kuns)
        else:
            print(f"[LOG] [RAG Flow] Respuesta del modelo lista para enviarse.")

        # Formatear citas
        formatted_answer = format_citations(answer, retrieved_kuns)

        print(f"[LOG] [RAG Flow] --- FIN DE CONSULTA ---")
        return {
            'query': user_query,
            'answer': formatted_answer,
            'retrieved_kuns': kun_ids,
            'retrieved_kuns_data': retrieved_kuns,
            'context': context_text
        }

    def _generate_mock_answer(self, query, kuns):
        """Generates a clean, user-friendly offline mock answer showing exact normative text without hallucination."""
        if not kuns:
            return (
                "⚠️ **Sin Conexión / Modo Offline**\n\n"
                "Lo siento, no he encontrado ninguna regla en mi base de datos que coincida con tu pregunta."
            )

        ans = (
            f"🔌 **Asistente en Modo Local (Sin Conexión) — Fuente: {self.config['version_label']}**\n\n"
            "*(Respuesta directa desde los pasajes normativos certificados de la base local, sin síntesis externa por IA)*\n\n"
        )

        for k in kuns:
            ans += f"### 🥋 [{k['id_conocimiento']}] {k['titulo']}\n"
            ans += f"* **Referencia Oficial:** {k['fuente_origen']} — {k.get('referencia_especifica', 'SOR Oficial')}\n"
            ans += f"> **Texto Normativo Original (Inglés):**\n"
            # Limitar a los primeros 600 caracteres para legibilidad limpia
            raw_t = k['contenido_traduccion'].strip()
            display_t = (raw_t[:600] + '...') if len(raw_t) > 600 else raw_t
            ans += f"> {display_t}\n\n"
            ans += "---\n\n"

        ans += "💡 *Consejo: Para obtener respuestas sintetizadas interactivamente por IA, active su conexión y configure `GEMINI_API_KEY`.*"
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
