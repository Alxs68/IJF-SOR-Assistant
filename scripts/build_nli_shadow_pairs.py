#!/usr/bin/env python3
"""Fase 10.2 - Dataset derivado de pares (premisa, hipotesis) para evaluar NLI en SHADOW.

Fuente: benchmark_v2 (evidencia minima y distractores de ambito ya verificados literalmente).
  premisa  = ventana del texto de la pagina SOR alrededor del fragmento literal
             (350 caracteres antes, 200 despues, ajustada a limite de palabra)
  hipotesis= afirmacion redactada para el item (CLAIMS), en el idioma de la consulta

Tipos de par y etiqueta binaria esperada (SUPPORTED / NOT_SUPPORTED):
  SUPPORT         premisa correcta   + afirmacion correcta          -> SUPPORTED
  SCOPE_PREMISE   premisa distractor + afirmacion correcta          -> NOT_SUPPORTED  (evidencia literal de otro ambito)
  SCOPE_CLAIM     premisa correcta   + afirmacion de ambito erroneo -> NOT_SUPPORTED
  NUMBER          premisa correcta   + afirmacion con cifras alteradas automaticamente -> NOT_SUPPORTED
Los pares SCOPE_PREMISE cuya ventana solapa el fragmento correcto se excluyen
(etiqueta no determinable) y se cuentan en el manifiesto.

Las afirmaciones son material de EVALUACION (no respuestas del sistema) y estan
PENDING_EXPERT_REVIEW. Cada par hereda el split de su item (dev / test_sealed).
Solo stdlib. Uso: python scripts/build_nli_shadow_pairs.py [--overwrite | --check]
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "nli_shadow_pairs_v1.0.0"
CORPUS_REL = "data/processed/rebuild_2026_08_corrected/passages_candidate.json"
BENCH_REL = "data/eval/benchmark_v2/benchmark_v2.jsonl"
OUT_REL = "data/eval/nli_shadow_v1"
BEFORE, AFTER = 350, 200

# id -> (afirmacion correcta, afirmacion con ambito/valor de otro ambito o None)
CLAIMS = {
    "B2-SCO-001": ("For veterans in the M7 age division and over, a contest lasts two and a half minutes.",
                   "For senior athletes, a contest lasts two and a half minutes."),
    "B2-SCO-002": ("En las competiciones de la IJF, un combate de cadetes dura 4 minutos de tiempo real.",
                   "En las competiciones de la IJF, un combate de cadetes dura tres minutos."),
    "B2-SCO-003": ("For a Masters event, the draw takes place at 14:00 local time the day before the competition.",
                   "For a Masters event, the draw takes place at 19:00 the day before the competition."),
    "B2-SCO-004": ("En los campeonatos de veteranos, el sorteo se realiza a las 19:00 horas del día anterior a la competición.",
                   "En los campeonatos de veteranos, el sorteo se realiza a las 14:00 hora local del día anterior."),
    "B2-SCO-005": ("At a Grand Prix, up to the top eight athletes in each weight category are seeded according to the IJF World Ranking List.",
                   "At a Grand Prix, there is no seeding."),
    "B2-SCO-006": ("En los campeonatos de veteranos no hay cabezas de serie.",
                   "En los campeonatos de veteranos se siembran los ocho mejores de cada categoría según el ranking mundial."),
    "B2-SCO-007": ("In kata competitions, the top six pairs on the ranking list are seeded.",
                   "In kata competitions, the top eight pairs are seeded based on the IJF World Ranking List."),
    "B2-SCO-008": ("En los Juegos Olímpicos, el sembrado se basa en el ranking mundial senior del periodo de clasificación olímpica.",
                   "En los Juegos Olímpicos no hay cabezas de serie."),
    "B2-SCO-009": ("There is no random weigh-in at IJF mixed team events.",
                   "At IJF mixed team events, the random weigh-in opens one hour before the start of the competition each day."),
    "B2-SCO-010": ("Los veteranos no tienen pesaje aleatorio.",
                   "Para los veteranos, el pesaje aleatorio abre una hora antes del inicio de la competición."),
    "B2-SCO-011": ("Veteran athletes must compete in a white or blue IJF approved judogi.",
                   "Veteran athletes must wear a white judogi with a black belt and a backnumber."),
    "B2-SCO-012": ("En kata los participantes deben llevar judogi blanco, cinturón negro y dorsal.",
                   "En kata los participantes pueden competir con judogi blanco o azul."),
    "B2-SCO-013": ("At a World Kata Championships, the competition area is 10 m x 10 m.",
                   "At a World Kata Championships, the competition area is 8 m x 8 m."),
    "B2-SCO-014": ("En los eventos de kata que no son campeonatos del mundo, el área de competición mide 8 m x 8 m.",
                   "En los eventos de kata que no son campeonatos del mundo, el área de competición mide 10 m x 10 m."),
    "B2-SCO-015": ("In a veterans category with only one athlete, no medal is awarded.",
                   "In a veterans category with only one athlete, medals are awarded according to standings regardless of the number of competitors."),
    "B2-SCO-016": ("En kata las medallas se entregan según la clasificación, sin importar el número de parejas.",
                   "En kata, si solo participa una pareja no se entrega ninguna medalla."),
    "B2-SCO-017": ("To take part in veterans competitions, athletes must be at least 30 years of age.",
                   "To take part in veterans competitions, athletes must be at least 15 years of age."),
    "B2-SCO-018": ("Para el examen de árbitro internacional de la IJF los límites de edad son de 30 a 50 años.",
                   "Para el examen de árbitro internacional de la IJF los límites de edad son de 25 a 45 años."),
    "B2-SCO-019": ("Los cadetes tienen una tolerancia adicional de 0,2 kg en el pesaje.",
                   "Los cadetes tienen una tolerancia del 5% en el pesaje."),
    "B2-SCO-020": ("Senior athletes get no additional weight tolerance at the official weigh-in of an individual event.",
                   "Senior athletes get an additional 0.2 kg weight tolerance at the official weigh-in."),
    "B2-SCO-021": ("A female team in a team event consists of up to five athletes.",
                   "A female team in a team event consists of six athletes, three women and three men."),
    "B2-SCO-022": ("Un equipo mixto puede tener hasta seis reservas, tres mujeres y tres hombres.",
                   "Un equipo mixto puede tener como máximo cinco reservas."),
    "B2-SCO-023": ("Points for the IJF Juniors World Ranking List are earned at Continental Cups Juniors, Continental Championships Juniors, Grand Prix Juniors and World Championships Juniors.",
                   "Points for the IJF Juniors World Ranking List are earned at IJF World Judo Tour events for seniors."),
    "B2-SCO-024": ("Una pareja de kata puede sumar puntos en Open Continentales, Campeonatos Continentales, Kata World Series y Campeonatos del Mundo de Kata.",
                   "Una pareja de kata suma puntos en los eventos senior del World Judo Tour."),
    "B2-SCO-025": ("If a minor injury occurs during a kata performance, the performance is stopped according to the decision of the judges.",
                   "If a minor injury occurs during a kata performance, the athlete may treat it himself and continue without stopping."),
    "B2-SCO-026": ("Durante un combate, una lesión leve puede ser tratada por el propio atleta.",
                   "Durante un combate, ante una lesión leve se detiene la actuación y la pareja la repite al final."),
    "B2-SCO-027": ("In a veterans category with four entries, a round robin system is used.",
                   "In a veterans category with four entries, a double repechage system is used."),
    "B2-SCO-028": ("Con dos participantes en veteranos se disputan dos combates y, si quedan 1-1, un tercer combate decide.", None),
    "B2-SCO-029": ("When the mixed team event follows an individual competition, the team composition must be confirmed by 13:00 local time on the day before the mixed team competition.",
                   "When the mixed team event follows an individual competition, the team composition must be confirmed by 14:00 local time the day before the competition."),
    "B2-SCO-030": ("A U21 kata pair can perform nage-no-kata, katame-no-kata and ju-no-kata.",
                   "A U21 kata pair can perform Kodokan goshin-jutsu and kime-no-kata."),
    "B2-CAT-001": ("Para un atleta de -66 kg, la falda de la chaqueta debe medir como mínimo 20 cm.",
                   "Para un atleta de -66 kg, la falda de la chaqueta debe medir como mínimo 25 cm."),
    "B2-CAT-002": ("The manufacturer's logo on the belt can be at most 9 cm2.",
                   "The manufacturer's logo on the belt can be at most 30 cm2."),
    "B2-CAT-003": ("Una pareja U18 de kata puede usar un cinturón verde sin etiqueta IJF.",
                   "Una pareja U18 de kata debe usar obligatoriamente cinturón negro."),
    "B2-CAT-004": ("Senior kata participants must hold at least 1st dan.",
                   "Senior kata participants only need to hold 1st kyu."),
    "B2-CAT-005": ("The men's -73 kg category of the Olympic mixed team groups the 60 kg, 66 kg and 73 kg categories.",
                   "The men's -73 kg category of the Olympic mixed team groups the 73 kg, 81 kg and 90 kg categories."),
    "B2-CAT-006": ("En el equipo mixto no se aplica ninguna tolerancia a las categorías de más (+).",
                   "En el equipo mixto se aplica una tolerancia del 5% a las categorías de más (+)."),
    "B2-CAT-007": ("At a Grand Prix Cadets, only the two best domestic athletes per weight category can obtain Cadets WRL points.",
                   "At a Grand Prix Cadets, the ten best domestic male and ten best domestic female athletes can obtain Cadets WRL points."),
    "B2-EXC-001": ("After confirmation, the mixed team list can be updated up to one hour after the end of the final block, only for the athletes competing on the last day.", None),
    "B2-EXC-002": ("Si el rival no puede continuar por haber perdido una lentilla, se concede kiken-gachi.", None),
    "B2-EXC-003": ("In exceptional cases, the IJF can inscribe an athlete into an IJF event to protect the athlete's career.", None),
    "B2-EXC-004": ("Si los médicos discrepan, decide el médico de la delegación, pero el Comisionado Médico de la IJF tiene la última palabra.", None),
    "B2-EXC-005": ("The head may not be covered except for bandaging of a medical nature.", None),
    "B2-EXC-006": ("Quien compite en individual y en mixto debe dar el peso de su categoría mixta sin la tolerancia del 5% al menos una vez durante las dos competiciones.", None),
    "B2-EXC-007": ("Category combining may only be applied to categories with fewer than three entrants.", None),
    "B2-EXC-008": ("Las decoraciones del tatami solo pueden colocarse en el área de seguridad, nunca en el área de combate.", None),
    "B2-EXC-009": ("An athlete absent from the awards ceremony without a good reason may forfeit the medal and prize money.", None),
    "B2-EXC-010": ("Los árbitros del World Judo Tour deben tener como máximo 55 años durante el ciclo olímpico.",
                   "Los árbitros del World Judo Tour deben tener como máximo 50 años durante el ciclo olímpico."),
    "B2-DIR-001": ("At the start, the referee stands 2 m back from the line from which the athletes start.", None),
    "B2-DIR-006": ("Un atleta tiene derecho a 10 minutos de descanso entre combates.", None),
    "B2-DIR-007": ("Athletes must attend the medal ceremony barefoot.", None),
    "B2-DIR-011": ("An athlete must arrive at the random weigh-in at the latest 30 minutes or 6 contests before his first contest.", None),
    "B2-DIR-012": ("En un equipo mixto se pueden inscribir como máximo 12 atletas.", None),
    "B2-DIR-013": ("With twelve pairs, the kata event is divided into two groups.", "With twelve pairs, the kata event is divided into three groups."),
    "B2-DIR-016": ("La temperatura del pabellón debe mantenerse constante entre 18 y 22 °C.", None),
    "B2-DIR-017": ("Athletes must give 20% of their prize money to their coach.", None),
    "B2-MLG-001": ("Lors des compétitions de l'IJF, un combat de cadets dure 4 minutes de temps réel.",
                   "Lors des compétitions de l'IJF, un combat de cadets dure trois minutes."),
    "B2-MLG-002": ("Uma equipa mista é composta por seis atletas, três mulheres e três homens.",
                   "Uma equipa mista é composta por até cinco atletas."),
    "B2-MLG-003": ("Les vétérans ne sont pas soumis à une pesée aléatoire.",
                   "Pour les vétérans, la pesée aléatoire ouvre une heure avant le début de la compétition."),
    "B2-MLG-004": ("No campeonato de veteranos, o sorteio realiza-se às 19:00 do dia anterior à competição.",
                   "No campeonato de veteranos, o sorteio realiza-se às 14:00 hora local do dia anterior."),
}


def norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def window(page_text, snippet):
    t = page_text
    i = t.find(norm_ws(snippet))
    if i < 0:
        return None
    a, b = max(0, i - BEFORE), min(len(t), i + len(norm_ws(snippet)) + AFTER)
    while a > 0 and t[a - 1] != " ":
        a += 1
    while b < len(t) and t[b] != " ":
        b += 1
    return t[a:b].strip()


def overlaps(page_text, ev_snippet, d_snippet):
    """True si la ventana del distractor solapa (aunque sea parcialmente) el fragmento de evidencia."""
    t = page_text
    i, j = t.find(norm_ws(d_snippet)), t.find(norm_ws(ev_snippet))
    if i < 0 or j < 0:
        return False
    a, b = max(0, i - BEFORE), i + len(norm_ws(d_snippet)) + AFTER
    return a < j + len(norm_ws(ev_snippet)) and j < b


def perturb_numbers(claim):
    """Altera cada cifra de forma determinista (generico; sin conocimiento del item)."""
    def rep(m):
        s = m.group(0)
        if "," in s or "." in s:
            whole, frac = re.split(r"[.,]", s, maxsplit=1)
            return f"{whole}{s[len(whole)]}{(int(frac) + 3) % 10}"
        n = int(s)
        return str(n + 1 if n < 5 else n + 2).zfill(len(s))
    out, k = re.subn(r"\d+(?:[.,]\d+)?", rep, claim)
    return out if k else None


def build(passages, bench):
    page = {}
    for p in passages:
        page.setdefault(p["pdf_page_index"], norm_ws(p["text_original"]))
    pairs, errors, excluded = [], [], []
    by_id = {r["id"]: r for r in bench}
    for qid, (claim, wrong) in sorted(CLAIMS.items()):
        it = by_id.get(qid)
        if not it:
            errors.append(f"{qid}: no existe en benchmark_v2")
            continue
        if it["auto_labels"]["expected_behavior"] != "RESPONDER":
            errors.append(f"{qid}: item no respondible")
            continue
        ev = it["minimum_evidence"][0]
        prem = window(page[ev["page"]], ev["snippet"])
        if prem is None:
            errors.append(f"{qid}: evidencia no localizable")
            continue
        base = {"item_id": qid, "split": it["split"], "language": it["language"], "category": it["category"],
                "review_status": "PENDING_EXPERT_REVIEW"}

        def add(kind, premise, hyp, label, src):
            pairs.append(dict(base, pair_id=f"{qid}:{kind}:{len([x for x in pairs if x['item_id'] == qid])}",
                              pair_type=kind, premise=premise, hypothesis=hyp, label=label, premise_source=src,
                              premise_sha256=sha(premise)))
        add("SUPPORT", prem, claim, "SUPPORTED", {"page": ev["page"], "role": "minimum_evidence"})
        if wrong:
            add("SCOPE_CLAIM", prem, wrong, "NOT_SUPPORTED", {"page": ev["page"], "role": "minimum_evidence"})
        num = perturb_numbers(claim)
        if num:
            add("NUMBER", prem, num, "NOT_SUPPORTED", {"page": ev["page"], "role": "minimum_evidence"})
        for d in it["wrong_scope_distractors"]:
            dp = window(page[d["page"]], d["snippet"])
            if dp is None:
                errors.append(f"{qid}: distractor no localizable")
                continue
            if any(d["page"] == e["page"] and overlaps(page[d["page"]], e["snippet"], d["snippet"]) for e in it["minimum_evidence"]):
                excluded.append(f"{qid}: ventana del distractor p{d['page']} solapa la evidencia correcta")
                continue
            add("SCOPE_PREMISE", dp, claim, "NOT_SUPPORTED", {"page": d["page"], "role": "wrong_scope_distractor",
                                                               "scope_note": d.get("scope_note")})
    return pairs, errors, excluded


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    raw = open(os.path.join(ROOT, CORPUS_REL), "rb").read()
    braw = open(os.path.join(ROOT, BENCH_REL), "rb").read()
    pairs, errors, excluded = build(json.loads(raw.decode("utf-8")),
                                    [json.loads(l) for l in braw.decode("utf-8").splitlines() if l.strip()])
    from collections import Counter
    counts = {"pairs": len(pairs), "by_type": dict(Counter(p["pair_type"] for p in pairs)),
              "by_split": dict(Counter(p["split"] for p in pairs)), "by_language": dict(Counter(p["language"] for p in pairs)),
              "by_label": dict(Counter(p["label"] for p in pairs)), "items": len({p["item_id"] for p in pairs})}
    files = {"pairs.jsonl": "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in pairs)}
    files["manifest.json"] = json.dumps({
        "version": VERSION, "benchmark_v2_sha256": hashlib.sha256(braw).hexdigest(),
        "corpus_file_sha256": hashlib.sha256(raw).hexdigest(), "window_chars": [BEFORE, AFTER],
        "counts": counts, "excluded_pairs": excluded, "build_errors": errors,
        "note": "afirmaciones de evaluacion PENDING_EXPERT_REVIEW; etiquetas binarias SUPPORTED/NOT_SUPPORTED; "
                "los pares de test_sealed no deben usarse para elegir umbral ni modelo"}, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
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
    for e in excluded:
        print("EXCLUIDO:", e)
    for e in errors:
        print("ERROR:", e)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
