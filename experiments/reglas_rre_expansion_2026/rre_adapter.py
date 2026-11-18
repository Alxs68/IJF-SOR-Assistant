"""Adaptador experimental AISLADO para ablacion de reglas del RRE.

Lee src/rre_engine.py (solo lectura), verifica su SHA-256 y genera EN MEMORIA un modulo variante en el que cada
bloque de reglas queda envuelto en `if not _ABL.get("<BLOQUE>"):` (conmutable en tiempo de ejecucion) y anota en
`_FIRED` los bloques cuya condicion se cumple. Con `_ABL` vacio el comportamiento es identico al original (se
comprueba en eval). Nunca escribe en src/: el diff generado se guarda en este directorio para auditoria.

`translate_ids` (opcional) sustituye mecanicamente los literales de passage_id por otros identificadores (p. ej. la
unidad-apartado que contiene ese pasaje). Es un DIAGNOSTICO de portabilidad: no crea reglas nuevas, traduce las
existentes, y no es candidato a integracion.
"""
import difflib, hashlib, os, re, sys, types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "src", "rre_engine.py")
EXPECTED_SHA = "a0318e88b4e98b271a38710c8b99768ad4cab2bdbe5ec0434f7333fce2841c78"

# Bloques con passage_id fijos (las 18 IDs) — cabecera exacta (sin sangria) de la sentencia que se conmuta
ID_BLOCKS = {
    "FRONTERA": "if has_boundary_term and has_osaekomi_term:",
    "PUENTE": "if is_bridge_specific or is_defense_specific:",
    "HEAD_DIVING": "if is_dive_specific or is_throw_by_tori or has_hansoku_term or (not is_defense_specific and not is_concussion_specific):",
    "CADETE": "if is_cadet_specific or ((is_defense_specific or is_throw_by_tori or is_senior_junior_specific) and has_head_term):",
    "CONDUCTA": "if has_conduct_term:",
    "F1_SEC2": "if p_art in f1_to_sec2:",
    "LATERAL": "if is_lateral_scoring:",
}
# Bloques complementarios por pagina/articulo SIN passage_id (no forman parte de las 18 IDs; se miden aparte)
PAGE_BLOCKS = {
    "CABEZA_ATEN": "if not is_concussion_specific:",
    "KUMIKATA": "if is_kumikata_grip_query:",
}
ALL_BLOCKS = {**ID_BLOCKS, **PAGE_BLOCKS}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def _indent(l):
    return len(l) - len(l.lstrip())


def build_source(translate_ids=None):
    raw = open(SRC, "rb").read()
    got = sha256(raw)
    if got != EXPECTED_SHA:
        raise RuntimeError(f"src/rre_engine.py cambio (sha {got}); el inventario de reglas no es valido")
    lines = raw.decode("utf-8").split("\n")
    ranges = []
    for name, head in ALL_BLOCKS.items():
        idx = [i for i, l in enumerate(lines) if l.strip() == head]
        if len(idx) != 1:
            raise RuntimeError(f"cabecera de {name} aparece {len(idx)} veces")
        i = idx[0]
        ind = _indent(lines[i])
        j = i + 1
        while j < len(lines):
            l = lines[j]
            if not l.strip() or _indent(l) > ind or (_indent(l) == ind and re.match(r"(elif|else)\b", l.strip())):
                j += 1
                continue
            break
        while not lines[j - 1].strip():
            j -= 1
        heads = [k for k in range(i, j) if _indent(lines[k]) == ind and re.match(r"(if|elif|else)\b", lines[k].strip())]
        ranges.append((i, j, ind, name, heads))
    ranges.sort()
    for a, b in zip(ranges, ranges[1:]):
        if a[1] > b[0]:
            raise RuntimeError(f"bloques solapados: {a[3]} / {b[3]}")
    out = list(lines)
    for i, j, ind, name, heads in reversed(ranges):
        body = []
        for k in range(i, j):
            l = lines[k]
            body.append("    " + l if l.strip() else l)
            if k in heads:  # la condicion de esta rama se cumplio
                body.append(" " * (ind + 8) + f'_FIRED.add("{name}")')
        out[i:j] = [" " * ind + f'if not _ABL.get("{name}"):'] + body
    new = "\n".join(out)
    if translate_ids:
        for old, nid in translate_ids.items():
            new = new.replace(f'"{old}"', f'"{nid}"').replace(f"'{old}'", f"'{nid}'")
        # tuplas que quedan con el mismo id repetido -> un solo elemento (evita duplicar la bonificacion)
        new = re.sub(r'\("([A-Z]{3}-\d{4})", "\1"\)', r'("\1",)', new)
    return raw.decode("utf-8"), new, {n: (i + 1, j) for i, j, _, n, _ in ranges}


def load_variant(tag="abl", translate_ids=None, save_diff=True):
    orig, new, line_ranges = build_source(translate_ids)
    name = f"rre_engine_{tag}"
    mod = types.ModuleType(name)
    mod.__file__ = SRC
    mod._ABL = {}
    mod._FIRED = set()
    sys.modules[name] = mod
    exec(compile(new, f"<{name} generado en memoria desde src/rre_engine.py>", "exec"), mod.__dict__)
    if save_diff:
        d = difflib.unified_diff(orig.split("\n"), new.split("\n"), "src/rre_engine.py", f"<{name}>", lineterm="", n=1)
        with open(os.path.join(HERE, f"adapter_diff_{tag}.patch"), "w", encoding="utf-8") as f:
            f.write("\n".join(d) + "\n")
    return mod, line_ranges, sha256(new.encode("utf-8"))
