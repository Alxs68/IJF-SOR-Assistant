import os
import json
import math
import re
from collections import Counter

passages_path = os.path.join("data", "processed", "rebuild_2026_08", "passages_candidate.json")
with open(passages_path, "r", encoding="utf-8") as f:
    passages = json.load(f)

print(f"Construyendo índice vectorial puro para {len(passages)} pasajes...")

def tokenize(text):
    return re.findall(r"[a-zA-Z0-9_\-]+", text.lower())

doc_freqs = Counter()
doc_tokens = {}

for p in passages:
    pid = p["passage_id"]
    tokens = set(tokenize(p["text_original"]))
    doc_tokens[pid] = tokens
    for t in tokens:
        doc_freqs[t] += 1

num_docs = len(passages)
idf = {}
for term, df in doc_freqs.items():
    idf[term] = math.log((num_docs + 1) / (df + 1)) + 1.0

doc_vectors = {}
for p in passages:
    pid = p["passage_id"]
    term_counts = Counter(tokenize(p["text_original"]))
    total_terms = sum(term_counts.values()) or 1
    
    vec = {}
    norm_sq = 0.0
    for term, count in term_counts.items():
        tf = count / total_terms
        weight = tf * idf.get(term, 1.0)
        vec[term] = weight
        norm_sq += weight * weight
    norm = math.sqrt(norm_sq) or 1.0
    doc_vectors[pid] = {t: w / norm for t, w in vec.items()}

index_data = {
    "version": "2026-08-14",
    "source_sha256": "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620",
    "num_docs": num_docs,
    "idf": idf,
    "vectors": doc_vectors
}

out_index = os.path.join("data", "processed", "rebuild_2026_08", "vector_index_candidate.json")
with open(out_index, "w", encoding="utf-8") as f:
    json.dump(index_data, f)

print(f"Índice vectorial guardado en: {out_index}")

def search(query, top_k=3):
    q_tokens = tokenize(query)
    q_counts = Counter(q_tokens)
    q_norm_sq = 0.0
    q_vec = {}
    for t, c in q_counts.items():
        w = (c / len(q_tokens)) * idf.get(t, 1.0)
        q_vec[t] = w
        q_norm_sq += w * w
    q_norm = math.sqrt(q_norm_sq) or 1.0
    q_vec = {t: w / q_norm for t, w in q_vec.items()}
    
    scores = []
    for pid, d_vec in doc_vectors.items():
        score = sum(q_vec[t] * d_vec.get(t, 0.0) for t in q_vec)
        if score > 0.05:
            scores.append((score, pid))
    scores.sort(reverse=True)
    return scores[:top_k]

sample_q = "head defence cadet shido"
hits = search(sample_q)
print(f"Prueba de búsqueda para '{sample_q}':")
for s, pid in hits:
    print(f"Score {s:.4f} -> {pid}")
