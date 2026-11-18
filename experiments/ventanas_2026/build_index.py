"""Experimento ventanas semanticas: construccion del indice experimental (solo lectura del corpus, sin red, sin LLM).

Ventanas de WIN tokens reales (tokenizador del modelo) con solapamiento OVL sobre text_original de cada pasaje;
se antepone el titulo del apartado (heading_path[0], el mismo titulo que usa el embebido actual "titulo + pagina")
a cada ventana; total <= MAX_TOTAL tokens con [CLS]/[SEP]. Ventanas de texto identico se codifican una sola vez.
Salida (solo en esta carpeta): windows_emb.npy, windows_meta.json, build_report.json
Uso (desde la raiz del repo): python experiments/ventanas_2026/build_index.py
"""
import glob, hashlib, json, os, time
os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                   "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GROQ_API_KEY": ""})
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected")
PROTECTED = ["passages_candidate.json", "dense_embeddings_candidate.npy", "vector_index_candidate.json",
             "knowledge_graph_candidate.json"]
WIN, OVL, MAX_TOTAL = 220, 30, 254


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    hashes_before = {f: sha(os.path.join(D, f)) for f in PROTECTED}
    t0 = time.perf_counter()
    snaps = sorted(glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/*")), reverse=True)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(snaps[0], local_files_only=True)
    assert model.get_sentence_embedding_dimension() == 384
    tok = model.tokenizer
    P = json.load(open(os.path.join(D, "passages_candidate.json"), encoding="utf-8"))
    meta_ids = json.load(open(os.path.join(D, "dense_embeddings_meta.json"), encoding="utf-8")).get("passage_ids")
    assert meta_ids is None or meta_ids == [p["passage_id"] for p in P], "orden de passage_ids distinto al del .npy"

    uniq, uniq_idx = [], {}           # texto de ventana -> fila en la matriz
    windows = []                      # una entrada por (pasaje, ventana)
    title_trunc = 0
    for p in P:
        title = p["heading_path"][0] if p.get("heading_path") else ""
        body = p.get("text_original", "") or ""
        t_ids = tok(title, add_special_tokens=False)["input_ids"]
        enc = tok(body, add_special_tokens=False, return_offsets_mapping=True)
        ids, offs = enc["input_ids"], enc["offset_mapping"]
        budget = MAX_TOTAL - 2 - len(t_ids)
        if budget < WIN:              # titulo largo: se recorta el titulo, no la ventana
            title_trunc += 1
            keep = max(0, MAX_TOTAL - 2 - WIN)
            title = tok.decode(t_ids[:keep]) if keep else ""
        starts = list(range(0, max(1, len(ids) - OVL), WIN - OVL)) if ids else [0]
        for s in starts:
            e = min(len(ids), s + WIN)
            chunk = body[offs[s][0]:offs[e - 1][1]] if ids else ""
            text = f"{title} {chunk}".strip()
            n = len(tok(text, add_special_tokens=True)["input_ids"])
            while n > MAX_TOTAL and e > s + 1:            # salvaguarda por re-tokenizacion de bordes
                e -= 1
                chunk = body[offs[s][0]:offs[e - 1][1]]
                text = f"{title} {chunk}".strip()
                n = len(tok(text, add_special_tokens=True)["input_ids"])
            if text not in uniq_idx:
                uniq_idx[text] = len(uniq)
                uniq.append(text)
            windows.append({"passage_id": p["passage_id"], "token_inicio": s, "token_fin": e,
                            "n_tokens_total": n, "fila": uniq_idx[text]})
            if e >= len(ids):
                break
    t_enc = time.perf_counter()
    emb = model.encode(uniq, batch_size=32, show_progress_bar=False, normalize_embeddings=True).astype(np.float32)
    t1 = time.perf_counter()
    np.save(os.path.join(HERE, "windows_emb.npy"), emb)
    json.dump({"modelo": snaps[0], "win": WIN, "overlap": OVL, "max_total": MAX_TOTAL, "dim": int(emb.shape[1]),
               "passage_ids_orden": [p["passage_id"] for p in P], "windows": windows},
              open(os.path.join(HERE, "windows_meta.json"), "w", encoding="utf-8"), ensure_ascii=False)

    per = {}
    for w in windows:
        per[w["passage_id"]] = per.get(w["passage_id"], 0) + 1
    counts = np.array([per.get(p["passage_id"], 0) for p in P])
    pids = {p["passage_id"] for p in P}
    hashes_after = {f: sha(os.path.join(D, f)) for f in PROTECTED}
    rep = {
        "parametros": {"win": WIN, "overlap": OVL, "max_total_con_especiales": MAX_TOTAL, "titulo": "heading_path[0]",
                       "normalize_embeddings": True, "dim": int(emb.shape[1]), "modelo": os.path.basename(snaps[0])},
        "pasajes": len(P), "ventanas": len(windows), "ventanas_unicas_codificadas": len(uniq),
        "ventanas_duplicadas_evitadas": len(windows) - len(uniq), "titulos_recortados": title_trunc,
        "max_tokens_ventana": max(w["n_tokens_total"] for w in windows),
        "distribucion_ventanas_por_pasaje": {str(k): int((counts == k).sum()) for k in sorted(set(counts.tolist()))},
        "media_ventanas_por_pasaje": round(float(counts.mean()), 2), "max_ventanas_por_pasaje": int(counts.max()),
        "integridad": {"todas_apuntan_a_pasaje_existente": all(w["passage_id"] in pids for w in windows),
                       "pasajes_con_ventanas": int((counts > 0).sum()),
                       "sha256_antes": hashes_before, "sha256_despues": hashes_after,
                       "sha256_identicos": hashes_before == hashes_after},
        "tiempo_s": {"tokenizacion": round(t_enc - t0, 2), "codificacion": round(t1 - t_enc, 2), "total": round(t1 - t0, 2)},
        "memoria_matriz_MB": round(emb.nbytes / 2**20, 2),
        "memoria_matriz_original_MB": round(385 * 384 * 4 / 2**20, 2),
    }
    json.dump(rep, open(os.path.join(HERE, "build_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "integridad"}, ensure_ascii=False, indent=1))
    print("integridad:", {k: v for k, v in rep["integridad"].items() if not k.startswith("sha256_a") and k != "sha256_despues"})


if __name__ == "__main__":
    main()
