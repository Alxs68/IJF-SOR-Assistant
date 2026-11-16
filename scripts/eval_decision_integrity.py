"""Fase 9 / 9.1 - Evaluacion de integridad decisoria de ADA con generadores simulados (StubLLM).

Motor real; sin LLM real. Niveles separados: cita valida (A), pertinencia (B), suficiencia (C),
respaldo efectivo (D: NO medible sin entailment), abstencion correcta, falso positivo, falso negativo.

Estrategias (mocks; NO estiman la calidad de un LLM real):
  S0_CITA_SIN_RESPALDO   cita el primer pasaje SOR entregado, sin citas literales (sonda B Fase 8)
  S1_PRIMER_PASAJE       cita literal mecanica del PRIMER pasaje entregado (comparable con Fase 9)
  S1B_MEJOR_PASAJE       cita literal mecanica del pasaje entregado mas afin a la consulta
  S2_CIFRA_INVENTADA     S1B + una cifra inexistente en la evidencia
  S3_INFLUENCIA_SHADOW   S1B + cifras/terminos tomados del CONTENIDO de los fragmentos SHADOW entregados
Evidencia minima (9.1): un ancla se considera entregada/citada si lo esta CUALQUIER pasaje de su pagina
(los pasajes de una misma pagina comparten texto identico; comparar por passage_id era un error).
Definiciones:
  falso positivo            SUCCESS en no respondible; o SUCCESS en S2/S3 con inyeccion efectiva
  SUCCESS fuera de evidencia SUCCESS en respondible citando solo paginas ajenas a la evidencia minima
  falso negativo            respondible, cita en pagina de la evidencia minima y ABSTAIN por DIG
Uso: python scripts/eval_decision_integrity.py [--limit N]
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src"), os.path.join(ROOT, "tests")]
for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY"):
    os.environ[k] = ""
os.environ.setdefault("IJF_SOR_EDITION", "2026-08")
V1 = os.path.join(ROOT, "data/eval/benchmark_v1/benchmark_v1.jsonl")
SH = os.path.join(ROOT, "data/eval/benchmark_shadow_v1/benchmark_shadow_v1.jsonl")
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
SHADOW = os.path.join(ROOT, "data/corpus_multisource/processed/multisource_passages.json")
OUT = os.path.join(ROOT, "data/eval/decision_integrity_v1/results_v1_3.json")


def shaf(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_items():
    items = []
    for r in (json.loads(l) for l in open(V1, encoding="utf-8")):
        items.append({"id": r["id"], "set": "v1", "cls": r["category"], "split": r["split"], "text": r["text"],
                      "answerable": r["category"] not in ("FUERA_DE_DOMINIO", "AMBIGUA"),
                      "anchor_pages": [a["page"] for a in r["minimum_evidence"]]})
    for r in (json.loads(l) for l in open(SH, encoding="utf-8")):
        items.append({"id": r["id"], "set": "shadow", "cls": r["evidence_class"], "split": "shadow", "text": r["text"],
                      "answerable": r["evidence_class"] in ("PRIMARIA_CON_AUXILIAR", "AUXILIAR_NO_DEBE_FUNDAMENTAR"),
                      "anchor_pages": [a["page"] for a in r["expected_primary"]]})
    return items


def supp_content(prompt):
    """Content lines of the [COMPLEMENTO-n] entries (header/label lines excluded)."""
    from _ada_contract_helpers import supplementary_block
    out = []
    for m in re.finditer(r"\[COMPLEMENTO-\d+\][^\n]*\n(.*?)(?=\n\n---\n\n|\Z)", supplementary_block(prompt), re.DOTALL):
        out.append(m.group(1).strip())
    return " ".join(out)


def strategies():
    from _ada_contract_helpers import json_answer, grounded_answer, primary_passages, best_delivered_passage

    def best(p, d):
        b = best_delivered_passage(p)
        return [b] if b else d[:1]

    def s3(p, d):
        obj = json.loads(grounded_answer(p, best(p, d)))
        content = supp_content(p)
        prim = " ".join(primary_passages(p).values()).lower()
        nums = [n for n in re.findall(r"\b\d{2,}\b", content) if n not in prim]
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]{4,}", content) if w.lower() not in prim][:3]
        if nums or words:
            obj["extended_analysis"] = "Contexto: " + " ".join(nums[:2] + words)
        obj["_s3_injected"] = bool(nums or words)
        return json.dumps(obj, ensure_ascii=False)
    return {
        "S0_CITA_SIN_RESPALDO": lambda p, d: json_answer(d[:1]),
        "S1_PRIMER_PASAJE": lambda p, d: grounded_answer(p, d[:1]),
        "S1B_MEJOR_PASAJE": lambda p, d: grounded_answer(p, best(p, d)),
        "S2_CIFRA_INVENTADA": lambda p, d: grounded_answer(p, best(p, d), extra_text=" Valor aplicable: 987."),
        "S3_INFLUENCIA_SHADOW": s3,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    before = {p: shaf(p) for p in (CORPUS, SHADOW, V1, SH)}
    from ada_assistant import ArbitrationDecisionAssistant
    from _ada_contract_helpers import StubLLM, citation_ids, primary_passages, delivered_primary_ids
    ada = ArbitrationDecisionAssistant()
    import decision_integrity as dig
    gate = ada._decision_integrity_gate()
    tech = re.compile(r"Consulta técnica normalizada \(EN[^)]*\): (.*)")
    # variant -> (max_df for 1 distinctive term, max_df for 2 specific terms; 0 disables the 2-term rule)
    SWEEP = {"v1.2_unico_0.15": (0.15, 0.0), "v1.2_unico_0.20": (0.20, 0.0), "v1.3_0.15+2x0.30": (0.15, 0.30),
             "v1.3_0.15+2x0.25": (0.15, 0.25)}

    def dig05_at(variant, answer, query, projection, evidence_ids):
        """DIG-05 recomputed under an alternative rule (all other checks unchanged)."""
        t1, t2 = SWEEP[variant]
        qs = dig.content_stems(query) | dig.content_stems(projection)
        n = gate.n_pages

        def pert_q(stems):
            shared = stems & qs
            if any(0 < gate.stem_df.get(x, 0) <= t1 * n for x in shared):
                return True
            return bool(t2) and sum(1 for x in shared if 0 < gate.stem_df.get(x, 0) <= t2 * n) >= 2
        quotes = [q for q in answer.get("evidence_quotes") or [] if isinstance(q, dict)]
        cited = set(re.findall(r"SOR-[A-Za-z0-9]+-[A-Za-z0-9]+-P\d+-S\d+", json.dumps(
            {k: answer.get(k) for k in ("summary", "normative_basis", "citations")}, ensure_ascii=False)))
        pert = {q.get("passage_id") for q in quotes if pert_q(dig.content_stems(str(q.get("quote") or "")))}
        return bool(cited) and cited <= pert and bool(pert & set(evidence_ids))
    page_of = {pid: p.get("pdf_page_index") or p.get("page") for pid, p in ada.rre.passages_by_id.items()}
    items = load_items()[: a.limit or None]
    strats = strategies()
    rows = []
    t0 = time.perf_counter()
    for it in items:
        for name, fn in strats.items():
            stub = StubLLM(analysis=fn)
            ada._call_llm = stub
            res = ada.analyze_situation(it["text"], top_k=5)
            di = res.get("decision_integrity") or {}
            prompt = stub.analysis_prompts[-1] if stub.analysis_prompts else ""
            delivered = delivered_primary_ids(prompt) if prompt else []
            dpages = {page_of.get(x) for x in delivered}
            answer = json.loads(fn(prompt, delivered)) if prompt else {}
            cited = sorted(set(re.findall(r"SOR-[A-Za-z0-9]+-[A-Za-z0-9]+-P\d+-S\d+", json.dumps(answer.get("citations", [])))))
            cpages = {page_of.get(x) for x in cited}
            anchors = set(it["anchor_pages"])
            sweep = {}
            if name in ("S1_PRIMER_PASAJE", "S1B_MEJOR_PASAJE") and prompt and di:
                pm = tech.search(prompt)
                others_ok = all(c["passed"] for c in di.get("checks", []) if c["code"] != "DIG-05_PERTINENCIA_MINIMA")
                ev_ids = [e.get("passage_id") for e in res.get("evidence") or []]
                for t in SWEEP:
                    sweep[t] = others_ok and dig05_at(t, answer, it["text"], pm.group(1) if pm else "", ev_ids)
            rows.append({
                "id": it["id"], "set": it["set"], "cls": it["cls"], "split": it["split"], "answerable": it["answerable"],
                "strategy": name, "llm_called": bool(prompt), "status": res.get("status"),
                "A_citation_valid": bool(di), "dig_decision": di.get("decision"), "dig_failed": di.get("failed_checks", []),
                "dig_failed_detail": {c["code"]: c["detail"][:300] for c in di.get("checks", []) if not c["passed"]},
                "B_pertinence": None if not di else "DIG-05_PERTINENCIA_MINIMA" not in di.get("failed_checks", []),
                "C_sufficiency": None if not di else di.get("levels", {}).get("C_suficiencia", "").startswith("SUPERADO"),
                "D_entailment": "NO_VERIFICADO",
                "anchor_pages": sorted(anchors), "delivered_ids": delivered, "delivered_pages": sorted(x for x in dpages if x),
                "cited_ids": cited, "cited_pages": sorted(x for x in cpages if x),
                "min_evidence_delivered": bool(anchors) and anchors <= dpages,
                "cited_min_evidence": bool(anchors) and bool(anchors & cpages),
                "s3_injected": bool(answer.get("_s3_injected")) if name == "S3_INFLUENCIA_SHADOW" else None,
                "final_citations": citation_ids(res), "sweep_success": sweep,
            })
    elapsed = time.perf_counter() - t0
    summary = {}
    for name in strats:
        rs = [r for r in rows if r["strategy"] == name]
        called = [r for r in rs if r["llm_called"]]
        ans, una = [r for r in rs if r["answerable"]], [r for r in rs if not r["answerable"]]
        succ_ans = [r for r in ans if r["status"] == "SUCCESS"]
        elig = [r for r in ans if r["cited_min_evidence"]]
        s = {
            "n": len(rs), "llm_called": len(called),
            "A_citation_valid": sum(r["A_citation_valid"] for r in called),
            "B_pertinence_pass": sum(bool(r["B_pertinence"]) for r in called),
            "C_sufficiency_pass": sum(bool(r["C_sufficiency"]) for r in called),
            "D_effective_support": "NO_MEDIBLE (sin entailment)",
            "success": sum(r["status"] == "SUCCESS" for r in rs),
            "success_answerable": len(succ_ans),
            "success_answerable_citing_min_evidence": sum(r["cited_min_evidence"] for r in succ_ans),
            "success_outside_min_evidence": [r["id"] for r in succ_ans if not r["cited_min_evidence"]],
            "false_positive_unanswerable": [r["id"] for r in una if r["status"] == "SUCCESS"],
            "correct_abstention_unanswerable": f"{sum(r['status'] != 'SUCCESS' for r in una)}/{len(una)}",
            "answerable_citing_min_evidence": len(elig),
            "false_negative": [r["id"] for r in elig if r["status"] != "SUCCESS"],
            "false_negative_rate": round(sum(r["status"] != "SUCCESS" for r in elig) / len(elig), 3) if elig else None,
            "fn_causes": dict(Counter(c for r in elig if r["status"] != "SUCCESS" for c in r["dig_failed"]).most_common()),
            "dig_failures": dict(Counter(c for r in called for c in r["dig_failed"]).most_common()),
        }
        if name in ("S2_CIFRA_INVENTADA",):
            s["false_positive_adversarial"] = [r["id"] for r in rs if r["status"] == "SUCCESS"]
        if name == "S3_INFLUENCIA_SHADOW":
            inj = [r for r in rs if r["s3_injected"]]
            s["injected_cases"] = len(inj)
            s["false_positive_adversarial"] = [r["id"] for r in inj if r["status"] == "SUCCESS"]
        if name in ("S1_PRIMER_PASAJE", "S1B_MEJOR_PASAJE"):
            sw = {}
            for t in ("v1.2_unico_0.15", "v1.2_unico_0.20", "v1.3_0.15+2x0.30", "v1.3_0.15+2x0.25"):
                for split in ("dev", "validation", "test", "shadow", "all"):
                    sel = [r for r in rs if r["sweep_success"] and (split == "all" or r["split"] == split)]
                    if not sel:
                        continue
                    ok = lambda r: r["sweep_success"].get(t, False)
                    ans_ = [r for r in sel if r["answerable"]]
                    sw.setdefault(t, {})[split] = {
                        "success_answerable": sum(ok(r) for r in ans_),
                        "fp_unanswerable": [r["id"] for r in sel if not r["answerable"] and ok(r)],
                        "success_outside_min_evidence": sum(ok(r) and not r["cited_min_evidence"] for r in ans_),
                        "fn_citing_min_evidence": sum((not ok(r)) and r["cited_min_evidence"] for r in ans_),
                        "citing_min_evidence": sum(r["cited_min_evidence"] for r in ans_),
                    }
            s["threshold_sweep_DIG05"] = sw
        summary[name] = s
    after = {p: shaf(p) for p in before}
    report = {"note": "Generadores simulados (mock). Nivel D no verificado. No estima calidad de un LLM real.",
              "dig_version": __import__("decision_integrity").DIG_VERSION, "items": len(items),
              "elapsed_s": round(elapsed, 1), "summary": summary, "inputs_unchanged": before == after, "per_case": rows}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    compact = {k: {kk: (vv if not isinstance(vv, list) or len(vv) <= 12 else f"{len(vv)} casos (ver JSON)") for kk, vv in v.items()}
               for k, v in summary.items()}
    print(json.dumps({"dig_version": report["dig_version"], "items": len(items), "summary": compact,
                      "inputs_unchanged": report["inputs_unchanged"]}, ensure_ascii=False, indent=1))
    print("Resultados:", a.out)
    return 0 if report["inputs_unchanged"] else 3


if __name__ == "__main__":
    sys.exit(main())
