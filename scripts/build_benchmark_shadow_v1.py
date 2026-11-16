"""Fase 8 (ampliacion SHADOW) - Benchmark de recuperacion auxiliar (benchmark_shadow_v1).

Separado de benchmark_v1 (que no se modifica). Cada item declara una CLASE DE EVIDENCIA:
  PRIMARIA_CON_AUXILIAR         el SOR fundamenta; el fragmento SHADOW aporta contexto util
  SOLO_AUXILIAR_SIN_PRIMARIA    el SOR no contiene la respuesta; SHADOW es informativo y NO puede
                                fundamentar una respuesta normativa (abstencion normativa esperada)
  AUXILIAR_NO_DEBE_FUNDAMENTAR  existe un fragmento SHADOW aparentemente pertinente, pero el SOR
                                rige; el fragmento no debe usarse como fundamento (incluye casos en
                                que el texto SHADOW difiere literalmente del SOR)
  SIN_EVIDENCIA_SUFICIENTE      ni SOR ni SHADOW contienen evidencia
Anclas SOR: fragmentos literales verificados con build_benchmark_v1.resolve_anchor.
Anclas SHADOW: fragmentos literales verificados contra content_text del chunk.
Politica de uso auxiliar en todos los items: CONTEXTO_NO_DECISORIO.
Sin revision arbitral: human_review_status = PENDIENTE_REVISION_ARBITRAL.
Uso: python scripts/build_benchmark_shadow_v1.py [--check | --overwrite]
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_benchmark_v1 as bb  # noqa: E402

VERSION = "benchmark_shadow_v1.0.0"
ROOT = bb.ROOT
OUT_REL = "data/eval/benchmark_shadow_v1"
SHADOW_REL = "data/corpus_multisource/processed/multisource_passages.json"
PCA, SAX, NOF, SIN = "PRIMARIA_CON_AUXILIAR", "SOLO_AUXILIAR_SIN_PRIMARIA", "AUXILIAR_NO_DEBE_FUNDAMENTAR", "SIN_EVIDENCIA_SUFICIENTE"
A = bb.A
ITEMS = []


def S(qid, lang, cls, text, primary=(), aux=(), forbidden_aux=(), why=""):
    """aux / forbidden_aux: (chunk_id, literal_snippet)."""
    ITEMS.append({"id": qid, "language": lang, "evidence_class": cls, "text": text, "primary": list(primary),
                  "aux": list(aux), "forbidden_aux": list(forbidden_aux), "justification": why})


S("SH-001", "es", PCA, "¿Qué sanciones pueden imponer los órganos disciplinarios de la IJF?",
  [A(14, "1.2.1", "The IJF Executive Committee has the authority to establish a Disciplinary Committee")],
  [("CHK-KUN-DIS-001-002", "The Disciplinary Bodies may impose the following sanctions")], why="SOR establece el comite; el Codigo Disciplinario detalla sanciones.")
S("SH-002", "en", PCA, "Is betting on IJF competitions prohibited?",
  [A(15, "1.2.2", "The IJF has rules dedicated to sports integrity")],
  [("CHK-KUN-ETH-001-002", "strictly prohibited from participating in, supporting or promoting any form of betting")], why="Integridad en SOR 1.2.2; detalle en Codigo de Etica.")
S("SH-003", "es", PCA, "¿Qué política aplica la IJF frente al acoso y el abuso?",
  [A(16, "1.2.3", "The IJF Policy for Safeguarding Athletes and Other Participants from Harassment and Abuse applies to all persons affiliated with the IJF")],
  [("CHK-KUN-ETH-001-003", "Zero tolerance applies to any form of harassment")], why="SOR 1.2.3 remite a la politica; contexto etico auxiliar.")
S("SH-004", "en", PCA, "How must athletes behave towards opponents and referees at IJF events?",
  [A(14, "1.1.1", "Unacceptable behaviour, violence or aggression will not be tolerated")],
  [("CHK-KUN-ETH-001-001", "must be spoken to calmly and with respect")], why="SOR 1.1.1 + principio etico.")
S("SH-005", "es", PCA, "¿Cuántos segundos de inmovilización se necesitan para obtener yuko?",
  [A(152, "Article 7", "Yuko: 5 seconds or more but less than 10 seconds (5-9 seconds)")],
  [("CHK-KUN-NEW-003-001", "If an athlete holds osaekomi-waza for 5 to 9 seconds")], why="El comunicado esta subsumido en el SOR (Article 7/15).")
S("SH-006", "en", PCA, "Do yuko scores accumulate into a waza-ari?",
  [A(169, "Article 15", "Yuko scores are counted (1, 2, 3, etc.) but they")],
  [("CHK-KUN-NEW-003-001", "yuko scores are counted but do not accumulate toward a waza-ari")], why="SOR Article 15; comunicado subsumido.")
S("SH-007", "en", PCA, "When is a transition from standing to ne-waza considered valid?",
  [A(155, "Article 10", "Transition from tachi-waza to ne-waza are considered valid if tori or uke makes a real attack or a counterattack")],
  [("CHK-KUN-PPT-002-001", "Groundwork (ne-waza) transition is allowed if one competitor immediately initiates a technique")], why="Article 10 (metadatos de pagina inexactos) + interpretacion de seminario.")
S("SH-008", "es", PCA, "¿Se sanciona arrastrar al rival al suelo sin intentar una proyección?",
  [A(177, "Article 18.1.1", "to pull the opponent down to start ne-waza")],
  [("CHK-KUN-PPT-002-002", "Pulling down the opponent directly to groundwork (ne-waza) without an active throw attempt is penalized with Shido")], why="SOR 18.1.1 + criterio de seminario.")
S("SH-009", "es", SAX, "¿Cuántas plazas tiene el judo en los Juegos Olímpicos LA28?",
  aux=[("CHK-KUN-QSY-001-001", "Total quota places for judo at the LA28 Olympic Games is 342 athletes")], why="El SOR no regula el sistema de clasificacion LA28.")
S("SH-010", "en", SAX, "How many athletes per weight category qualify directly for LA28 through the world ranking list?",
  aux=[("CHK-KUN-QSY-001-002", "The top 17 highest ranked athletes per individual weight category")], why="Fuera del SOR; solo sistema de clasificacion.")
S("SH-011", "es", SAX, "¿Cuál es el plazo de prescripción de las infracciones disciplinarias en la IJF?",
  aux=[("CHK-KUN-DIS-001-003", "if five (5) years have elapsed since the disciplinary offence was committed")], why="Regulado en el Codigo Disciplinario, no en el SOR.")
S("SH-012", "en", SAX, "When does the LA28 Olympic qualification period run?",
  aux=[("CHK-KUN-QSY-001-004", "The Olympic qualification period runs from 15th June 2026 to 12th June 2028")], why="Fuera del SOR.")
S("SH-013", "es", SAX, "¿Qué requisitos debe cumplir un Comité Olímpico Nacional para inscribir un equipo mixto en LA28?",
  aux=[("CHK-KUN-QSY-001-003", "are eligible to enter a team in the Olympic Mixed Team competition")], why="El SOR define categorias del equipo mixto olimpico (2.2.3) pero no la elegibilidad del CON.")
S("SH-014", "en", SAX, "Are the IJF refereeing rules frozen for the LA28 Olympic cycle?",
  aux=[("CHK-KUN-NEW-001-001", "The IJF refereeing rules are locked in for the duration of the Olympic qualification cycle")], why="Comunicado institucional; no regla SOR.")
S("SH-015", "es", NOF, "¿Cuánto tiempo puede mantenerse el kumikata sin atacar?",
  [A(177, "Article 18.1.1", "The time between conventional kumikata and making an attack is 45 seconds if there is a positive progression")],
  forbidden_aux=[("CHK-KUN-NEW-001-003", "A 30-second time limit for kumi-kata")],
  why="Discrepancia literal observada (SOR 45 s / fragmento 30 s); el SOR rige. Pendiente de revision arbitral.")
S("SH-016", "en", NOF, "Is reverse seoi-nage allowed?",
  [A(189, "Article 18.1.4", "In cadet events there will be no score for reverse seoi-nage")],
  forbidden_aux=[("CHK-KUN-NEW-001-002", "Reverse seoi-nage is re-allowed for senior athletes")], why="La regla aplicable es la del SOR (cadetes); el comunicado no la sustituye.")
S("SH-017", "es", NOF, "¿Se sanciona el contacto de la cabeza con el tatami durante una proyección?",
  [A(190, "Article 18.2.1", "Techniques using head diving are dangerous and will be penalised with hansoku-make")],
  forbidden_aux=[("CHK-KUN-NEW-003-003", "Involuntary head contact during a transition or throw is not subject to penalization")],
  why="El fragmento formula una excepcion que no se localiza literalmente en el SOR; no puede fundamentar.")
S("SH-018", "en", NOF, "Can the +5% weight tolerance be used to compete in a lower mixed team weight category?",
  [A(82, "6.4.2", "The +5% weight tolerance cannot be used by an athlete wishing to compete in a lower Mixed Team weight category")],
  forbidden_aux=[("CHK-KUN-QSY-001-004", "A 5% weight tolerance applies to the mixed team event")], why="SOR 6.4.2 rige; el fragmento LA28 es contexto olimpico.")
S("SH-019", "es", NOF, "¿Con qué se sanciona la pasividad en combate?",
  [A(177, "Article 18.1.1", "Negative positions, against the fighting spirit, will be penalised by shido")],
  forbidden_aux=[("CHK-KUN-NEW-003-002", "When evaluating passivity, referees will consider attacks in both tachi-waza")], why="La sancion esta en el SOR; el fragmento no fija sancion.")
S("SH-020", "es", NOF, "¿Puede el Código Disciplinario imponer hansoku-make durante un combate?",
  [A(190, "Article 18.2.2", "If this type of hansoku-make is awarded the athlete CANNOT continue in the competition")],
  forbidden_aux=[("CHK-KUN-DIS-001-002", "The Disciplinary Bodies may impose the following sanctions")], why="Hansoku-make es sancion arbitral del SOR; las sanciones disciplinarias son otro ambito.")
for qid, lang, text in [("SH-021", "es", "¿Cuántas plazas tendrá el judo en los Juegos Olímpicos de Brisbane 2032?"),
                        ("SH-022", "en", "What is the exact fine amount for match fixing?"),
                        ("SH-023", "es", "¿Qué patrocinadores oficiales tiene el Grand Slam de Ulaanbaatar?"),
                        ("SH-024", "en", "What daily fee is paid to referees at a Grand Prix?")]:
    S(qid, lang, SIN, text, why="Ni el SOR ni los fragmentos SHADOW vigentes contienen esta informacion (verificar en revision).")


def build(passages, sor_raw, shadow_raw):
    chunks = {c["chunk_id"]: c for c in json.loads(shadow_raw.decode("utf-8"))}
    pages = defaultdict(list)
    for p in passages:
        pages[p["pdf_page_index"]].append(p)
    errors, recs = [], []
    for it in ITEMS:
        prim = [bb.resolve_anchor(a, pages) for a in it["primary"]]
        def aux_check(lst):
            out = []
            for cid, snip in lst:
                c = chunks.get(cid)
                ok = bool(c) and bb.norm_ws(snip) in bb.norm_ws(c["content_text"])
                if not ok:
                    errors.append(f"{it['id']}: ancla SHADOW no verificada {cid}")
                out.append({"chunk_id": cid, "document_id": c["document_id"] if c else None, "snippet": snip,
                            "status": "VERIFICADA_TEXTUALMENTE" if ok else "PENDIENTE"})
            return out
        aux, forb = aux_check(it["aux"]), aux_check(it["forbidden_aux"])
        for r in prim:
            if r["status"] == "PENDIENTE":
                errors.append(f"{it['id']}: ancla SOR no verificada p{r['page']}")
        status = "PENDIENTE" if any(x["status"] == "PENDIENTE" for x in prim + aux + forb) else (
            "VERIFICADA_TEXTUALMENTE_CON_ARTICULO_PENDIENTE" if any(x["status"] != "VERIFICADA_TEXTUALMENTE" for x in prim) else "VERIFICADA_TEXTUALMENTE")
        if it["evidence_class"] == SIN:
            status = "SIN_EVIDENCIA_ESPERADA_NO_VERIFICABLE_EXHAUSTIVAMENTE"
        recs.append({"id": it["id"], "benchmark_version": VERSION, "text": it["text"], "language": it["language"],
                     "evidence_class": it["evidence_class"],
                     "expected_primary": prim, "expected_primary_passage_ids": sorted({p for r in prim for p in r["passage_ids"]}),
                     "expected_auxiliary": aux, "forbidden_as_basis": forb,
                     "auxiliary_use_policy": "CONTEXTO_NO_DECISORIO",
                     "normative_answer_expected": it["evidence_class"] in (PCA, NOF),
                     "expected_normative_basis": "SOR_PRIMARIO" if it["evidence_class"] in (PCA, NOF) else "NINGUNO (abstencion normativa)",
                     "justification": it["justification"], "annotation_source": bb.SOURCE, "annotation_status": status,
                     "human_review_status": bb.HUMAN, "certified_by_referees": False})
    recs.sort(key=lambda r: r["id"])
    counts = {"total": len(recs), "by_evidence_class": dict(sorted(Counter(r["evidence_class"] for r in recs).items())),
              "by_language": dict(sorted(Counter(r["language"] for r in recs).items())),
              "by_annotation_status": dict(sorted(Counter(r["annotation_status"] for r in recs).items())),
              "shadow_chunks_covered": sorted({a["chunk_id"] for r in recs for a in r["expected_auxiliary"] + r["forbidden_as_basis"]}),
              "shadow_chunks_total": len(chunks)}
    manifest = {"benchmark_version": VERSION, "sor_corpus_sha256": hashlib.sha256(sor_raw).hexdigest(),
                "shadow_passages_sha256": hashlib.sha256(shadow_raw).hexdigest(), "counts": counts, "build_errors": errors,
                "policy": {"auxiliary_use": "CONTEXTO_NO_DECISORIO en todos los items", "human_review_status": bb.HUMAN,
                           "certified_by_referees": False, "split": "conjunto unico de evaluacion; no usar para ajustar"}}
    files = {"benchmark_shadow_v1.jsonl": "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in recs),
             "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"}
    files["hashes.json"] = json.dumps({k: bb.sha(v) for k, v in sorted(files.items())}, indent=2, sort_keys=True) + "\n"
    return files, recs, errors, counts


def load(root=ROOT):
    with open(os.path.join(root, bb.CORPUS_REL), "rb") as fh:
        sor_raw = fh.read()
    with open(os.path.join(root, SHADOW_REL), "rb") as fh:
        shadow_raw = fh.read()
    return json.loads(sor_raw.decode("utf-8")), sor_raw, shadow_raw


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    files, recs, errors, counts = build(*load())
    if a.check:
        diffs = [n for n, c in files.items() if not os.path.exists(os.path.join(a.out, n))
                 or open(os.path.join(a.out, n), encoding="utf-8").read().replace("\r\n", "\n") != c]
        print("REPRODUCIBLE" if not diffs else f"NO REPRODUCIBLE: {diffs}")
        return 0 if not diffs else 1
    if os.path.isdir(a.out) and os.listdir(a.out) and not a.overwrite:
        print(f"ERROR: {a.out} ya existe; use --check o --overwrite", file=sys.stderr)
        return 2
    os.makedirs(a.out, exist_ok=True)
    for n, c in files.items():
        with open(os.path.join(a.out, n), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(c)
    print(json.dumps(counts, ensure_ascii=False, indent=1))
    for e in errors:
        print("ERROR:", e)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
