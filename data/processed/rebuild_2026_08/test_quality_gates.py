import os
import json
import hashlib

passages_file = os.path.join("data", "processed", "rebuild_2026_08", "passages_candidate.json")
with open(passages_file, "r", encoding="utf-8") as f:
    passages = json.load(f)

# 1. Prueba de Cero Contaminación
kun_matches = [p["passage_id"] for p in passages if "KUN-" in p["text_original"] or "KUN-" in p["passage_id"]]
print(f"1. Prueba de Cero Contaminación (KUN heredados): {len(kun_matches)} hallazgos. (Esperado: 0)")
assert len(kun_matches) == 0, "Fallo: existen IDs KUN heredados en los pasajes"

# 2. Prueba de Unicidad de Identificadores
all_ids = [p["passage_id"] for p in passages]
unique_ids = set(all_ids)
print(f"2. Prueba de Unicidad de IDs: {len(unique_ids)}/{len(all_ids)} únicos.")
assert len(all_ids) == len(unique_ids), "Fallo: IDs duplicados"

# 3. Prueba de Cobertura de Páginas Físicas
pages_covered = set(p["pdf_page_index"] for p in passages)
print(f"3. Cobertura de páginas físicas con texto normativo: {len(pages_covered)} páginas.")
assert len(pages_covered) > 250, "Fallo: cobertura insuficiente de páginas físicas"

# 4. Integridad criptográfica de los textos extraídos (no solo formato del hash)
bad_hashes = []
for passage in passages:
    text_original = passage.get("text_original")
    declared_hash = str(passage.get("text_sha256", "")).lower()
    if not isinstance(text_original, str):
        bad_hashes.append((passage.get("passage_id", "<sin-id>"), "text_original ausente/no textual"))
        continue
    computed_hash = hashlib.sha256(text_original.encode("utf-8")).hexdigest()
    if declared_hash != computed_hash:
        bad_hashes.append((passage.get("passage_id", "<sin-id>"), declared_hash, computed_hash))
print(f"4. Verificación SHA-256 real de textos: {len(passages) - len(bad_hashes)}/{len(passages)} coinciden.")
assert not bad_hashes, f"Fallo: hashes de texto no coinciden con text_original. Muestras: {bad_hashes[:3]}"

# 5. Trazabilidad y alineación completa del grafo con el corpus
graph_file = os.path.join("data", "processed", "rebuild_2026_08", "knowledge_graph_candidate.json")
with open(graph_file, "r", encoding="utf-8") as f:
    graph = json.load(f)

nodes = graph.get("nodes", [])
edges = graph.get("edges", [])
node_ids = [node.get("id") for node in nodes]
node_id_set = set(node_ids)
passage_id_set = set(all_ids)
dangling_edges = [
    (edge.get("source"), edge.get("target"))
    for edge in edges
    if edge.get("source") not in node_id_set or edge.get("target") not in node_id_set
]
missing_graph_nodes = sorted(passage_id_set - node_id_set)
unexpected_graph_nodes = sorted(node_id_set - passage_id_set)

print(f"5. Integridad referencial del grafo: {len(edges)} aristas, {len(dangling_edges)} aristas huérfanas.")
assert edges, "Fallo: el grafo no contiene aristas"
assert not dangling_edges, f"Fallo: aristas del grafo apuntan a nodos inexistentes: {dangling_edges[:3]}"
assert len(node_ids) == len(node_id_set), "Fallo: el grafo contiene IDs de nodo duplicados"
assert not missing_graph_nodes and not unexpected_graph_nodes, (
    f"Fallo: nodos del grafo no coinciden con el corpus. "
    f"Faltantes: {missing_graph_nodes[:3]}; extra: {unexpected_graph_nodes[:3]}"
)

print("=== BATERÍA DE PRUEBAS DE CALIDAD SUPERADA CON ÉXITO ===")
