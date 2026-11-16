#!/usr/bin/env python3
"""Fase 11A - Diagnostico individual de abstenciones del DIG y CSV de revision arbitral.

Entradas (no se llama al LLM):
  --dev      informes de eval_llm_shadow sobre dev con detalle de comprobaciones (Fase 11)
  --phase10  informes reclasificados de la Fase 10 (dev y test_sealed; solo codigos de regla)
Casos: respuestas del LLM a consultas RESPONDIBLES que el DIG bloqueo (status != SUCCESS con
texto del modelo). Prioridad: los que citan literalmente la evidencia esperada.

La clasificacion automatica es una PROPUESTA (auto_*); la decision es del arbitro.
  BLOQUEO_CORRECTO           una regla bloquea por un motivo verificable (cifra ausente de todo
                             el material entregado, cita no literal, insuficiencia declarada...)
  FALSO_NEGATIVO_POTENCIAL   todas las reglas activadas tienen un motivo compatible con una
                             respuesta respaldada (cifra presente en el pasaje entregado pero no
                             en la cita, pertinencia lexica fallida con cita del ancla correcto...)
  REQUIERE_REVISION_ARBITRAL resto, o sin detalle disponible
Los casos de test_sealed se incluyen SOLO para revision humana (uso = SOLO_REVISION_HUMANA) y
no se usan para justificar cambios.
Uso: python scripts/diag_abstentions_f11.py --dev data/eval/fase11/llm_dev_r1.json \
        --phase10 data/eval/benchmark_v2/results/llm_shadow_dev_rescored.json \
                  data/eval/benchmark_v2/results/llm_shadow_test_sealed_rescored.json
"""
import argparse
import ast
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, "src")]
CORPUS = os.path.join(ROOT, "data/processed/rebuild_2026_08_corrected/passages_candidate.json")
BENCH = os.path.join(ROOT, "data/eval/benchmark_v2/benchmark_v2.jsonl")
OUT_DIR = os.path.join(ROOT, "data/eval/fase11")

from decision_integrity import numbers_in  # noqa: E402  (solo lectura de la normalizacion de cifras)
from experimental.dig_variants import formatting_artifacts  # noqa: E402
from experimental.benchmark_access import expand  # noqa: E402

BC, FN, RV = "BLOQUEO_CORRECTO", "FALSO_NEGATIVO_POTENCIAL", "REQUIERE_REVISION_ARBITRAL"
RECO = {
    "CIFRA_NO_RESPALDADA": "Mantener bloqueo: la cifra no aparece en el material SOR entregado.",
    "CIFRA_EN_PASAJE_NO_CITADA": ("No cambiar DIG-06. Causa de generacion: la cita literal omite la cifra presente en el "
                                  "pasaje. Evaluar instruccion de prompt o seleccion de cita (experimental)."),
    "CIFRA_DE_LA_CONSULTA": "Revisar: la cifra procede de la propia consulta; posible FN de DIG-06 (variante experimental).",
    "ARTEFACTO_DE_FORMATO": ("FN de DIG-06/08 por formato: la 'cifra' es la edicion (14 agosto 2026 / SOR 2026), un "
                             "identificador SOR con guion Unicode, numeracion de lista o etiqueta de seccion. Candidato a "
                             "variante experimental de normalizacion (dig_variants), a evaluar offline."),
    "SHADOW_TERMINO_EN_IDIOMA_DE_RESPUESTA": ("Arbitro: palabra comun en espanol presente en SHADOW (espanol) y ausente del "
                                              "SOR (ingles). Posible FN sistematico de DIG-08 en respuestas en espanol."),
    "TERMINO_DE_CONSULTA_AUSENTE_DEL_SOR": ("Arbitro: DIG-11 bloquea por una palabra de la consulta que no esta en el SOR "
                                            "(vocabulario del usuario). Decidir si la regla es demasiado estricta."),
    "TERMINO_TECNICO_NO_CITADO": "Arbitro: termino tecnico de la respuesta sin respaldo en citas; verificar si es afirmacion adicional.",
    "CIFRA_DERIVADA": "Arbitro: la cifra parece calculada o convertida; decidir si es respaldo admisible.",
    "PERTINENCIA_LEXICA_CON_ANCLA": ("Revisar DIG-05: la cita es del ancla esperada pero no comparte terminos distintivos "
                                     "con la consulta (traduccion / sinonimia). Candidato a variante experimental."),
    "PERTINENCIA_SIN_ANCLA": "Mantener bloqueo: la cita no corresponde a la evidencia esperada.",
    "SHADOW_CIFRA": "Mantener bloqueo: cifra presente solo en documentacion SHADOW.",
    "SHADOW_TERMINOS": "Arbitro: terminos solo presentes en SHADOW; verificar si son vocabulario de la respuesta o influencia real.",
    "EXCEPCION_REQUERIDA_NO_CITADA": "Mantener bloqueo: la excepcion exigida por el benchmark no se cito.",
    "EXCEPCION_CERCANA_NO_CITADA": "Arbitro: decidir si la excepcion cercana es pertinente a la consulta.",
    "CITA_NO_LITERAL": "Mantener bloqueo (contrato de cita literal). Causa de generacion.",
    "INSUFICIENCIA_DECLARADA": "Mantener: el propio modelo declaro evidencia insuficiente o conflicto.",
    "JSON_INVALIDO": "Mantener: salida no estructurada. Causa de generacion.",
    "CITAS_SIN_LITERAL": "Mantener (contrato). Causa de generacion.",
    "VALIDADOR_DE_CITAS": ("Mantener: la respuesta no cito un pasaje primario entregado (validador de nivel A, previo al DIG). "
                           "Causa de generacion / formato del proveedor."),
    "OTRA": "Arbitro: revisar el detalle de la regla.",
    "SIN_DETALLE": "Arbitro: corrida de Fase 10 sin detalle; revisar con la corrida de Fase 11 o manualmente.",
}


def parse_list(detail, key):
    m = re.search(re.escape(key) + r"=(\[[^\]]*\])", detail or "")
    if not m:
        return []
    try:
        return list(ast.literal_eval(m.group(1)))
    except Exception:
        return re.findall(r"'([^']*)'", m.group(1))


def classify_check(code, detail, row, item, ptext):
    """-> (clase, subtipo, motivo tecnico)"""
    quotes_ok = bool(row.get("quotes_hit_evidence"))
    answer = " ".join(str((row.get("llm_json") or {}).get(k) or "") for k in ("summary", "normative_basis", "conditions_and_exceptions"))
    if code.startswith("DIG-06"):
        missing = parse_list(detail, "cifras_sin_respaldo")
        art = set(formatting_artifacts(answer, missing)) if answer.strip() else set()
        delivered = " ".join(ptext.get(b["passage_id"], "") for b in row.get("bundle_detail") or [])
        dn, qn = numbers_in(delivered), numbers_in(item["text"] + " " + (row.get("translation") or ""))
        subs = []
        for n in missing:
            if n in art:
                subs.append("ARTEFACTO_DE_FORMATO")
            elif n in qn:
                subs.append("CIFRA_DE_LA_CONSULTA")
            elif n in dn:
                subs.append("CIFRA_EN_PASAJE_NO_CITADA")
            elif "." in n:
                subs.append("CIFRA_DERIVADA")
            else:
                subs.append("CIFRA_NO_RESPALDADA")
        sub = ("CIFRA_NO_RESPALDADA" if "CIFRA_NO_RESPALDADA" in subs else
               "CIFRA_DERIVADA" if "CIFRA_DERIVADA" in subs else
               "CIFRA_EN_PASAJE_NO_CITADA" if "CIFRA_EN_PASAJE_NO_CITADA" in subs else
               "CIFRA_DE_LA_CONSULTA" if "CIFRA_DE_LA_CONSULTA" in subs else "ARTEFACTO_DE_FORMATO")
        cls = {"CIFRA_NO_RESPALDADA": BC, "CIFRA_DERIVADA": RV}.get(sub, FN)
        return cls, sub, f"cifras sin respaldo en la cita: {missing} -> {dict(zip(missing, subs))}"
    if code.startswith("DIG-05"):
        no_pert = parse_list(detail, "pasajes_citados_sin_cita_pertinente")
        sub = "PERTINENCIA_LEXICA_CON_ANCLA" if quotes_ok else "PERTINENCIA_SIN_ANCLA"
        return (FN if quotes_ok else BC), sub, f"cita sin termino distintivo de la consulta en {no_pert}"
    if code.startswith("DIG-08"):
        nums = parse_list(detail, "cifras")
        terms = parse_list(detail, "terminos")
        real_nums = [n for n in nums if n not in set(formatting_artifacts(answer, nums))] if answer.strip() else nums
        if real_nums:
            return BC, "SHADOW_CIFRA", f"cifras solo en SHADOW: {real_nums}"
        if nums and not terms:
            return FN, "ARTEFACTO_DE_FORMATO", f"'cifras' solo en SHADOW que son edicion/formato: {nums}"
        ans_lang = "es" if len(re.findall(r"\b(?:el|los|las|que|para|del|una|con)\b", answer.lower())) >= 3 else row.get("language")
        if ans_lang != "en" and terms:
            return RV, "SHADOW_TERMINO_EN_IDIOMA_DE_RESPUESTA", f"terminos solo en SHADOW: {terms[:10]} (respuesta en {ans_lang})"
        return RV, "SHADOW_TERMINOS", f"terminos solo en SHADOW: {terms[:10]}"
    if code.startswith("DIG-09"):
        missing = re.findall(r"'([^']{10,})'", detail or "")
        req = [norm_ws(x["snippet"])[:60] for x in item.get("exceptions_to_preserve") or []]
        required = any(r[:40].lower() in (detail or "").lower() for r in req)
        return ((BC, "EXCEPCION_REQUERIDA_NO_CITADA", f"excepcion exigida no citada: {missing[:2]}") if required else
                (RV, "EXCEPCION_CERCANA_NO_CITADA", f"excepcion a +-2 frases no citada: {missing[:2]}"))
    if code.startswith("DIG-03"):
        return BC, "CITA_NO_LITERAL", f"citas no localizadas literalmente: {parse_list(detail, 'no_literales')[:2]}"
    if code.startswith("DIG-01"):
        return BC, "INSUFICIENCIA_DECLARADA", detail
    if code.startswith("DIG-00"):
        return BC, "JSON_INVALIDO", detail
    if code.startswith("DIG-02"):
        return BC, "CITAS_SIN_LITERAL", detail
    if code.startswith("DIG-11"):
        return RV, "TERMINO_DE_CONSULTA_AUSENTE_DEL_SOR", detail
    if code.startswith("DIG-07"):
        return RV, "TERMINO_TECNICO_NO_CITADO", detail
    return RV, "OTRA", detail


def norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def case_rows(rep, source, items, ptext, detailed):
    out = []
    for run in rep["per_run"]:
        for r in run:
            if r["expected_behavior"] != "RESPONDER" or r["status"] == "SUCCESS" or not r.get("llm_text_present"):
                continue
            it = items[r["id"]]
            checks = r.get("dig_checks") if detailed else None
            per = []
            if checks:
                for c in checks:
                    per.append((c["code"],) + classify_check(c["code"], c["detail"], r, it, ptext))
            elif detailed and not r.get("dig_decision"):
                # bloqueo previo al DIG: validador de citas de nivel A (_validate_llm_citations)
                per = [("VALIDADOR_CITAS_NIVEL_A", BC, "VALIDADOR_DE_CITAS",
                        f"{(r.get('abstain_reason_text') or '')[:200]} provider={r.get('provider')}")]
            else:
                per = [(code, RV, "SIN_DETALLE", "corrida sin detalle de comprobaciones") for code in (r.get("dig_failed_checks") or [])]
            classes = {p[1] for p in per}
            case_cls = BC if BC in classes else (FN if classes == {FN} else RV)
            in_b = all(expand(a["passage_ids"]) & set(r.get("bundle") or []) for a in it["minimum_evidence"])
            ev = ("SI" if in_b and r.get("quotes_hit_all_evidence") else
                  "PARCIAL" if in_b and r.get("quotes_hit_evidence") else
                  "EN_BUNDLE_NO_CITADA" if in_b else "NO_RECUPERADA")
            uso = "SOLO_REVISION_HUMANA" if it["split"] == "test_sealed" else "DIAGNOSTICO_DEV"
            out.append({
                "case_id": f"{source}:{r['id']}:run{r.get('run', 0)}", "source": source, "split": it["split"], "uso": uso,
                "query_id": r["id"], "run": r.get("run", 0), "language": r["language"], "category": r["category"],
                "query": it["text"], "translation": r.get("translation") or "",
                "outcome_f10": r.get("outcome"), "priority": "ALTA" if r.get("outcome") == "ABSTENCION_CON_CITA_CORRECTA" else "MEDIA",
                "expected_evidence": " || ".join(f"p{a['page']} {a['snippet'][:90]}" for a in it["minimum_evidence"]),
                "retrieved_evidence": " ".join(f"p{b['page']}" for b in (r.get("bundle_detail") or [])) or " ".join(r.get("bundle") or []),
                "quotes": " || ".join((q.get("quote") or "")[:120] for q in (r.get("quotes") or [])),
                "dig_rules": ";".join(p[0] for p in per),
                "technical_reason": " | ".join(f"{p[0]}: {p[3]}" for p in per)[:1500],
                "evidence_sufficient_auto": ev,
                "auto_classification": case_cls,
                "auto_subtypes": ";".join(f"{p[0]}={p[2]}" for p in per),
                "recommendation": " / ".join(dict.fromkeys(RECO.get(p[2], RECO["OTRA"]) for p in per)),
                "reviewer": "", "review_date": "", "verdict": "", "notes": "",
            })
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", nargs="*", default=[])
    ap.add_argument("--phase10", nargs="*", default=[])
    ap.add_argument("--out-dir", default=OUT_DIR)
    a = ap.parse_args(argv)
    items = {json.loads(l)["id"]: json.loads(l) for l in open(BENCH, encoding="utf-8") if l.strip()}
    ptext = {p["passage_id"]: p["text_original"] for p in json.load(open(CORPUS, encoding="utf-8"))}
    rows = []
    for p in a.dev:
        rows += case_rows(json.load(open(p, encoding="utf-8")), "F11_" + os.path.splitext(os.path.basename(p))[0], items, ptext, True)
    for p in a.phase10:
        rows += case_rows(json.load(open(p, encoding="utf-8")), "F10_" + os.path.splitext(os.path.basename(p))[0], items, ptext, False)
    os.makedirs(a.out_dir, exist_ok=True)
    cols = list(rows[0].keys()) if rows else ["case_id"]
    with open(os.path.join(a.out_dir, "arbitral_review_abstentions.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    det = [r for r in rows if r["source"].startswith("F11_")]
    summ = {
        "cases_total": len(rows), "by_source": dict(Counter(r["source"] for r in rows)),
        "by_uso": dict(Counter(r["uso"] for r in rows)),
        "f11_dev_detailed": {
            "cases": len(det), "priority_alta": sum(r["priority"] == "ALTA" for r in det),
            "auto_classification": dict(Counter(r["auto_classification"] for r in det)),
            "auto_classification_priority_alta": dict(Counter(r["auto_classification"] for r in det if r["priority"] == "ALTA")),
            "rule_subtypes": dict(Counter(s for r in det for s in r["auto_subtypes"].split(";") if s)),
            "evidence_sufficient_auto": dict(Counter(r["evidence_sufficient_auto"] for r in det)),
            "rules": dict(Counter(x for r in det for x in r["dig_rules"].split(";") if x)),
        },
        "phase10_rules": dict(Counter(x for r in rows if r["source"].startswith("F10_") for x in r["dig_rules"].split(";") if x)),
        "note": "auto_* son propuestas automaticas PENDIENTES de revision arbitral; no constituyen veredicto.",
    }
    with open(os.path.join(a.out_dir, "diag_abstentions_summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summ, fh, ensure_ascii=False, indent=2)
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
