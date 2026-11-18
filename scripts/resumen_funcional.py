"""Resume y compara ejecuciones de eval_funcional.py (mismo conjunto de consultas).

  python scripts/resumen_funcional.py base.jsonl v140.jsonl [cand2.jsonl ...]
Imprime, por version: respuestas/abstenciones por tipo de consulta, recuperacion y contexto de la evidencia
esperada, controles DIG fallidos, proveedor/fallback y errores HTTP; y una tabla por consulta.
"""
import collections
import json
import sys


ESPERADO = {}


def page(pid):
    return (pid or "")[:4]


def load(path):
    rs = {r["id"]: r for r in (json.loads(l) for l in open(path, encoding="utf-8") if l.strip())}
    for r in rs.values():  # coincidencia por PAGINA y con el conjunto de consultas vigente
        exp = {page(x) for x in ESPERADO.get(r["id"], r["esperado"])}
        r["esperado"] = sorted(exp)
        r["esperado_recuperado"] = sorted(exp & {page(x) for x in (r.get("recuperado") or []) + (r.get("relacionados") or [])})
        r["esperado_en_contexto"] = sorted(exp & {page(x) for x in r.get("contexto") or []})
    return rs


def main(paths):
    import os
    qp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "funcional",
                      "consultas_funcionales_v1.json")
    if os.path.exists(qp):
        ESPERADO.update({c["id"]: c["esperado"] for c in json.load(open(qp, encoding="utf-8"))["consultas"]})
    runs =[(p.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].replace(".jsonl", ""), load(p)) for p in paths]
    ids = sorted(set().union(*[set(r) for _, r in runs]))
    for name, rs in runs:
        c = collections.Counter()
        fails = collections.Counter()
        prov = collections.Counter()
        for r in rs.values():
            resp = r["respondible"]
            ok = r["estado"] == "SUCCESS"
            c[(resp, "responde" if ok else (r["estado"] or "ERROR").lower())] += 1
            exp = set(r["esperado"])
            if exp:
                c["con_esperado"] += 1
                c["esperado_recuperado"] += bool(r["esperado_recuperado"])
                c["esperado_en_contexto"] += bool(r["esperado_en_contexto"])
            for f in (r.get("dig") or {}).get("fallidos") or []:
                fails[f] += 1
            for x in r.get("llm") or []:
                prov[(x.get("tipo"), x.get("proveedor"), x.get("modelo"), bool(x.get("fallback")))] += 1
                for p, e in (x.get("errores") or {}).items():
                    prov[("ERROR", p, e.get("tipo"), e.get("http"))] += 1
        print(f"=== {name} ({len(rs)} consultas)")
        for k in ("SI", "PARCIAL", "AMBIGUA", "NO"):
            parts = {b: v for (a, b), v in ((kk, vv) for kk, vv in c.items() if isinstance(kk, tuple)) if a == k}
            print(f"  respondible={k}: {parts}")
        print(f"  evidencia esperada recuperada: {c['esperado_recuperado']}/{c['con_esperado']}  en contexto: {c['esperado_en_contexto']}/{c['con_esperado']}")
        print(f"  DIG fallidos: {dict(fails.most_common())}")
        print(f"  LLM: {dict(prov)}")
    print("\nid   resp     " + "  ".join(f"{n[:22]:<22}" for n, _ in runs))
    for i in ids:
        cells = []
        for _, rs in runs:
            r = rs.get(i)
            if not r:
                cells.append(f"{'-':<22}")
                continue
            st = {"SUCCESS": "OK", "ABSTAIN": "ABS", "CLARIFICATION_REQUIRED": "ACL"}.get(r["estado"], str(r["estado"]))
            f = ",".join(x.split("_")[0].replace("DIG-", "") for x in ((r.get("dig") or {}).get("fallidos") or []))
            ctx = "c" if r["esperado_en_contexto"] else ("r" if r["esperado_recuperado"] else ("-" if r["esperado"] else " "))
            cells.append(f"{st:<3} {ctx} {f:<16}"[:22].ljust(22))
        any_r = next(rs[i] for _, rs in runs if i in rs)
        print(f"{i:<4} {any_r['respondible']:<8} " + "  ".join(cells))
    print("\nleyenda: OK responde | ABS abstiene | ACL pide aclaracion; c=esperado en contexto, r=recuperado pero fuera de contexto, -=no recuperado; numeros = controles DIG fallidos")


if __name__ == "__main__":
    main(sys.argv[1:])
