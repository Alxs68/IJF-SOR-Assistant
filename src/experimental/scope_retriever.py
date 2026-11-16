"""Fase 11B - Recuperador EXPERIMENTAL (modo SHADOW). Version 0: solo diagnostico.

Reutiliza EN SOLO LECTURA los canales del RRE productivo (rre._sparse_search, rre._dense_search,
rre._is_version_history_passage, rre._query_requests_document_history). No modifica el RRE ni
ninguna de sus estructuras.

  R0  = rre.retrieve(...)            (produccion tal cual; lo llama el evaluador)
  R1  = clean_fusion(rre, query)     misma fusion RRF de produccion (k=60, pesos 1,2/1,0,
                                     bonificacion multicanal) SIN las reglas tematicas fijas
                                     (bonificaciones por palabra clave e identificador de pasaje).
                                     Sirve para medir cuanto aportan / restan esas reglas.
  channel_ranks()                    rango de cada pasaje objetivo en cada canal, para atribuir fallos.

Las variantes R2-R5 (unidades de articulo, ambito, expansion estructural, multilingue) se
anadiran solo si el diagnostico las justifica (ver docs/audits/FASE_11_RECUPERACION_EXPERIMENTAL.md).
Salidas marcadas EXPERIMENTAL_NO_DECISORIO.
"""
from . import EXPERIMENTAL_LABEL

K_RRF = 60
W_SPARSE, W_DENSE = 1.2, 1.0
CHANNEL_DEPTH = 25
SPARSE_MIN = 0.05


def _channels(rre, query, depth=CHANNEL_DEPTH):
    hist = rre._query_requests_document_history(query)
    sparse = [h for h in rre._sparse_search(query, top_k=depth)
              if h[1] >= SPARSE_MIN and (hist or not rre._is_version_history_passage(h[0]))]
    dense = [h for h in rre._dense_search(query, top_k=depth)
             if hist or not rre._is_version_history_passage(h[0])]
    return sparse, dense


def clean_fusion(rre, query, top_k=10, depth=CHANNEL_DEPTH):
    """R1: fusion RRF identica a la productiva hasta el punto previo a las reglas tematicas."""
    sparse, dense = _channels(rre, query, depth)
    scores = {}
    for rank, (pid, _s) in enumerate(sparse, 1):
        scores[pid] = scores.get(pid, 0.0) + W_SPARSE / (K_RRF + rank)
    for rank, (pid, _s) in enumerate(dense, 1):
        scores[pid] = scores.get(pid, 0.0) + W_DENSE / (K_RRF + rank)
    smap, dmap = dict(sparse), dict(dense)
    for pid in scores:
        if pid in smap and pid in dmap:
            scores[pid] = (scores[pid] + 0.035) * 1.35
        elif pid in smap and smap[pid] >= 0.20:
            scores[pid] += 0.035
    ranked = sorted(scores, key=lambda p: -scores[p])
    return {"experimental_label": EXPERIMENTAL_LABEL, "variant": "R1_RRF_SIN_REGLAS_FIJAS",
            "ranked": ranked[:top_k], "scores": {p: round(scores[p], 5) for p in ranked[:top_k]},
            "n_sparse": len(sparse), "n_dense": len(dense)}


def channel_ranks(rre, query, target_pids, depth=CHANNEL_DEPTH):
    """Primer rango (1-based) de cualquier pasaje objetivo en cada canal; None si no aparece."""
    sparse, dense = _channels(rre, query, depth)
    t = set(target_pids)
    first = lambda hits: next((i for i, (p, _s) in enumerate(hits, 1) if p in t), None)
    return {"sparse": first(sparse), "dense": first(dense),
            "sparse_top_score": round(sparse[0][1], 4) if sparse else None,
            "dense_top_score": round(dense[0][1], 4) if dense else None}
