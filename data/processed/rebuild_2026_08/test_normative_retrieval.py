import json
import math
import re
from collections import Counter

with open("data/processed/rebuild_2026_08/vector_index_candidate.json", "r", encoding="utf-8") as f:
    idx_data = json.load(f)

with open("data/processed/rebuild_2026_08/passages_candidate.json", "r", encoding="utf-8") as f:
    passages = json.load(f)
passages_dict = {p["passage_id"]: p for p in passages}

source_sha256 = idx_data["source_sha256"]
expected_sha256 = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
print(f"1. Vinculación del Índice con SHA-256 de la fuente: {source_sha256 == expected_sha256}")
assert source_sha256 == expected_sha256, "Fallo: Índice no vinculado a la fuente"

test_queries = [
    {
        "query": "cadet head defend shido",
        "expected_terms": ["head", "cadet", "defend", "shido"]
    },
    {
        "query": "tatami contest area dimensions 8m 10m",
        "expected_terms": ["tatami", "contest", "area"]
    },
    {
        "query": "osaekomi time 20 seconds ippon 10 seconds waza-ari",
        "expected_terms": ["osaekomi", "seconds"]
    },
    {
        "query": "sokuteiki judogi control measurement",
        "expected_terms": ["sokuteiki", "judogi"]
    },
    {
        "query": "medical intervention unconsciousness concussion doctor",
        "expected_terms": ["medical", "doctor"]
    }
]

def search(query, top_k=3):
    q_tokens = re.findall(r"[a-zA-Z0-9_\-]+", query.lower())
    q_counts = Counter(q_tokens)
    q_norm_sq = 0.0
    q_vec = {}
    idf = idx_data["idf"]
    for t, c in q_counts.items():
        w = (c / len(q_tokens)) * idf.get(t, 1.0)
        q_vec[t] = w
        q_norm_sq += w * w
    q_norm = math.sqrt(q_norm_sq) or 1.0
    q_vec = {t: w / q_norm for t, w in q_vec.items()}
    
    scores = []
    for pid, d_vec in idx_data["vectors"].items():
        score = sum(q_vec[t] * d_vec.get(t, 0.0) for t in q_vec)
        if score > 0.05:
            scores.append((score, pid))
    scores.sort(reverse=True)
    return scores[:top_k]

print("\n2. Evaluación de Consultas Normativas:")
for t in test_queries:
    q = t["query"]
    hits = search(q, top_k=3)
    assert hits, f"Fallo: la consulta no devolvió resultados: {q!r}"

    top_pid = hits[0][1]
    top_p = passages_dict.get(top_pid)
    assert top_p is not None, f"Fallo: el índice devolvió un passage_id inexistente: {top_pid}"
    assert top_p["pdf_page_index"] is not None and top_p["article_id"] is not None

    top_text = " ".join(
        passages_dict[pid]["text_original"].lower()
        for _, pid in hits
        if pid in passages_dict
    )
    result_terms = set(re.findall(r"[a-zA-Z0-9_\\-]+", top_text))
    expected_terms = set(t["expected_terms"])
    assert result_terms.intersection(expected_terms), (
        f"Fallo: los tres primeros resultados no contienen ningún término esperado para {q!r}. "
        f"Esperados: {sorted(expected_terms)}; top IDs: {[pid for _, pid in hits]}"
    )

    print(f"Query: '{q}'")
    print(f"   -> Top Hit: {top_pid} (Score: {hits[0][0]:.4f})")
    print(f"   -> Artículo: {top_p['article_id']} | Pág: {top_p['pdf_page_index']} | Heading: {top_p['heading_path'][0]}")
print("\n=== AUDITORÍA D: ÍNDICE Y RECUPERACIÓN NORMATIVA EXITOSA ===")
