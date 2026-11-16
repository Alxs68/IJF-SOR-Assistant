"""Fase 8 (ampliacion SHADOW) - Capa derivada de unidades complementarias (shadow_units_v1).

Separada del corpus SOR primario y de article_units_v1. Ninguna unidad es fuente normativa:
normative_status = AUXILIAR_NO_NORMATIVA, decisive = False, citable_as_sor = False.

Entradas (solo lectura):
  data/corpus_multisource/processed/multisource_passages.json   fragmentos sidecar vigentes
  data/corpus_multisource/sidecar_registry.json + manifests/     lote activo y hashes
  data/corpus_multisource/staging/<DOC>_staged.md                espejos curados (KUN)
  docs/registro_documental_multifuente_ijf.csv                   catalogo de autoridad
  data/derived/article_units_v1/units.jsonl                      solo para resolver articulos SOR relacionados
Segmentacion: cada fragmento sidecar es ya un enunciado KUN atomico -> 1 unidad por fragmento
(chunk_identity); no se divide ni se fusiona. El texto derivado es identico al fragmento y se
localiza literalmente (offset) en el espejo de staging.
Uso: python scripts/build_shadow_units.py [--check | --overwrite] [--verify-upstream]
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

PROCESSOR = "sor_shadow_unit_builder"
VERSION = "1.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MS = "data/corpus_multisource"
PASSAGES_REL = f"{MS}/processed/multisource_passages.json"
REGISTRY_REL = f"{MS}/sidecar_registry.json"
CATALOG_REL = "docs/registro_documental_multifuente_ijf.csv"
SOR_REL = "data/processed/rebuild_2026_08_corrected/passages_candidate.json"
AU_REL = "data/derived/article_units_v1/units.jsonl"
RAW_REL = "data/raw/complementary"
OUT_REL = "data/derived/shadow_units_v1"
CORPUS_TAG = "SHADOW_COMPLEMENTARIO"
NORMATIVE_STATUS = "AUXILIAR_NO_NORMATIVA"
# Igual que _SUPPLEMENTARY_ROLE_BY_AUTHORITY de ADA (por nivel); TIER_1 nunca es complementario.
ROLE_BY_TIER = {"TIER_2": "COMPLEMENTO_INTERPRETATIVO", "TIER_3": "COMPLEMENTO_INTERPRETATIVO",
                "TIER_4": "MATERIAL_DIDACTICO", "TIER_5": "EVIDENCIA_AUDIOVISUAL"}
# Mismo filtro de elegibilidad que MultisourceRetriever._load_passages
ELIG_VALIDITY = {"VIGENTE", "CURRENT", "INTERPRETIVE_VALID"}
ELIG_STATUS = {"ELIGIBLE_INTERPRETATIVA", "APPROVED"}


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha(s):
    return sha_bytes(s.encode("utf-8"))


def read(rel, root=ROOT):
    with open(os.path.join(root, rel), "rb") as fh:
        return fh.read()


def err(sev, code, detail, unit_id=None):
    return {"severity": sev, "code": code, "unit_id": unit_id, "detail": detail}


def tier_of(s):
    m = re.match(r"(TIER_\d)", s or "")
    return m.group(1) if m else None


def parse_related(raw_list):
    nums = []
    for raw in raw_list:
        for n in re.findall(r"\b\d+(?:\.\d+)*\b", raw):
            if n not in nums:
                nums.append(n)
    return nums


def resolve_sor(nums, au_labels):
    out = []
    for n in nums:
        cands = [c for c in (f"Article {n}", n) if c in au_labels]
        out.append({"reference": n, "candidates": cands,
                    "resolution": "RESUELTA" if len(cands) == 1 else ("AMBIGUA" if cands else "NO_RESUELTA"),
                    "sor_unit_ids": sorted({u for c in cands for u in au_labels[c]})})
    return out


def load_inputs(root=ROOT):
    raw = {r: read(r, root) for r in (PASSAGES_REL, REGISTRY_REL, CATALOG_REL, SOR_REL)}
    chunks = json.loads(raw[PASSAGES_REL].decode("utf-8"))
    registry = json.loads(raw[REGISTRY_REL].decode("utf-8"))
    catalog = list(csv.DictReader(raw[CATALOG_REL].decode("utf-8").splitlines()))
    manifests = {}
    for name in registry.get("active_manifests", []):
        rel = f"{MS}/manifests/{name}"
        raw[rel] = read(rel, root)
        manifests[name] = json.loads(raw[rel].decode("utf-8"))
    staged = {}
    for f in sorted(glob.glob(os.path.join(root, MS, "staging", "*_staged.md"))):
        rel = os.path.relpath(f, root).replace("\\", "/")
        raw[rel] = read(rel, root)
        staged[os.path.basename(f).replace("_staged.md", "")] = rel
    au_labels = defaultdict(list)
    if os.path.exists(os.path.join(root, AU_REL)):
        raw[AU_REL] = read(AU_REL, root)
        for line in raw[AU_REL].decode("utf-8").splitlines():
            u = json.loads(line)
            if u["unit_level"] == 1 and u.get("article_label"):
                au_labels[u["article_label"]].append(u["unit_id"])
    sor_ids = {p["passage_id"] for p in json.loads(raw[SOR_REL].decode("utf-8"))}
    raw_files = sorted(os.path.relpath(f, root).replace("\\", "/") for f in glob.glob(os.path.join(root, RAW_REL, "*")))
    for rel in raw_files:
        raw[rel] = read(rel, root)
    return raw, chunks, registry, catalog, manifests, staged, au_labels, sor_ids, raw_files


def build(root=ROOT):
    raw, chunks, registry, catalog, manifests, staged, au_labels, sor_ids, raw_files = load_inputs(root)
    errors = []
    cat = {r["document_id"]: r for r in catalog}
    manifest_docs = {}
    for name, m in manifests.items():
        for d in m.get("documents_ingested", []):
            manifest_docs[d["document_id"]] = d
    if registry.get("multisource_passages_sha256") != sha_bytes(raw[PASSAGES_REL]):
        errors.append(err("ERROR", "REGISTRY_PASSAGES_HASH_MISMATCH", "sidecar_registry no coincide con multisource_passages.json"))
    if registry.get("primary_sor_corpus_sha256") != sha_bytes(raw[SOR_REL]):
        errors.append(err("ERROR", "REGISTRY_SOR_HASH_MISMATCH", "sidecar_registry no coincide con el corpus SOR"))
    if registry.get("total_sidecar_chunks") != len(chunks):
        errors.append(err("ERROR", "REGISTRY_CHUNK_COUNT_MISMATCH", f"{registry.get('total_sidecar_chunks')} != {len(chunks)}"))
    units, seen = [], Counter(c["chunk_id"] for c in chunks)
    for cid, n in seen.items():
        if n > 1:
            errors.append(err("ERROR", "DUPLICATE_CHUNK_ID", cid))
    for c in chunks:
        uid = "SHU1-" + c["chunk_id"]
        doc = c["document_id"]
        row = cat.get(doc)
        st_rel = staged.get(doc)
        st_txt = raw[st_rel].decode("utf-8") if st_rel else ""
        st_sha = sha_bytes(raw[st_rel]) if st_rel else None
        text = c["content_text"]
        off = st_txt.find(text)
        loc = "LITERAL" if off >= 0 else None
        if off < 0:
            esc = json.dumps(text, ensure_ascii=False)[1:-1]
            off = st_txt.find(esc)
            loc = "LITERAL_JSON_ESCAPADO" if off >= 0 else None
        kun_off = st_txt.find(f"### {c.get('source_kun_id')}:")
        heading = st_txt[kun_off:st_txt.find("\n", kun_off)].strip() if kun_off >= 0 else None
        if row is None:
            errors.append(err("ERROR", "DOCUMENT_NOT_IN_CATALOG", doc, uid))
        if not st_rel:
            errors.append(err("ERROR", "STAGED_FILE_MISSING", doc, uid))
        elif st_sha != c.get("staging_sha256"):
            errors.append(err("ERROR", "STAGED_HASH_MISMATCH", doc, uid))
        if row and row["hash_integridad"] != c.get("staging_sha256"):
            errors.append(err("ERROR", "CATALOG_HASH_MISMATCH", doc, uid))
        if doc in manifest_docs and manifest_docs[doc].get("staging_sha256") != c.get("staging_sha256"):
            errors.append(err("ERROR", "MANIFEST_HASH_MISMATCH", doc, uid))
        if doc not in manifest_docs:
            errors.append(err("ERROR", "DOCUMENT_NOT_IN_ACTIVE_MANIFEST", doc, uid))
        if off < 0:
            errors.append(err("ERROR", "CHUNK_TEXT_NOT_IN_STAGED", c["chunk_id"], uid))
        if kun_off < 0:
            errors.append(err("WARNING", "KUN_BLOCK_NOT_FOUND", str(c.get("source_kun_id")), uid))
        elif off >= 0:
            nxt = st_txt.find("\n### ", kun_off + 4)
            if not (kun_off <= off < (nxt if nxt >= 0 else len(st_txt))):
                errors.append(err("WARNING", "CHUNK_OUTSIDE_DECLARED_KUN_BLOCK", f"{c['chunk_id']} / {c.get('source_kun_id')}", uid))
        chunk_tier = tier_of(c.get("authority"))
        cat_tier = row["nivel_autoridad"] if row else None
        if chunk_tier != cat_tier:
            errors.append(err("ERROR", "AUTHORITY_TIER_MISMATCH", f"fragmento {chunk_tier} / catalogo {cat_tier}", uid))
        if cat_tier == "TIER_1" or chunk_tier == "TIER_1":
            errors.append(err("ERROR", "SHADOW_WITH_PRIMARY_AUTHORITY", doc, uid))
        eligible = (chunk_tier in ("TIER_2", "TIER_3") and str(c.get("validity")).upper() in ELIG_VALIDITY
                    and str(c.get("eligibility")).upper() in ELIG_STATUS)
        nums = parse_related(c.get("related_sor_articles", []))
        rel = resolve_sor(nums, au_labels)
        for r in rel:
            if r["resolution"] != "RESUELTA":
                errors.append(err("INFO", "RELATED_SOR_REFERENCE_" + r["resolution"], f"{r['reference']} -> {r['candidates']}", uid))
        units.append({
            "unit_id": uid, "corpus": CORPUS_TAG, "chunk_id": c["chunk_id"], "document_id": doc,
            "source_kun_id": c.get("source_kun_id"), "title": c.get("title"),
            "derived_text": text, "derived_text_sha256": sha(text),
            "chunk_record_sha256": sha(json.dumps(c, ensure_ascii=False, sort_keys=True)),
            "segmentation_method": f"{PROCESSOR}/{VERSION}:chunk_identity",
            "staged_path": st_rel, "staged_sha256": st_sha, "staged_char_start": off if off >= 0 else None,
            "staged_char_end": (off + (len(text) if loc == "LITERAL" else len(json.dumps(text, ensure_ascii=False)) - 2)) if off >= 0 else None,
            "staged_locator": loc, "staged_line": (st_txt.count("\n", 0, off) + 1) if off >= 0 else None,
            "kun_block_heading": heading,
            "authority_chunk": c.get("authority"), "authority_tier": chunk_tier,
            "catalog_authority": row["autoridad_documental"] if row else None,
            "catalog_validity": row["estado_vigencia"] if row else None,
            "catalog_approval": row["estado_aprobacion"] if row else None,
            "catalog_normative_relation": row["relacion_normativa"] if row else None,
            "catalog_source": row["fuente"] if row else None, "catalog_url": row["url"] if row else None,
            "validity": c.get("validity"), "eligibility": c.get("eligibility"), "eligible_for_sidecar": eligible,
            "related_sor_articles_raw": c.get("related_sor_articles", []), "related_sor_resolution": rel,
            "supplementary_role": ROLE_BY_TIER.get(chunk_tier),
            "normative_status": NORMATIVE_STATUS, "decisive": False, "citable_as_sor": False,
            "may_substitute_sor": False, "subordinate_to": "SOR-2026-08 (TIER_1, corpus primario)",
            "validation_status": "VALIDADA",
        })
    for u in units:
        if any(e["unit_id"] == u["unit_id"] and e["severity"] == "ERROR" for e in errors):
            u["validation_status"] = "ERROR"
    errors += validate(units, sor_ids, au_labels)
    inventory = []
    ingested = {c["document_id"] for c in chunks}
    raw_hash = {sha_bytes(raw[r]): r for r in raw_files}
    for r in catalog:
        if r["nivel_autoridad"] == "TIER_1":
            status = "CORPUS_PRIMARIO_SOR"
        elif r["document_id"] in ingested:
            status = "INGESTADO_SIDECAR"
        elif r["estado_aprobacion"] == "RECHAZADO":
            status = "RECHAZADO"
        elif r["estado_vigencia"] in ("HISTORICO", "HISTORICO_DEROGADO", "OBSOLETO", "OBSOLETO_RETIRADO"):
            status = "HISTORICO_NO_INGESTADO"
        else:
            status = "REGISTRADO_NO_INGESTADO"
        inventory.append({"document_id": r["document_id"], "title": r["titulo"], "tier": r["nivel_autoridad"],
                          "authority": r["autoridad_documental"], "validity": r["estado_vigencia"],
                          "approval": r["estado_aprobacion"], "normative_relation": r["relacion_normativa"],
                          "hash": r["hash_integridad"], "local_raw_file": raw_hash.get(r["hash_integridad"]),
                          "chunks": sum(1 for c in chunks if c["document_id"] == r["document_id"]),
                          "inventory_status": status})
    cat_hashes = {r["hash_integridad"] for r in catalog}
    uncatalogued = [r for r in raw_files if sha_bytes(raw[r]) not in cat_hashes]
    for r in uncatalogued:
        errors.append(err("WARNING", "LOCAL_FILE_NOT_IN_CATALOG", r))
    sev = Counter(e["severity"] for e in errors)
    stats = {
        "catalog_documents": len(catalog), "inventory_by_status": dict(sorted(Counter(i["inventory_status"] for i in inventory).items())),
        "sidecar_documents": len(ingested), "sidecar_chunks": len(chunks), "units": len(units),
        "units_by_tier": dict(sorted(Counter(u["authority_tier"] for u in units).items())),
        "units_by_document": dict(sorted(Counter(u["document_id"] for u in units).items())),
        "units_eligible_for_sidecar": sum(u["eligible_for_sidecar"] for u in units),
        "units_located_literally_in_staged": sum(u["staged_locator"] is not None for u in units),
        "related_sor_resolution": dict(sorted(Counter(r["resolution"] for u in units for r in u["related_sor_resolution"]).items())),
        "units_decisive_true": sum(u["decisive"] for u in units),
        "local_raw_files": raw_files, "local_raw_files_not_in_catalog": uncatalogued,
        "errors_by_severity": dict(sorted(sev.items())), "errors_by_code": dict(sorted(Counter(e["code"] for e in errors).items())),
    }
    report = {"processor": PROCESSOR, "processor_version": VERSION, "accepted": sev.get("ERROR", 0) == 0,
              "checks": ["traceability_chunk_staged_catalog_manifest", "hash_consistency", "corpus_separation",
                         "no_normative_authority", "eligibility_consistency", "id_disjointness_with_sor"],
              "errors": [e for e in errors if e["severity"] == "ERROR"], "warnings": [e for e in errors if e["severity"] == "WARNING"]}
    input_hashes = {k: sha_bytes(v) for k, v in sorted(raw.items())}
    metadata = {"processor": PROCESSOR, "processor_version": VERSION, "corpus": CORPUS_TAG, "normative_status": NORMATIVE_STATUS,
                "description": "Unidades derivadas de documentacion complementaria SHADOW; subordinadas al SOR; nunca fundamento normativo.",
                "segmentation": "chunk_identity: 1 unidad por fragmento sidecar (enunciado KUN atomico), texto identico",
                "active_manifests": registry.get("active_manifests"), "input_sha256": input_hashes,
                "build_command": "python scripts/build_shadow_units.py", "id_scheme": "SHU1-<chunk_id>"}
    trace = {"chunk_to_unit": {u["chunk_id"]: u["unit_id"] for u in units},
             "unit_to_source": {u["unit_id"]: {"document_id": u["document_id"], "chunk_id": u["chunk_id"], "kun": u["source_kun_id"],
                                               "staged_path": u["staged_path"], "staged_char_start": u["staged_char_start"],
                                               "staged_line": u["staged_line"]} for u in units},
             "document_to_units": {d: [u["unit_id"] for u in units if u["document_id"] == d] for d in sorted(ingested)},
             "unit_to_related_sor_units": {u["unit_id"]: sorted({x for r in u["related_sor_resolution"] for x in r["sor_unit_ids"]}) for u in units}}
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    files = {"units.jsonl": "".join(json.dumps(u, ensure_ascii=False, sort_keys=True) + "\n" for u in units),
             "inventory.json": dump(inventory), "traceability_map.json": dump(trace), "coverage_stats.json": dump(stats),
             "validation_report.json": dump(report), "errors.jsonl": "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in errors),
             "metadata.json": dump(metadata)}
    files["hashes.json"] = dump({"artifacts_sha256": {k: sha(v) for k, v in sorted(files.items())}, "processor_version": VERSION})
    return files, units, errors, stats, report, raw


def validate(units, sor_ids, au_labels):
    errs = []
    au_ids = {x for v in au_labels.values() for x in v}
    for u in units:
        if u["unit_id"] in sor_ids or u["unit_id"] in au_ids or u["chunk_id"] in sor_ids:
            errs.append(err("ERROR", "ID_COLLISION_WITH_PRIMARY", u["unit_id"], u["unit_id"]))
        if re.match(r"SOR-|AU1-", u["unit_id"]):
            errs.append(err("ERROR", "PRIMARY_ID_PATTERN_IN_SHADOW", u["unit_id"], u["unit_id"]))
        if u["corpus"] != CORPUS_TAG or u["normative_status"] != NORMATIVE_STATUS:
            errs.append(err("ERROR", "CORPUS_TAG_INVALID", u["unit_id"], u["unit_id"]))
        if u["decisive"] or u["citable_as_sor"] or u["may_substitute_sor"]:
            errs.append(err("ERROR", "SHADOW_GRANTED_NORMATIVE_AUTHORITY", u["unit_id"], u["unit_id"]))
        if u["supplementary_role"] is None:
            errs.append(err("ERROR", "NO_SUPPLEMENTARY_ROLE", str(u["authority_tier"]), u["unit_id"]))
        if u["derived_text_sha256"] != sha(u["derived_text"]):
            errs.append(err("ERROR", "DERIVED_HASH_MISMATCH", u["unit_id"], u["unit_id"]))
    if os.path.normpath(OUT_REL) == os.path.normpath(os.path.dirname(AU_REL)):
        errs.append(err("ERROR", "OUTPUT_NOT_SEPARATED", OUT_REL))
    return errs


def verify_upstream(units, root=ROOT):
    """Opcional: busca cada fragmento en el texto extraido de los PDF originales locales (pypdf)."""
    try:
        from pypdf import PdfReader
    except Exception as e:  # pragma: no cover
        return {"status": "NO_VERIFICABLE", "reason": f"pypdf no disponible: {e}"}
    norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip().lower()
    pdfs = {}
    for f in sorted(glob.glob(os.path.join(root, RAW_REL, "*.pdf"))):
        pdfs[os.path.basename(f)] = [norm(p.extract_text() or "") for p in PdfReader(f).pages]
    import pypdf
    out = {"status": "EJECUTADA", "pypdf_version": pypdf.__version__, "pdfs": sorted(pdfs), "units": {}}
    for u in units:
        t = norm(u["derived_text"])
        full = [{"file": k, "page": i + 1} for k, ps in pdfs.items() for i, p in enumerate(ps) if t in p]
        pref = [] if full else [{"file": k, "page": i + 1} for k, ps in pdfs.items() for i, p in enumerate(ps) if t[:60] in p]
        out["units"][u["unit_id"]] = {"result": "LITERAL_COMPLETO" if full else ("PREFIJO_60_CARACTERES" if pref else "NO_LOCALIZADO_EN_PDF_LOCAL"),
                                      "locations": full or pref}
    out["summary"] = dict(Counter(v["result"] for v in out["units"].values()))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--verify-upstream", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    files, units, errors, stats, report, raw = build()
    _f2, _u2, _e2, _s2, _r2, raw_after = build()
    if {k: sha_bytes(v) for k, v in raw.items()} != {k: sha_bytes(v) for k, v in raw_after.items()}:
        print("ERROR: entradas modificadas durante la construccion", file=sys.stderr)
        return 3
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
    if a.verify_upstream:
        with open(os.path.join(a.out, "upstream_verification.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(verify_upstream(units), fh, ensure_ascii=False, indent=2, sort_keys=True)
    print(json.dumps({k: stats[k] for k in ("catalog_documents", "inventory_by_status", "sidecar_chunks", "units",
                                            "units_located_literally_in_staged", "related_sor_resolution", "errors_by_severity")}, ensure_ascii=False, indent=1))
    print("ACEPTADA" if report["accepted"] else "NO ACEPTADA")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    sys.exit(main())
