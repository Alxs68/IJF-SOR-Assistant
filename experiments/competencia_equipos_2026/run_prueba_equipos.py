"""Prueba de recuperacion documental (SOLO LECTURA, sin LLM, sin red) para una consulta amplia sobre competicion por equipos.

Configuraciones (ninguna nueva; todas existentes y documentadas):
  A-prod  RRE de produccion tal como lo construye ADA (ada_assistant.py:124-131: semantic_ranker, desambiguador de
          ordenes, OOD y anclas negativas), indices originales por pagina, R1 apagado (FIX3 apagado por defecto), top_k=5
          (rag_engine.query k=5), expand_graph=True.
  A-ref   referencia de los informes anteriores ("B"): paginas, OOD, R1 encendido.
  B       apartados (experiments/segmentacion_apartados_2026/index), denso truncado, R1   ("S" de los informes)
  C1      ventanas sobre paginas (experiments/ventanas_2026), R1                           ("D" de ventanas_2026)
  C2      ventanas sobre apartados (index/windows_*), R1                                  ("SW" de los informes)
  D       C2 + expansion jerarquica B4 (S=2, MAX_ADD=8, sin filtro), copia literal del mecanismo de
          experiments/reglas_rre_expansion_2026/eval_reglas_expansion.py (se verifica contra results.json)
Consulta: proyeccion determinista de ADA (_translate_to_technical_english sin LLM -> respaldo por diccionario) como
consulta de recuperacion y la pregunta original como domain_query, igual que ADA.
Salidas (solo en esta carpeta): resultados_competencia_equipos.json, stdout_competencia_equipos.log
"""
import collections, hashlib, json, os, re, sys, time, types
os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": "", "GROQ_API_KEY": ""})
for v in ("RRE_CHANNEL_CHAMPIONS", "RRE_ENABLE_SCOPE_PREFERENCE", "RRE_ENABLE_SEMANTIC_RANKER", "ADA_TRANSLATE_ANY_LANG"):
    os.environ.pop(v, None)
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEG = os.path.join(ROOT, "experiments", "segmentacion_apartados_2026")
VEN = os.path.join(ROOT, "experiments", "ventanas_2026")
EXPD = os.path.join(ROOT, "experiments", "reglas_rre_expansion_2026")
IDX = os.path.join(SEG, "index")
D = os.path.join(ROOT, "data", "processed", "rebuild_2026_08_corrected")
PDF = os.path.join(ROOT, "data", "raw", "sor_2026_08_rebuild", "IJF_Sport_and_Organisation_Rules_2026_08_14.pdf")
PDF_SHA = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), SEG]
os.chdir(ROOT)

Q = ("Explícame cómo se desarrolla una competencia de judo por equipos, desde la organización inicial hasta la finalización "
     "de los encuentros. Describe el sistema de competición, la composición de los equipos, el orden de los combates, las "
     "categorías de peso, cómo se determina el equipo ganador y qué sucede en caso de empate, de acuerdo con el SOR 2026")

PROTECTED = ([os.path.join(D, f) for f in ("passages_candidate.json", "dense_embeddings_candidate.npy", "vector_index_candidate.json",
                                           "knowledge_graph_candidate.json", "dense_embeddings_meta.json")]
             + [os.path.join(IDX, f) for f in sorted(os.listdir(IDX))]
             + [os.path.join(SEG, "units.jsonl"), os.path.join(VEN, "windows_emb.npy"), os.path.join(VEN, "windows_meta.json"),
                os.path.join(EXPD, "results.json"), os.path.join(ROOT, "src", "rre_engine.py"), os.path.join(ROOT, "src", "ada_assistant.py"),
                os.path.join(ROOT, "app.py"), PDF])

# Conjunto de referencia: fragmentos LITERALES del PDF (pagina impresa = pdf_page_index). nucleo=True -> imprescindible
# para la explicacion pedida; False -> complementario (bajo numero, round robin, pesaje).
REF = [
    ("SIS-1", "sistema", "2.7", 42, True, "The system of competition for IJF Mixed Teams events will be the elimination system with quarter-final repechage"),
    ("SIS-2", "sistema", "2.7", 42, True, "For other team events, different types of systems can be used such as double repechage, full repechage, or direct knockout"),
    ("SIS-3", "sistema", "2.7", 42, True, "Match is used to define the competition between both teams"),
    ("SIS-4", "sistema", "2.5.2", 38, True, "repechage contests will compete in bronze medal contests against the loser of the"),
    ("SIS-5", "sistema", "2.5", 37, True, "Gold, silver and two (2) bronze medals will be awarded except in the case of low numbers"),
    ("SIS-6", "sistema", "2.6", 41, False, "If there are one (1) to five (5) athletes or teams the low numbers competition systems"),
    ("SIS-7", "sistema", "2.6.2", 42, False, "For other individual and team events, the organiser can choose the competition system"),
    ("COMP-1", "composicion", "2.7.1", 42, True, "Each mixed team must consist of six (6) athletes (3 women and 3 men)"),
    ("COMP-2", "composicion", "2.7.1", 42, True, "A maximum of 12 athletes can be entered, with a maximum of two (2) athletes per mixed team weight category"),
    ("COMP-3", "composicion", "2.7.1", 42, True, "a mixed team will be allowed to compete with a minimum of four (4) athletes"),
    ("COMP-4", "composicion", "2.7.2", 45, True, "Each team will consist of up to five (5) athletes and has the possibility to have up to five"),
    ("COMP-5", "composicion", "2.7.2", 45, True, "A team must consist of a minimum of three (3) athletes"),
    ("COMP-6", "composicion", "2.7.2", 45, True, "A total of 10 athletes can be inscribed with a maximum of two (2) athletes per category"),
    ("ORD-1", "orden", "2.7.1", 43, True, "After the draw of the mixed team event, a further draw will decide the starting category"),
    ("ORD-2", "orden", "2.7.1", 43, True, "The following rounds will start with the next category in the sequence"),
    ("ORD-3", "orden", "2.7.1 (tabla)", 43, True, "1st round: -73 kg, -70 kg, -90 kg, +70 kg, +90 kg, -57 kg"),
    ("ORD-4", "orden", "2.7.2", 46, True, "The contests in female and male team matches will be fought from the lightest weight to the highest weight"),
    ("ORD-5", "orden", "2.7.1", 43, True, "Before each match the team leader must select the athletes for each contest"),
    ("ORD-6", "orden", "2.7.2", 46, True, "Before each match the team leader must select the athletes for each contest"),
    ("ORD-7", "orden", "2.7.1", 43, True, "For the first round the lists must be returned at least 30 minutes before the start of the"),
    ("ORD-8", "orden", "art. 9", 153, True, "in order according to the draw of categories, and will stand face-to-face"),
    ("CAT-1", "categorias", "2.2.2", 34, True, "Over 57.0 kg up to and including 70.0 kg"),
    ("CAT-2", "categorias", "2.2.2/2.2.3", 34, True, "Athletes qualified only in these individual categories can take part in the mixed team"),
    ("CAT-3", "categorias", "2.2.2 (cadetes)", 34, True, "Over 48 kg up to and including 63.0 kg"),
    ("CAT-4", "categorias", "2.2.4", 35, True, "+70 kg Half-heavyweight Over 70.0 kg"),
    ("CAT-5", "categorias", "2.2.4", 35, True, "+90 kg Half-heavyweight Over 90.0 kg"),
    ("CAT-6", "categorias", "2.7.1", 42, True, "each athlete is entitled to compete in their own mixed team weight category or in the next higher mixed team"),
    ("CAT-7", "categorias", "2.7.2", 45, True, "each athlete is entitled to compete in their own weight category or in the next higher category"),
    ("GAN-1", "ganador", "2.7.1", 44, True, "The first mixed team to win the majority of contests is declared the winner"),
    ("GAN-2", "ganador", "2.7.2", 46, True, "The first team to win the majority of contests is declared the winner"),
    ("GAN-3", "ganador", "2.7.1", 43, True, "After the team bow the byes are displayed on the scoreboard and wins are given"),
    ("GAN-4", "ganador", "2.7.1", 44, True, "In IJF events the remaining contests will not be fought except in case of small numbers"),
    ("GAN-5", "ganador", "2.7.1", 44, True, "If one (1) mixed team does not arrive for a match, the other mixed team will be declared"),
    ("GAN-6", "ganador", "2.5.5.2", 40, False, "Rule 1. Number of matches won: Team with more matches won is placed higher"),
    ("GAN-7", "ganador", "2.5.5.2", 40, False, "Rule 3. Sum of all points"),
    ("EMP-1", "empate", "2.7.1", 44, True, "If there are an equal number of wins at the end of the match, there is a draw for the"),
    ("EMP-2", "empate", "2.7.1", 44, True, "mixed team weight category that will compete in a golden score contest"),
    ("EMP-3", "empate", "2.7.1", 44, True, "The draw is done by computer and displayed on the athlete and public"),
    ("EMP-4", "empate", "2.7.1", 45, True, "If there is a double hansoku-make during the golden score contest the following rules"),
    ("EMP-5", "empate", "2.7.2", 46, True, "If there are an equal number of wins at the end of the match see Section 2.7.1 for the"),
    ("EMP-6", "empate", "2.5.5.2", 40, False, "Rule 7. Equal placing/decision contest"),
    ("EMP-7", "empate", "art. 9", 154, True, "In case of equal wins after finishing the last contest of the match, the referee will order"),
    ("DES-1", "desarrollo", "art. 9", 153, True, "In team competitions, before the start of the contests from every encounter, it shall"),
    ("DES-2", "desarrollo", "art. 9", 153, True, "Each one of the three allocated referees will referee two consecutive contests"),
    ("DES-3", "desarrollo", "art. 9", 154, True, "After finishing the last contest of the match, the referee will order the teams to"),
    ("DES-4", "desarrollo", "2.7.1", 43, True, "Duration of each contest: women four (4) minutes and men four (4) minutes"),
    ("DES-5", "desarrollo", "2.7.1", 43, True, "Two (2) coaches and one (1) doctor per team will be allowed to enter the field of play"),
    ("DES-6", "desarrollo", "2.7.2", 46, True, "One (1) coach and one (1) doctor per team will be allowed to enter the field of play"),
    ("DES-7", "desarrollo", "2.7.1", 44, True, "athlete enters the tatami and refuses to compete"),
    ("DES-8", "desarrollo", "2.7.1", 45, True, "The result of the match depends on the rules used"),
    ("DES-9", "desarrollo", "2.7.2", 47, True, "team cannot compete in a match, the other team must submit the lineup for the match"),
    ("ORG-1", "organizacion", "2.7.1", 42, True, "At the time of mixed team confirmation at the accreditation, the delegation must have"),
    ("ORG-2", "organizacion", "2.7.1", 43, True, "the composition of the mixed team must be confirmed by the delegation to the IJF Sport Commission by 13:00"),
    ("ORG-3", "organizacion", "2.7.2", 45, True, "Before the start of the official weigh-in the coach can update the team list"),
    ("ORG-4", "organizacion", "6.4", 80, False, "There are two scenarios for mixed team competitions: a standalone mixed team"),
    ("ORG-5", "organizacion", "6.5", 84, False, "There are two scenarios for team competitions: a standalone team competition and a"),
]
# Unidades y paginas normativas (para rangos por canal). Se derivan de REF y de units.jsonl, no de la recuperacion.
REQ_UNITS = ["SEC-0053", "SEC-0054", "SEC-0055", "SEC-0036", "SEC-0037", "SEC-0038", "TAB-0006", "TAB-0007", "TAB-0008", "TAB-0009",
             "TAB-0010", "TAB-0011", "TAB-0016", "SEC-0041", "SEC-0043", "SEC-0183", "SEC-0048", "SEC-0050", "SEC-0051", "SEC-0052",
             "SEC-0098", "SEC-0102"]


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def norm(s):
    # espacios y apostrofos, y el artefacto de extraccion "Rule 1 ." / "2 .2 .4" (espacio antes de signo) en ambos lados
    return re.sub(r" ([.,:;])", r"\1", " ".join(str(s).replace("’", "'").replace(" ", " ").split()))


def main():
    log = []
    say = lambda *a: (print(*a), log.append(" ".join(str(x) for x in a)))
    assert sha_file(PDF) == PDF_SHA
    hashes_before = {os.path.relpath(p, ROOT): sha_file(p) for p in PROTECTED}

    # ---- 0. Fragmentos de referencia verificados contra el PDF (PyMuPDF), el corpus por paginas y units.jsonl ----
    import fitz
    doc = fitz.open(PDF)
    pdf_pages = {i + 1: norm(doc[i].get_text()) for i in range(len(doc))}
    P = json.load(open(os.path.join(D, "passages_candidate.json"), encoding="utf-8"))
    page_text = {}
    for p in P:
        page_text.setdefault(p["pdf_page_index"], p["text_original"])
    units_list = [json.loads(l) for l in open(os.path.join(SEG, "units.jsonl"), encoding="utf-8")]
    U = {u["passage_id"]: u for u in units_list}
    uspan = lambda u: set(range(u["pdf_page_index"], u["page_end"] + 1))
    ref_check = []
    for rid, fac, lab, pg, core, snip in REF:
        ns = norm(snip)
        in_units = [u["passage_id"] for u in units_list if pg in uspan(u) and ns in norm(u["text_original"])]
        ref_check.append({"id": rid, "faceta": fac, "apartado": lab, "pagina": pg, "nucleo": core, "fragmento": snip,
                          "en_pdf": ns in pdf_pages.get(pg, ""), "en_corpus_paginas": ns in norm(page_text.get(pg, "")),
                          "unidades_que_lo_contienen": in_units,
                          "otras_paginas_pdf_con_el_fragmento": [k for k, v in pdf_pages.items() if k != pg and ns in v]})
    bad = [r["id"] for r in ref_check if not r["en_pdf"]]
    assert not bad, f"fragmentos no literales en el PDF: {bad}"

    # ---- 1. Consulta de recuperacion: la de ADA sin LLM (respaldo determinista) ----
    import rre_engine
    from rre_engine import ReasoningRetrievalEngine
    from ada_assistant import ArbitrationDecisionAssistant
    from negative_domain_anchor_scoring import NegativeDomainAnchorScorer

    t0 = time.perf_counter()
    eng_prod = ReasoningRetrievalEngine(enable_semantic_ranker=True, enable_referee_disambiguation=True,
                                        enable_ood_detector=True, enable_negative_domain_anchors=True)
    eng_p = ReasoningRetrievalEngine(enable_ood_detector=True)
    eng_s = ReasoningRetrievalEngine(base_dir=IDX, enable_ood_detector=True)
    t_init = time.perf_counter() - t0
    assert eng_s.operating_mode == "HYBRID", eng_s.degradation_reason
    stub = types.SimpleNamespace(rre=eng_prod, _call_llm=lambda prompt: (None, {}), _last_translation_usage=None)
    q_ret = ArbitrationDecisionAssistant._translate_to_technical_english(stub, Q)
    neg = NegativeDomainAnchorScorer.score_negative_domain(Q)
    say("consulta de recuperacion (respaldo ADA sin LLM):", q_ret)
    say("ancla negativa (pre-chequeo ADA): is_ood =", neg.is_ood)

    # ---- 2. Canal denso por ventanas (funciones existentes, sin cambios) ----
    from eval_sections import window_dense
    sys.path.insert(0, VEN)
    import importlib.util
    spec = importlib.util.spec_from_file_location("ventanas_eval", os.path.join(VEN, "eval.py"))
    ven = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ven)
    wm_p = json.load(open(os.path.join(VEN, "windows_meta.json"), encoding="utf-8"))
    pids_p = eng_p.dense_meta.get("passage_ids", [p["passage_id"] for p in eng_p.passages])
    assert wm_p["passage_ids_orden"] == list(pids_p)
    W_p_raw = np.load(os.path.join(VEN, "windows_emb.npy"))
    W_p = W_p_raw[[w["fila"] for w in wm_p["windows"]]]
    pos_p = {pid: i for i, pid in enumerate(pids_p)}
    widx_p = np.array([pos_p[w["passage_id"]] for w in wm_p["windows"]])
    dense_win_p = ven.make_window_dense_search(eng_p, W_p, widx_p, len(pids_p), rre_engine.STOPWORDS)
    wm_s = json.load(open(os.path.join(IDX, "windows_meta.json"), encoding="utf-8"))
    W_s = np.load(os.path.join(IDX, "windows_emb.npy"))
    pos_s = {pid: i for i, pid in enumerate(eng_s.dense_meta["passage_ids"])}
    widx_s = np.array([pos_s[w["passage_id"]] for w in wm_s["windows"]])
    dense_win_s = window_dense(eng_s, W_s, widx_s, rre_engine.STOPWORDS)
    dense_orig_p, dense_orig_s = eng_p._dense_search, eng_s._dense_search

    CONFIGS = {  # nombre: (motor, R1, canal denso, es_apartados)
        "A-prod": (eng_prod, "0", None, False),
        "A-ref": (eng_p, "1", dense_orig_p, False),
        "B": (eng_s, "1", dense_orig_s, True),
        "C1": (eng_p, "1", dense_win_p, False),
        "C2": (eng_s, "1", dense_win_s, True),
    }

    def recs_pages(rec, units):
        if units:
            return uspan(U[rec["passage_id"]])
        pg = {rec.get("page")} | {s.get("page") for s in rec.get("source_spans", []) if isinstance(s, dict)}
        return {p for p in pg if p is not None}

    def sat(text, pages, r):
        return r["pagina"] in pages and norm(r["fragmento"]) in norm(text)

    def unit_of_page_passage(pid):
        p = eng_p.passages_by_id[pid]
        return p["pdf_page_index"], (p.get("heading_path") or [""])[0]

    out = {"consulta": Q, "consulta_recuperacion": q_ret, "ancla_negativa_is_ood": bool(neg.is_ood), "referencia": ref_check,
           "configs": {}, "t_init_s": round(t_init, 2)}
    bundles = {}
    for name, (eng, r1, dense, units) in CONFIGS.items():
        os.environ["RRE_CHANNEL_CHAMPIONS"] = r1
        if dense is not None:
            eng._dense_search = dense
        hist = eng._query_requests_document_history(q_ret)
        sp60 = eng._sparse_search(q_ret, top_k=60)
        de60 = eng._dense_search(q_ret, top_k=60)
        sp25 = [h for h in sp60[:25] if h[1] >= 0.05 and (hist or not eng._is_version_history_passage(h[0]))]
        de25 = [h for h in de60[:25] if hist or not eng._is_version_history_passage(h[0])]
        t = time.perf_counter()
        r5 = eng.retrieve(q_ret, top_k=5, expand_graph=True, domain_query=Q)
        t5 = time.perf_counter() - t
        r40 = eng.retrieve(q_ret, top_k=40, expand_graph=False, domain_query=Q)
        sup = []
        if name == "A-prod":
            try:
                sup = eng.retrieve_supplementary(Q, min_score=2.0) or eng.retrieve_supplementary(q_ret, min_score=2.0)
            except Exception as ex:  # se registra, no se oculta
                sup = [{"error": repr(ex)}]
        if dense is not None:
            eng._dense_search = dense_orig_p if eng is eng_p else dense_orig_s
        ev, rel = r5.get("evidence", []), r5.get("related_passages", [])
        pkg = ev + [x for x in rel if x["passage_id"] not in {y["passage_id"] for y in ev}]
        pk_recs = [(x["passage_id"], (U[x["passage_id"]]["text_original"] if units else x.get("text_original", "")), recs_pages(x, units)) for x in pkg]
        bundles[name] = {"top5": [x["passage_id"] for x in ev], "bundle": [x["passage_id"] for x in pkg],
                         "top40": [x["passage_id"] for x in r40.get("evidence", [])], "recs": pk_recs}
        lab = (lambda pid: f"{U[pid]['unit_type']} {U[pid]['label']} p{U[pid]['pdf_page_index']}-{U[pid]['page_end']}") if units else \
              (lambda pid: f"p{unit_of_page_passage(pid)[0]} {unit_of_page_passage(pid)[1][:55]}")
        cand_recs = lambda ids: [(pid, (U if units else eng.passages_by_id)[pid]["text_original"],
                                  uspan(U[pid]) if units else {eng.passages_by_id[pid]["pdf_page_index"]}) for pid in ids]
        sp_ids, de_ids = [h[0] for h in sp25], [h[0] for h in de25]
        f40 = bundles[name]["top40"]
        clas = {}
        for r in ref_check:
            if any(sat(tx, pg, r) for _, tx, pg in pk_recs):
                c = "ENTREGADA"
            elif any(sat(tx, pg, r) for _, tx, pg in cand_recs(f40)):
                c = "DESPLAZADA (en la fusion, fuera del paquete)"
            elif any(sat(tx, pg, r) for _, tx, pg in cand_recs(sp_ids + de_ids)):
                c = "EN CANAL, PERDIDA EN LA FUSION"
            elif any(sat(tx, pg, r) for _, tx, pg in cand_recs([h[0] for h in sp60] + [h[0] for h in de60])):
                c = "FUERA DEL CORTE DE CANAL (26-60)"
            else:
                c = "NUNCA RECUPERADA (top-60)"
            clas[r["id"]] = c
        # rangos de las unidades/paginas normativas
        if units:
            targets = {u: lab(u) for u in REQ_UNITS}
            key = lambda pid: pid
        else:
            targets = {pg: f"p{pg}" for pg in sorted({r["pagina"] for r in ref_check})}
            key = lambda pid: eng.passages_by_id[pid]["pdf_page_index"]
        def rank_in(ids, t):
            return next((i for i, pid in enumerate(ids, 1) if key(pid) == t), None)
        ranks = {str(t): {"etiqueta": l, "tfidf_top60": rank_in([h[0] for h in sp60], t), "denso_top60": rank_in([h[0] for h in de60], t),
                          "fusion_top40": rank_in(f40, t), "paquete": t in {key(pid) for pid in bundles[name]["bundle"]}}
                 for t, l in targets.items()}
        out["configs"][name] = {
            "status": r5.get("status"), "reason": r5.get("reason"), "operating_mode": r5.get("operating_mode"), "tiempo_ms": round(t5 * 1000, 1),
            "canal_tfidf_top25": [(pid, lab(pid), round(s, 4)) for pid, s in sp25],
            "canal_denso_top25": [(pid, lab(pid), round(s, 4)) for pid, s in de25],
            "fusion_top40": [(x["passage_id"], lab(x["passage_id"]), x.get("score")) for x in r40.get("evidence", [])],
            "evidencia_top5": [{"passage_id": x["passage_id"], "etiqueta": lab(x["passage_id"]), "score": x.get("score"),
                                "is_stitched": x.get("is_stitched"), "stitched_kuns": x.get("stitched_kuns"),
                                "paginas": sorted(recs_pages(x, units)), "chars": len(x.get("text_original", ""))} for x in ev],
            "relacionados": [{"passage_id": x["passage_id"], "etiqueta": lab(x["passage_id"]), "desde": x.get("source_seed"),
                              "relacion": x.get("relation")} for x in rel],
            "campeones_R1": r5.get("channel_champions"), "preferencia_ambito": r5.get("scope_preference"),
            "suplementarios": [{k: s.get(k) for k in ("passage_id", "source_id", "source_title", "title", "score", "error") if k in s} for s in sup],
            "paquete_chars": sum(len(tx) for _, tx, _ in pk_recs),
            "clasificacion_referencia": clas, "rangos_normativos": ranks}
        say(f"[{name}] status={r5.get('status')} top5={bundles[name]['top5']} rel={[x['passage_id'] for x in rel]}")
    os.environ.pop("RRE_CHANNEL_CHAMPIONS", None)

    # ---- 3. Ventanas: que ventanas puntuan y a que apartado/pagina pertenecen ----
    def window_trace(eng, W, wm, idx_pid, units, n=25):
        q1 = eng.dense_model.encode(q_ret, normalize_embeddings=True)
        clean = q_ret.lower()
        engq = " ".join(eng.SPANISH_TO_ENGLISH_SYNONYMS.get(t, t) for t in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", clean) if t not in rre_engine.STOPWORDS)
        sims = W @ q1
        if engq and engq != q_ret:
            sims = np.maximum(sims, W @ eng.dense_model.encode(engq, normalize_embeddings=True))
        tok = eng.dense_model.tokenizer
        res = []
        for wi in np.argsort(sims)[::-1][:n]:
            w = wm["windows"][wi]
            src = (U if units else eng.passages_by_id)[w["passage_id"]]
            body = src["text_original"]
            offs = tok(body, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
            a, b = offs[w["token_inicio"]][0], offs[w["token_fin"] - 1][1]
            chunk = body[a:b]
            res.append({"ventana": int(wi), "unidad": w["passage_id"], "etiqueta": (f"{U[w['passage_id']]['unit_type']} {U[w['passage_id']]['label']}" if units
                         else f"p{src['pdf_page_index']} {(src.get('heading_path') or [''])[0][:50]}"),
                        "tokens": [w["token_inicio"], w["token_fin"]], "chars": [a, b], "sim": round(float(sims[wi]), 4),
                        "fragmentos_referencia_en_ventana": [r["id"] for r in ref_check if norm(r["fragmento"]) in norm(chunk)],
                        "inicio": chunk[:90].replace("\n", " ")})
        return res
    out["ventanas"] = {"C1": window_trace(eng_p, W_p, wm_p, None, False), "C2": window_trace(eng_s, W_s, wm_s, None, True)}

    # similitud densa (misma proyeccion que el canal) de las unidades normativas frente al umbral del top-25 del canal
    def dense_profile(fn, ids_of_interest, label):
        hits = fn(q_ret, top_k=100000)
        rank = {pid: (i, s) for i, (pid, s) in enumerate(hits, 1)}
        return {"sim_puesto_25": round(hits[24][1], 4) if len(hits) >= 25 else None, "sim_puesto_1": round(hits[0][1], 4),
                "unidades": {str(k): {"etiqueta": label(k), "rango": rank.get(k, (None, None))[0],
                                      "sim": round(rank[k][1], 4) if k in rank else None} for k in ids_of_interest}}
    ulab = lambda k: f"{U[k]['unit_type']} {U[k]['label']} ({len(U[k]['text_original'])} car.)"
    plab = lambda k: f"p{eng_p.passages_by_id[k]['pdf_page_index']} {(eng_p.passages_by_id[k].get('heading_path') or [''])[0][:40]} ({len(eng_p.passages_by_id[k]['text_original'])} car.)"
    page_ids = ["SOR-2026-08-P042-S054", "SOR-2026-08-P043-S054", "SOR-2026-08-P044-S054", "SOR-2026-08-P045-S055", "SOR-2026-08-P046-S055",
                "SOR-2026-08-P153-S182", "SOR-2026-08-P154-S182", "SOR-2026-08-P091-S106"]
    out["perfil_denso"] = {"A (paginas, truncado)": dense_profile(dense_orig_p, page_ids, plab),
                           "C1 (ventanas sobre paginas)": dense_profile(dense_win_p, page_ids, plab),
                           "B (apartados, truncado)": dense_profile(dense_orig_s, REQ_UNITS, ulab),
                           "C2 (ventanas sobre apartados)": dense_profile(dense_win_s, REQ_UNITS, ulab)}

    # ---- 4. Expansion B4 (copia literal de eval_reglas_expansion.py, limites S=2, MAX_ADD=8, sin filtro) ----
    MAX_ADD, S_DEFAULT = 8, 2
    secs = sorted((u for u in units_list if u["passage_id"].startswith("SEC-")), key=lambda u: int(u["passage_id"][4:]))
    order = {u["passage_id"]: i for i, u in enumerate(secs)}
    lab2u = {}
    for u in secs:
        if u["unit_type"] == "APARTADO":
            lab2u.setdefault(u["label"], u["passage_id"])
    prev_portada, last = {}, None
    for u in secs:
        prev_portada[u["passage_id"]] = last if u["unit_type"] != "PORTADA" else None
        if u["unit_type"] == "PORTADA":
            last = u["passage_id"]

    def sparent(pid):
        u = U[pid]
        if u.get("parent_unit_id"):
            return u["parent_unit_id"], "parent_unit_id"
        if u["unit_type"] != "APARTADO":
            return None, None
        mm = re.match(r"^(article|[a-z]{0,2})(\d+(?:\.\d+)+)$", u["label"])
        if mm:
            cand = mm.group(1) + mm.group(2).rsplit(".", 1)[0]
            if cand in lab2u and lab2u[cand] != pid:
                return lab2u[cand], "etiqueta"
        return prev_portada.get(pid), ("portada" if prev_portada.get(pid) else None)

    PARENT = {pid: sparent(pid) for pid in U}
    kids = collections.defaultdict(list)
    for pid in order:
        if U[pid]["unit_type"] == "APARTADO" and PARENT[pid][0]:
            kids[PARENT[pid][0]].append(pid)
    g = json.load(open(os.path.join(IDX, "knowledge_graph_candidate.json"), encoding="utf-8"))
    refs_table = collections.defaultdict(list)
    for e in g["edges"]:
        if e.get("relation_type") == "references_table":
            refs_table[e["source"]].append(e["target"])

    def siblings(pid, S, gate):
        if U[pid]["unit_type"] != "APARTADO" or not PARENT[pid][0]:
            return []
        sib = sorted((x for x in kids[PARENT[pid][0]] if x != pid), key=lambda x: abs(order[x] - order[pid]))
        if gate is not None:
            sib = [x for x in sib if x in gate]
        return sib if S is None else sib[:S]

    def expansion(bundle_ids, seeds, level, S, max_add, gate):
        seen, added = set(bundle_ids), []
        for seed in seeds:
            par = PARENT[seed][0]
            sib = siblings(seed, S, gate) if level >= 2 else []
            struct = [x for x in [seed, par] + sib if x]
            cands = ([par] if par else []) + sib
            if level >= 3:
                cands += [t for x in struct for t in (U[x].get("table_unit_ids") or [])]
            if level >= 4:
                cands += [t for x in struct for t in refs_table.get(x, [])]
            for c in cands:
                if c not in seen:
                    seen.add(c)
                    added.append(c)
                    if max_add is not None and len(added) >= max_add:
                        return added
        return added

    # verificacion de fidelidad de la copia: mismas adiciones que results.json (SW+B4) en las 82 consultas DEV
    prev = json.load(open(os.path.join(EXPD, "results.json"), encoding="utf-8"))
    fid = {"n": 0, "iguales": 0, "difs": []}
    for row in prev["rows"]:
        if "SW" in row and "SW+B4" in row:
            fid["n"] += 1
            got = expansion(row["SW"]["bundle"], row["SW"]["top5"], 4, S_DEFAULT, MAX_ADD, None) if row["SW"]["top5"] else []
            if got == row["SW+B4"]["added"]:
                fid["iguales"] += 1
            else:
                fid["difs"].append(f"{row['id']}/{row['form']}")
    out["fidelidad_copia_B4"] = fid
    say("fidelidad copia B4:", fid["iguales"], "/", fid["n"])

    base = bundles["C2"]
    added = expansion(base["bundle"], base["top5"], 4, S_DEFAULT, MAX_ADD, None) if base["top5"] else []
    # diagnostico de lo descartado: candidatos sin limites (mismo mecanismo con S=None, max=None) -> motivo
    full = expansion(base["bundle"], base["top5"], 4, None, None, None) if base["top5"] else []
    s2_all = expansion(base["bundle"], base["top5"], 4, S_DEFAULT, None, None) if base["top5"] else []
    origin = {}
    for seed in base["top5"]:
        par = PARENT[seed][0]
        sib_all = siblings(seed, None, None)
        for c, why in ([(par, f"padre ({PARENT[seed][1]})")] if par else []) + [(x, f"hermano #{i}") for i, x in enumerate(sib_all, 1)]:
            origin.setdefault(c, (seed, why))
        for x in [seed, par] + sib_all:
            if not x:
                continue
            for t in U[x].get("table_unit_ids") or []:
                origin.setdefault(t, (seed, f"tabla contenida en {x}"))
            for t in refs_table.get(x, []):
                origin.setdefault(t, (seed, f"tabla referida por {x}"))
    descartes = []
    for c in full:
        if c in added:
            continue
        why = "limite de hermanos S=2" if c not in s2_all else "limite MAX_ADD=8 alcanzado"
        descartes.append({"unidad": c, "etiqueta": f"{U[c]['unit_type']} {U[c]['label']}", "semilla": origin.get(c, (None,))[0],
                          "via": origin.get(c, (None, None))[1], "motivo": why})
    d_bundle = base["bundle"] + added
    d_recs = [(x, U[x]["text_original"], uspan(U[x])) for x in d_bundle]
    clasD = {}
    for r in ref_check:
        if any(sat(tx, pg, r) for _, tx, pg in d_recs):
            clasD[r["id"]] = "ENTREGADA"
        else:
            clasD[r["id"]] = out["configs"]["C2"]["clasificacion_referencia"][r["id"]]
    out["configs"]["D"] = {"base": "C2", "limites": {"nivel": 4, "S": S_DEFAULT, "MAX_ADD": MAX_ADD, "filtro_top20": False},
                           "anadidas": [{"unidad": c, "etiqueta": f"{U[c]['unit_type']} {U[c]['label']} p{U[c]['pdf_page_index']}-{U[c]['page_end']}",
                                         "semilla": origin.get(c, (None,))[0], "via": origin.get(c, (None, None))[1]} for c in added],
                           "descartadas": descartes, "ya_en_paquete_no_se_anaden": [s for s in base["bundle"]],
                           "paquete": d_bundle, "paquete_chars": sum(len(tx) for _, tx, _ in d_recs), "clasificacion_referencia": clasD,
                           "rangos_normativos": {u: {**out["configs"]["C2"]["rangos_normativos"][u], "paquete": u in d_bundle} for u in REQ_UNITS}}
    say("[D] anadidas:", [a["etiqueta"] for a in out["configs"]["D"]["anadidas"]])

    # ---- 5. Resumen de cobertura ----
    summ = {}
    for name in list(CONFIGS) + ["D"]:
        c = out["configs"][name]["clasificacion_referencia"]
        tot = collections.Counter(c.values())
        core = [r for r in ref_check if r["nucleo"]]
        fac = collections.defaultdict(lambda: [0, 0])
        for r in core:
            fac[r["faceta"]][1] += 1
            fac[r["faceta"]][0] += c[r["id"]] == "ENTREGADA"
        summ[name] = {"nucleo_entregado": sum(c[r["id"]] == "ENTREGADA" for r in core), "nucleo_total": len(core),
                      "todos_entregado": tot["ENTREGADA"], "todos_total": len(ref_check), "por_clase": dict(tot),
                      "por_faceta_nucleo": {k: f"{v[0]}/{v[1]}" for k, v in fac.items()}, "paquete_chars": out["configs"][name]["paquete_chars"]}
        say(f"[{name}] nucleo {summ[name]['nucleo_entregado']}/{len(core)}  {summ[name]['por_faceta_nucleo']}  chars={summ[name]['paquete_chars']}")
    out["resumen"] = summ

    hashes_after = {os.path.relpath(p, ROOT): sha_file(p) for p in PROTECTED}
    out["integridad"] = {"archivos": len(hashes_before), "identicos": hashes_before == hashes_after,
                         "cambiados": [k for k in hashes_before if hashes_before[k] != hashes_after.get(k)], "sha_antes": hashes_before}
    say("integridad:", out["integridad"]["identicos"], len(hashes_before))
    json.dump(out, open(os.path.join(HERE, "resultados_competencia_equipos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(HERE, "stdout_competencia_equipos.log"), "w", encoding="utf-8").write("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
