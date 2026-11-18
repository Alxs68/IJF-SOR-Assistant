"""Diagnostico (solo lectura) de SCO-020 con apartados: rango de 6.1, 6.3, tabla 6.3.4 y 6.4.2 en cada canal
(TF-IDF, denso truncado, denso por ventanas), puntuacion RRF final y campeones R1. Sin LLM, sin red.
Uso: python experiments/segmentacion_apartados_2026/diag_sco020.py -> diag_sco020.json
"""
import json, os, sys
os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GROQ_API_KEY": ""})
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), HERE]
os.chdir(ROOT)
import rre_engine
from rre_engine import ReasoningRetrievalEngine
from eval_sections import window_dense

Q = "Do senior athletes get any weight tolerance at the official weigh-in of an individual event?"
rre = ReasoningRetrievalEngine(base_dir=os.path.join(HERE, "index"), enable_ood_detector=True)
U = rre.passages_by_id
lab = {u["passage_id"]: u["heading_path"][0][:70] for u in U.values()}
targets = {k: v for k, v in (("6.1", "SEC-0086"), ("6.2.3", "SEC-0090"), ("6.3", "SEC-0093"), ("6.3.4", "SEC-0097"),
                              ("tabla 6.3.4", next(u for u, x in U.items() if x["unit_type"] == "TABLA" and "Random Weigh-in with Tolerances" in x["heading_path"][0])),
                              ("6.4.2", "SEC-0100"))}
assert U["SEC-0086"]["label"] == "6.1" and U["SEC-0093"]["label"] == "6.3" and U["SEC-0100"]["label"] == "6.4.2"
wm = json.load(open(os.path.join(HERE, "index", "windows_meta.json"), encoding="utf-8"))
pos = {p: i for i, p in enumerate(rre.dense_meta["passage_ids"])}
sw = window_dense(rre, np.load(os.path.join(HERE, "index", "windows_emb.npy")), np.array([pos[w["passage_id"]] for w in wm["windows"]]), rre_engine.STOPWORDS)
out = {"query": Q, "targets": targets}
for name, hits in (("tfidf", rre._sparse_search(Q, top_k=60)), ("denso_truncado", rre._dense_search(Q, top_k=60)), ("denso_ventanas", sw(Q, top_k=60))):
    ids = [p for p, _ in hits]
    out[name] = {"top8": [(p, lab[p], round(s, 4)) for p, s in hits[:8]],
                 "rangos": {k: (ids.index(v) + 1 if v in ids else None) for k, v in targets.items()},
                 "scores": {k: (round(dict(hits)[v], 4) if v in ids else None) for k, v in targets.items()}}
os.environ["RRE_CHANNEL_CHAMPIONS"] = "1"
for name, fn in (("S", rre._dense_search), ("SW", sw)):
    orig = rre._dense_search
    rre._dense_search = fn
    r = rre.retrieve(Q, top_k=10, domain_query=Q)
    rre._dense_search = orig
    ev = [e["passage_id"] for e in r["evidence"]]
    out[f"final_{name}"] = {"top10": [(p, lab[p]) for p in ev], "rangos": {k: (ev.index(v) + 1 if v in ev else None) for k, v in targets.items()},
                            "campeones_R1": r.get("channel_champions")}
os.environ.pop("RRE_CHANNEL_CHAMPIONS", None)
json.dump(out, open(os.path.join(HERE, "diag_sco020.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
