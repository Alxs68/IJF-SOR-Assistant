"""
Multisource Ingestion and Sidecar Management Module for IJF SOR Assistant.
Part of Phase 4.2.2: Isolated Sidecar Storage & Controlled Ingestion.

Implements strict validation, hashing, staging, and isolated sidecar indexing
without touching or mutating primary SOR 2026 artifacts.
"""

import os
import re
import json
import shutil
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.document_governance import (
    DocumentAuthority,
    ValidityStatus,
    ApprovalStatus,
    EligibilityStatus,
    NormativeRelationType,
    DocumentMetadata
)
from src.document_validator import DocumentValidator, DocumentValidationError


class SidecarChunk(BaseModel):
    """
    Normalized chunk representation within an isolated sidecar index.
    Preserves strict provenance, authority, and relation to primary SOR articles.
    """
    chunk_id: str = Field(..., description="Unique chunk ID (e.g. CHK-PPT002-001)")
    document_id: str = Field(..., description="Document ID from multisource registry")
    title: str = Field(..., description="Descriptive title of the section or KUN")
    content_text: str = Field(..., min_length=10, description="Normalized textual body")
    authority: DocumentAuthority = Field(..., description="Document authority tier")
    validity: ValidityStatus = Field(..., description="Temporal validity status")
    eligibility: EligibilityStatus = Field(..., description="Pipeline eligibility gating")
    related_sor_articles: List[str] = Field(default_factory=list, description="Associated primary SOR articles")
    normative_relation: NormativeRelationType = Field(..., description="Relation nature to SOR")
    source_kun_id: Optional[str] = Field(None, description="Original KUN identifier if extracted from mirror")
    staging_sha256: str = Field(..., description="SHA-256 hash of the staging source file")
    ingested_at: str = Field(..., description="ISO 8601 ingestion timestamp")


class BatchManifest(BaseModel):
    """
    Cryptographic manifest tracking a batch of ingested sidecar documents.
    """
    batch_id: str = Field(..., description="Unique batch identifier")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    approved_by: str = Field(..., description="Data steward responsible for approval")
    curatorship_log: Optional[str] = Field(None, description="Path or reference to curatorship log")
    documents_ingested: List[Dict[str, Any]] = Field(default_factory=list, description="Summary of ingested docs")
    total_chunks: int = Field(0, description="Total chunks generated across batch")
    sidecar_passages_sha256: Optional[str] = Field(None, description="SHA-256 of processed multisource_passages.json")
    primary_sor_corpus_sha256: str = Field(..., description="SHA-256 baseline of primary SOR to certify isolation")


class MultisourceIngestionEngine:
    """
    Orchestrates the ingestion, staging, validation, chunking, and isolated
    sidecar persistence of supplementary documents approved by Alexis.
    """

    DEFAULT_SIDECAR_DIR = os.path.join("data", "corpus_multisource")
    PRIMARY_SOR_PASSAGES = os.path.join("data", "processed", "rebuild_2026_08_corrected", "passages_candidate.json")

    def __init__(self, base_dir: Optional[str] = None, validator: Optional[DocumentValidator] = None):
        if base_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.base_dir = os.path.join(project_root, self.DEFAULT_SIDECAR_DIR)
            self.project_root = project_root
        else:
            self.base_dir = base_dir
            self.project_root = os.path.dirname(os.path.dirname(base_dir))

        self.staging_dir = os.path.join(self.base_dir, "staging")
        self.manifests_dir = os.path.join(self.base_dir, "manifests")
        self.processed_dir = os.path.join(self.base_dir, "processed")
        self.sidecar_registry_file = os.path.join(self.base_dir, "sidecar_registry.json")

        self.validator = validator or DocumentValidator()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Creates the isolated sidecar folder structure."""
        os.makedirs(self.staging_dir, exist_ok=True)
        os.makedirs(self.manifests_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

    @staticmethod
    def calculate_file_sha256(filepath: str) -> str:
        """Computes hexadecimal SHA-256 hash of a file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found for hashing: {filepath}")
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def stage_document(self, document_id: str, source_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates eligibility and stages an approved document into staging/ with pre-hashing.
        Rejects documents with PENDIENTE, RECHAZADO, or ARCHIVADO status.
        """
        doc = self.validator.get_document(document_id)
        if not doc:
            return False, f"Rejection: Document {document_id} is not registered in the catalog.", {}

        # Gate 1: Check approval status
        if doc.approval not in (ApprovalStatus.APROBADO, ApprovalStatus.APROBADO_CONDICIONADO):
            return False, f"Rejection: Document {document_id} has approval status {doc.approval.value} (Only APROBADO allowed).", {}

        # Gate 2: Check validity
        if doc.validity in (ValidityStatus.HISTORICO_DEROGADO, ValidityStatus.OBSOLETO_RETIRADO):
            return False, f"Rejection: Document {document_id} is {doc.validity.value} and cannot be staged.", {}

        # Gate 3: Check source file existence and verify hash if documented
        if not os.path.isabs(source_path):
            abs_source = os.path.join(self.project_root, source_path)
        else:
            abs_source = source_path

        if not os.path.exists(abs_source):
            return False, f"Rejection: Source file not found: {abs_source}", {}

        source_hash = self.calculate_file_sha256(abs_source)
        if doc.integrity_hash and doc.integrity_hash != "UNKNOWN":
            if source_hash != doc.integrity_hash:
                return False, f"Rejection: Cryptographic mismatch for {document_id}: expected {doc.integrity_hash}, got {source_hash}.", {}

        # Copy to staging
        ext = os.path.splitext(abs_source)[1]
        staging_filename = f"{document_id}_staged{ext}"
        staging_dest = os.path.join(self.staging_dir, staging_filename)
        shutil.copy2(abs_source, staging_dest)

        dest_hash = self.calculate_file_sha256(staging_dest)
        if dest_hash != source_hash:
            os.remove(staging_dest)
            return False, "Rejection: Hash verification failed during staging copy.", {}

        stage_meta = {
            "document_id": document_id,
            "source_path": abs_source,
            "staging_path": staging_dest,
            "sha256": dest_hash,
            "staged_at": datetime.now(timezone.utc).isoformat(),
            "authority": doc.authority.value,
            "validity": doc.validity.value,
            "eligibility": doc.determine_eligibility().value,
            "related_sor_articles": doc.related_sor_articles,
            "normative_relation": doc.normative_relation.value
        }

        return True, f"Document {document_id} staged successfully with SHA-256 {dest_hash[:16]}...", stage_meta

    def parse_markdown_kuns(self, staging_path: str, document_id: str, doc_meta: DocumentMetadata) -> List[SidecarChunk]:
        """
        Parses structured Markdown mirrors (extracting JSON KUN blocks or sections)
        into normalized SidecarChunk objects.
        """
        chunks: List[SidecarChunk] = []
        with open(staging_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        file_hash = self.calculate_file_sha256(staging_path)

        # Pattern 1: Look for JSON blocks in KUN files
        json_blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_blocks:
            for idx, raw_json in enumerate(json_blocks, start=1):
                try:
                    data = json.loads(raw_json)
                    kun_id = data.get("id_conocimiento", f"KUN-{idx:04d}")
                    title = data.get("titulo", f"{document_id} Unit {idx}")
                    body = data.get("contenido_original", "") or data.get("contenido_traduccion", "") or data.get("contenido", "") or data.get("descripcion", "") or data.get("criterio", "")
                    if not body:
                        # Extract any non-empty textual field
                        for k, v in data.items():
                            if isinstance(v, str) and len(v) > 20 and k not in ("id_conocimiento", "titulo", "tipo", "nivel_autoridad", "referencia_especifica", "fuente_origen"):
                                body = v
                                break
                    if not body:
                        body = json.dumps(data, ensure_ascii=False)

                    chunk_id = f"CHK-{document_id}-{idx:03d}"
                    sc = SidecarChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        title=title,
                        content_text=body.strip(),
                        authority=doc_meta.authority,
                        validity=doc_meta.validity,
                        eligibility=doc_meta.determine_eligibility(),
                        related_sor_articles=doc_meta.related_sor_articles,
                        normative_relation=doc_meta.normative_relation,
                        source_kun_id=kun_id,
                        staging_sha256=file_hash,
                        ingested_at=datetime.now(timezone.utc).isoformat()
                    )
                    chunks.append(sc)
                except Exception:
                    continue

        # Pattern 2: If no JSON blocks, fallback to Markdown heading split (###)
        if not chunks:
            sections = re.split(r"\n(?=###?\s+)", content)
            for idx, sec in enumerate(sections, start=1):
                sec_text = sec.strip()
                if len(sec_text) < 30:
                    continue
                lines = sec_text.splitlines()
                title = lines[0].lstrip("#").strip() if lines else f"{document_id} Section {idx}"
                body = "\n".join(lines[1:]).strip() if len(lines) > 1 else sec_text

                chunk_id = f"CHK-{document_id}-{idx:03d}"
                sc = SidecarChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    title=title,
                    content_text=body if len(body) >= 10 else sec_text,
                    authority=doc_meta.authority,
                    validity=doc_meta.validity,
                    eligibility=doc_meta.determine_eligibility(),
                    related_sor_articles=doc_meta.related_sor_articles,
                    normative_relation=doc_meta.normative_relation,
                    source_kun_id=None,
                    staging_sha256=file_hash,
                    ingested_at=datetime.now(timezone.utc).isoformat()
                )
                chunks.append(sc)

        return chunks

    def process_and_persist_sidecar(
        self,
        staged_items: List[Dict[str, Any]],
        batch_id: str,
        approved_by: str = "Alexis"
    ) -> BatchManifest:
        """
        Processes staged documents, extracts chunks, writes multisource_passages.json
        in processed/, creates a BatchManifest, and registers the sidecar batch.
        Guarantees that primary SOR passages are untouched.
        """
        all_chunks: List[SidecarChunk] = []
        ingested_summary: List[Dict[str, Any]] = []

        # Certify primary SOR hash before processing
        primary_sor_path = os.path.join(self.project_root, self.PRIMARY_SOR_PASSAGES)
        sor_baseline_hash = self.calculate_file_sha256(primary_sor_path)

        for item in staged_items:
            doc_id = item["document_id"]
            doc_meta = self.validator.get_document(doc_id)
            if not doc_meta:
                continue

            staging_path = item["staging_path"]
            chunks = self.parse_markdown_kuns(staging_path, doc_id, doc_meta)
            all_chunks.extend(chunks)

            ingested_summary.append({
                "document_id": doc_id,
                "staging_path": staging_path,
                "staging_sha256": item["sha256"],
                "chunks_count": len(chunks),
                "authority": doc_meta.authority.value,
                "validity": doc_meta.validity.value
            })

        # Save processed chunks to isolated destination
        processed_passages_path = os.path.join(self.processed_dir, "multisource_passages.json")
        chunks_data = [c.model_dump() for c in all_chunks]
        with open(processed_passages_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

        passages_sha256 = self.calculate_file_sha256(processed_passages_path)

        # Save processed metadata catalog
        meta_catalog_path = os.path.join(self.processed_dir, "multisource_metadata.json")
        with open(meta_catalog_path, "w", encoding="utf-8") as f:
            json.dump(ingested_summary, f, ensure_ascii=False, indent=2)

        # Build and write BatchManifest
        manifest = BatchManifest(
            batch_id=batch_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            approved_by=approved_by,
            curatorship_log="docs/registro_documental_multifuente_ijf.csv",
            documents_ingested=ingested_summary,
            total_chunks=len(all_chunks),
            sidecar_passages_sha256=passages_sha256,
            primary_sor_corpus_sha256=sor_baseline_hash
        )

        manifest_path = os.path.join(self.manifests_dir, f"{batch_id}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(), f, ensure_ascii=False, indent=2)

        # Update sidecar_registry.json
        registry_data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "active_manifests": [f"{batch_id}.json"],
            "total_sidecar_chunks": len(all_chunks),
            "multisource_passages_sha256": passages_sha256,
            "primary_sor_corpus_sha256": sor_baseline_hash,
            "status": "READY"
        }
        with open(self.sidecar_registry_file, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, ensure_ascii=False, indent=2)

        # Certify primary SOR hash AFTER processing has finished
        sor_post_hash = self.calculate_file_sha256(primary_sor_path)
        if sor_baseline_hash != sor_post_hash:
            raise DocumentValidationError("FATAL: Primary SOR passages file was mutated during sidecar processing!")

        return manifest

    def execute_rollback(self) -> Dict[str, Any]:
        """
        Executes complete, isolated rollback of experimental sidecar artifacts:
        removes staging, manifests, and processed directories under data/corpus_multisource/
        without touching any primary SOR artifacts.
        """
        removed_items = []
        for d in (self.staging_dir, self.manifests_dir, self.processed_dir):
            if os.path.exists(d):
                shutil.rmtree(d)
                removed_items.append(d)

        if os.path.exists(self.sidecar_registry_file):
            os.remove(self.sidecar_registry_file)
            removed_items.append(self.sidecar_registry_file)

        # Re-create empty directory structure
        self._ensure_directories()

        return {
            "status": "ROLLBACK_SUCCESSFUL",
            "removed_paths": removed_items,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
