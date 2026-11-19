"""Compara estado por consulta entre la ejecucion previa (v4f2/v4v) y la nueva (g01f/g01v)."""
import json
import sys

pairs = [(sys.argv[1], sys.argv[2], "funcional-36"), (sys.argv[3], sys.argv[4], "validacion-23")]


def load(p):
    return {r["id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}


def repairs(r):
    s = json.dumps(r.get("dig") or {}, ensure_ascii=False)
    out = []
    try:
        rep = (r.get("dig") or {}).get("reparaciones") or {}
        for c in rep.get("identificadores") or []:
            out.append(f"{c.get('de')}->{c.get('a')} ({c.get('estado') or c.get('motivo')})")
    except AttributeError:
        pass
    return out, "Identificador inexistente" in s


tot_changed = 0
for old_p, new_p, name in pairs:
    old, new = load(old_p), load(new_p)
    assert set(old) == set(new), (name, set(old) ^ set(new))
    changed = [(i, old[i]["estado"], new[i]["estado"]) for i in sorted(old) if old[i]["estado"] != new[i]["estado"]]
    emitted_old = [i for i in old if old[i]["estado"] not in ("ABSTAIN", "CLARIFICATION_REQUIRED")]
    print(f"== {name}: {len(old)} consultas; emitidas antes {len(emitted_old)}")
    print("   cambios de estado:", changed or "ninguno")
    tot_changed += len(changed)
    for i in sorted(new):
        rp, retired = repairs(new[i])
        if retired or any("None" in x for x in rp):
            print(f"   {i}: reparacion de inexistente -> {rp}  estado {old[i]['estado']} -> {new[i]['estado']}")
    from collections import Counter
    print("   estados antes:", dict(Counter(r["estado"] for r in old.values())))
    print("   estados ahora:", dict(Counter(r["estado"] for r in new.values())))
print("TOTAL cambios de estado:", tot_changed)
