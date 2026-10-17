import os
import json

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

# 4. Prueba de Integridad de Hashes de Texto
bad_hashes = sum(1 for p in passages if len(p.get("text_sha256", "")) != 64)
print(f"4. Prueba de Integridad de SHA-256 de texto: {bad_hashes} errores. (Esperado: 0)")
assert bad_hashes == 0, "Fallo: hashes corruptos o inválidos"

# 5. Prueba de Trazabilidad de Grafo
graph_file = os.path.join("data", "processed", "rebuild_2026_08", "knowledge_graph_candidate.json")
with open(graph_file, "r", encoding="utf-8") as f:
    graph = json.load(f)

dangling_edges = 0
node_id_set = {n["id"] for n in graph["nodes"]}
for edge in graph["edges"]:
    if edge["source"] not in node_id_set or edge["target"] not in node_id_set:
        dangling_edges += 1

edge_count = len(graph.get("edges", []))
print(f"5. Integridad Referencial del Grafo: {edge_count} aristas, {dangling_edges} aristas huérfanas.")
assert dangling_edges == 0, "Fallo: aristas del grafo apuntan a nodos inexistentes"

print("=== BATERÍA DE PRUEBAS DE CALIDAD SUPERADA CON ÉXITO ===")
