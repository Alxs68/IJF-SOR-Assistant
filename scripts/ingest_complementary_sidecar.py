"""
Script to stage and ingest newly discovered complementary IJF documents
into the isolated sidecar index without touching primary SOR 2026.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
from src.multisource_indexer import MultisourceIngestionEngine

def main():
    engine = MultisourceIngestionEngine()
    
    # 1. Stage new documents
    docs_to_stage = [
        ("KUN-DIS-001", "data/markdown/kuns_dis_001.md"),
        ("KUN-ETH-001", "data/markdown/kuns_eth_001.md"),
        ("KUN-QSY-001", "data/markdown/kuns_qsy_001.md"),
    ]
    
    new_staged = []
    for doc_id, path in docs_to_stage:
        ok, msg, meta = engine.stage_document(doc_id, path)
        print(f"Staging {doc_id}: ok={ok}, msg={msg}")
        if not ok:
            raise RuntimeError(f"Failed to stage {doc_id}: {msg}")
        new_staged.append(meta)

    # 2. Collect all staged items (existing + new)
    all_staged = [
        {
            "document_id": "KUN-PPT-002",
            "source_path": os.path.join(engine.project_root, "data", "markdown", "kuns_ppt_002.md"),
            "staging_path": os.path.join(engine.staging_dir, "KUN-PPT-002_staged.md"),
            "sha256": engine.calculate_file_sha256(os.path.join(engine.staging_dir, "KUN-PPT-002_staged.md"))
        },
        {
            "document_id": "KUN-NEW-001",
            "source_path": os.path.join(engine.project_root, "data", "markdown", "kuns_new_001.md"),
            "staging_path": os.path.join(engine.staging_dir, "KUN-NEW-001_staged.md"),
            "sha256": engine.calculate_file_sha256(os.path.join(engine.staging_dir, "KUN-NEW-001_staged.md"))
        },
        {
            "document_id": "KUN-NEW-003",
            "source_path": os.path.join(engine.project_root, "data", "markdown", "kuns_new_003.md"),
            "staging_path": os.path.join(engine.staging_dir, "KUN-NEW-003_staged.md"),
            "sha256": engine.calculate_file_sha256(os.path.join(engine.staging_dir, "KUN-NEW-003_staged.md"))
        }
    ]
    all_staged.extend(new_staged)

    # 3. Process and persist sidecar batch
    batch_id = "BATCH-MULTI-2026-11-02"
    manifest = engine.process_and_persist_sidecar(
        staged_items=all_staged,
        batch_id=batch_id,
        approved_by="Alexis"
    )
    
    print("\n=== Ingestion Complete ===")
    print(f"Batch ID: {manifest.batch_id}")
    print(f"Total Chunks: {manifest.total_chunks}")
    print(f"Documents Ingested: {len(manifest.documents_ingested)}")
    print(f"Sidecar Passages SHA-256: {manifest.sidecar_passages_sha256}")
    print(f"Primary SOR Corpus SHA-256 (Invariant): {manifest.primary_sor_corpus_sha256}")

if __name__ == "__main__":
    main()
