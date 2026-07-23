import re
import math
import json
import os

class VectorStore:
    """A lightweight, zero-dependency Vector Space Model (TF-IDF) or Semantic Embeddings (Gemini) retriever."""
    
    def __init__(self):
        self.kun_ids = []      # List of KUN IDs indexed
        self.mode = "tfidf"     # "tfidf" or "embeddings"
        
        # TF-IDF structures
        self.vocabulary = {}    # term -> index
        self.idf = {}           # term -> idf weight
        
        self.vectors = []       # List of document vectors (dicts for TF-IDF, list of floats for embeddings)
        self.doc_lengths = []   # Euclidean length of each doc vector (for normalization)

    def _tokenize(self, text):
        """Tokenizes and normalizes text into clean lowercase words."""
        if not text:
            return []
        text = text.lower()
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ñ': 'n'
        }
        for char, repl in replacements.items():
            text = text.replace(char, repl)
        return re.findall(r'\b[a-z0-9]{2,}\b', text)

    def _get_embedding(self, text, api_key):
        """Calls Gemini text-embedding-004 API via native HTTP request (zero-dependency)."""
        import urllib.request
        import urllib.error
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
        payload = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{
                    "text": text
                }]
            }
        }
        headers = {
            "Content-Type": "application/json"
        }
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=headers,
                method='POST'
            )
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                embedding = res_data.get('embedding', {}).get('values', [])
                return embedding
        except Exception as e:
            print(f"[LOG] [VectorStore] Error al obtener embedding de Gemini: {e}")
            return None

    def index_kun_corpus(self, kuns_dict, api_key=None):
        """Indexes KUNs using Gemini Embeddings if api_key is provided, otherwise falls back to local TF-IDF."""
        if api_key:
            print("[LOG] [VectorStore] Inicializando indexación con Gemini Embeddings...")
            self.kun_ids = []
            self.vectors = []
            self.doc_lengths = []
            
            success_count = 0
            for kun_id, kun_data in kuns_dict.items():
                text = f"{kun_data.get('contenido_traduccion', '')} {kun_data.get('interpretacion', '')}"
                embedding = self._get_embedding(text, api_key)
                if embedding:
                    self.kun_ids.append(kun_id)
                    self.vectors.append(embedding)
                    # Compute Euclidean length for cosine similarity normalization
                    length = math.sqrt(sum(v ** 2 for v in embedding))
                    self.doc_lengths.append(length)
                    success_count += 1
                else:
                    print(f"[LOG] [VectorStore] Fallo al obtener embedding para {kun_id}. Activando fallback a TF-IDF.")
                    break
            
            if success_count == len(kuns_dict) and len(kuns_dict) > 0:
                self.mode = "embeddings"
                print(f"[LOG] [VectorStore] Indexación semántica completada con éxito. {success_count} KUNs indexadas.")
                return
                
        # TF-IDF Fallback (either because api_key is None or API failed)
        print("[LOG] [VectorStore] Ejecutando indexación local con TF-IDF...")
        self.mode = "tfidf"
        self.kun_ids = []
        self.vocabulary = {}
        self.idf = {}
        self.vectors = []
        self.doc_lengths = []
        
        doc_terms = []
        doc_freq = {}
        
        for kun_id, kun_data in kuns_dict.items():
            self.kun_ids.append(kun_id)
            text = f"{kun_data.get('contenido_traduccion', '')} {kun_data.get('interpretacion', '')}"
            tokens = self._tokenize(text)
            
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            doc_terms.append(tf)
            
            for token in tf:
                doc_freq[token] = doc_freq.get(token, 0) + 1
                
        num_docs = len(self.kun_ids)
        if num_docs == 0:
            return
            
        for term, df in doc_freq.items():
            self.idf[term] = math.log(num_docs / df) + 1.0
            
        for idx, term in enumerate(self.idf.keys()):
            self.vocabulary[term] = idx
            
        for tf in doc_terms:
            vector = {}
            length_sq = 0.0
            for term, count in tf.items():
                term_idx = self.vocabulary[term]
                tf_weight = 1.0 + math.log(count)
                tfidf_val = tf_weight * self.idf[term]
                vector[term_idx] = tfidf_val
                length_sq += tfidf_val ** 2
            self.vectors.append(vector)
            self.doc_lengths.append(math.sqrt(length_sq))

    def search(self, query, k=5, api_key=None):
        """Searches the index using either Gemini Embeddings or TF-IDF, returning top k hits."""
        if self.mode == "embeddings" and api_key:
            query_embedding = self._get_embedding(query, api_key)
            if query_embedding:
                query_len = math.sqrt(sum(v ** 2 for v in query_embedding))
                if query_len == 0.0:
                    return []
                    
                results = []
                for idx, doc_vector in enumerate(self.vectors):
                    doc_len = self.doc_lengths[idx]
                    if doc_len == 0.0:
                        continue
                    
                    # Compute dot product
                    dot_product = sum(q * d for q, d in zip(query_embedding, doc_vector))
                    similarity = dot_product / (query_len * doc_len)
                    if similarity > 0.0:
                        results.append({
                            'id_conocimiento': self.kun_ids[idx],
                            'score': similarity
                        })
                results = sorted(results, key=lambda x: x['score'], reverse=True)
                return results[:k]
            else:
                print("[LOG] [VectorStore] Error al obtener embedding de consulta. Usando fallback de búsqueda TF-IDF (si está disponible)...")
                
        # TF-IDF search fallback
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.vectors or self.mode != "tfidf":
            return []
            
        query_tf = {}
        for token in query_tokens:
            query_tf[token] = query_tf.get(token, 0) + 1
            
        query_vector = {}
        query_len_sq = 0.0
        for term, count in query_tf.items():
            if term in self.vocabulary:
                term_idx = self.vocabulary[term]
                tf_weight = 1.0 + math.log(count)
                tfidf_val = tf_weight * self.idf[term]
                query_vector[term_idx] = tfidf_val
                query_len_sq += tfidf_val ** 2
                
        query_len = math.sqrt(query_len_sq)
        if query_len == 0.0:
            return []
            
        results = []
        for idx, doc_vector in enumerate(self.vectors):
            doc_len = self.doc_lengths[idx]
            if doc_len == 0.0:
                continue
                
            dot_product = 0.0
            for term_idx, query_val in query_vector.items():
                if term_idx in doc_vector:
                    dot_product += query_val * doc_vector[term_idx]
                    
            similarity = dot_product / (query_len * doc_len)
            if similarity > 0.0:
                results.append({
                    'id_conocimiento': self.kun_ids[idx],
                    'score': similarity
                })
                
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        return results[:k]

    def save_index(self, filepath):
        """Saves the index data structures into a JSON file, supporting both TF-IDF and Embeddings."""
        data = {
            'mode': self.mode,
            'kun_ids': self.kun_ids,
            'doc_lengths': self.doc_lengths
        }
        if self.mode == "embeddings":
            data['vectors'] = self.vectors
        else:
            data['vocabulary'] = self.vocabulary
            data['idf'] = self.idf
            data['vectors'] = [{str(k): v for k, v in doc.items()} for doc in self.vectors]
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_index(self, filepath):
        """Loads index data structures from a JSON file, supporting both TF-IDF and Embeddings."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Index file not found: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.mode = data.get('mode', 'tfidf')
        self.kun_ids = data.get('kun_ids', [])
        self.doc_lengths = data.get('doc_lengths', [])
        
        if self.mode == "embeddings":
            self.vectors = data.get('vectors', [])
        else:
            self.vocabulary = data.get('vocabulary', {})
            self.idf = data.get('idf', {})
            raw_vectors = data.get('vectors', [])
            self.vectors = []
            for doc in raw_vectors:
                self.vectors.append({int(k): v for k, v in doc.items()})

if __name__ == '__main__':
    from graph_manager import compile_graph_from_markdown
    brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kg = compile_graph_from_markdown(brain_path)
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    vs = VectorStore()
    vs.index_kun_corpus(kg.nodes, api_key=api_key)
    
    query = "defensa de cabeza hansoku-make"
    hits = vs.search(query, k=3, api_key=api_key)
    print(f"Index created in mode '{vs.mode}'. Search test for: '{query}'")
    for h in hits:
        print(f"Hit: {h['id_conocimiento']}, Score: {h['score']:.4f}")
        
    index_path = os.path.join(brain_path, 'scratch', 'vector_store_index.json')
    vs.save_index(index_path)
    print(f"Vector Store Index saved to: {index_path}")
