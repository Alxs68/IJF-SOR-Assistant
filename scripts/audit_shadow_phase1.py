import os
import json
import csv

# 1. Staging files
staging_dir = "data/corpus_multisource/staging"
staging_files = os.listdir(staging_dir) if os.path.exists(staging_dir) else []
print(f"Staging files ({len(staging_files)}): {staging_files}")

# 2. Markdown files
markdown_dir = "data/markdown"
markdown_files = [f for f in os.listdir(markdown_dir) if f.startswith("kuns_")] if os.path.exists(markdown_dir) else []
print(f"Markdown KUN files ({len(markdown_files)}): {markdown_files}")

# 3. Processed sidecar passages
passages_file = "data/corpus_multisource/processed/multisource_passages.json"
passages = []
if os.path.exists(passages_file):
    with open(passages_file, "r", encoding="utf-8") as f:
        passages = json.load(f)
print(f"\nTotal passages in multisource_passages.json: {len(passages)}")
passages_by_doc = {}
for p in passages:
    d = p.get("document_id")
    passages_by_doc.setdefault(d, []).append(p["chunk_id"])
for d, chunks in passages_by_doc.items():
    print(f"  {d}: {len(chunks)} chunks -> {chunks}")

# 4. Master CSV
csv_file = "docs/registro_documental_multifuente_ijf.csv"
csv_docs = []
if os.path.exists(csv_file):
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_docs = list(reader)
print(f"\nTotal entries in registro_documental_multifuente_ijf.csv: {len(csv_docs)}")
for r in csv_docs:
    print(f"  {r['document_id']} | Tier {r['nivel_autoridad']} | {r['estado_vigencia']} | {r['estado_aprobacion']} | {r['titulo'][:50]}")
