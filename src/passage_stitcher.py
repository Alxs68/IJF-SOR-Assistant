"""
PassageStitcher — Componente de reconstrucción de continuidad normativa para RRE 3.0 (Fase 2).

Reconstruye pasajes fragmentados entre páginas consecutivas del IJF SOR 2026
preservando la integridad documental, identificadores KUN primarios, números de página,
URLs ancladas y trazabilidad de citas sin alterar el corpus persistente.

Distinción conceptual obligatoria:
1. Continuidad Textual: oraciones o listas divididas físicamente entre el pie de página N y el tope de N+1.
2. Pertenencia Estructural: fragmentos que pertenecen al mismo artículo o subsección normativa.
3. Relación Normativa: referencias cruzadas, excepciones o penalizaciones reguladas en artículos distintos.
   (La relación normativa se maneja exclusivamente a través del Grafo Normativo, SIN concatenación textual).
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PassageStitcher:
    """
    Ensamblador dinámico de fragmentos contiguos en tiempo de ejecución (runtime).
    """

    def __init__(self, passages_by_id: Dict[str, Dict[str, Any]], max_expansion_pages: int = 3):
        self.passages_by_id = passages_by_id
        self.max_expansion_pages = max_expansion_pages
        self.structural_index: Dict[Tuple[str, str, int], List[str]] = {}
        self._build_structural_index()

    def _normalize_heading(self, heading_path: Any) -> str:
        if isinstance(heading_path, list) and heading_path:
            return str(heading_path[0]).strip().lower()
        elif isinstance(heading_path, str):
            return heading_path.strip().lower()
        return ""

    def _normalize_article(self, article_id: Any) -> str:
        if not article_id:
            return ""
        art = str(article_id).strip()
        # No normalizar a vacío; preservar tal cual
        return art

    def _build_structural_index(self):
        """
        Indexa pasajes por (article_id, heading_normalizado, pdf_page_index).
        Excluye expresamente 'GENERAL' y apéndices de historial documental 'H1.1'
        para evitar uniones ambiguas o masivas.
        """
        self.structural_index.clear()
        for pid, p in self.passages_by_id.items():
            art = self._normalize_article(p.get("article_id"))
            page = p.get("pdf_page_index")
            heading = self._normalize_heading(p.get("heading_path"))

            # Excluir 'GENERAL', 'H1.1' o pasajes sin página/artículo válido
            if not art or not page or art.upper() in ["GENERAL", "H1.1", "UNKNOWN", "NONE"]:
                continue

            key = (art, heading, int(page))
            self.structural_index.setdefault(key, []).append(pid)

    def is_eligible_for_stitching(self, passage: Dict[str, Any]) -> bool:
        """
        Determina si un pasaje candidato puede ser expandido con continuidad estructural.
        """
        art = self._normalize_article(passage.get("article_id"))
        page = passage.get("pdf_page_index")
        heading = self._normalize_heading(passage.get("heading_path"))

        if not art or not page or art.upper() in ["GENERAL", "H1.1", "UNKNOWN", "NONE"]:
            return False

        page_num = int(page)
        has_next = (art, heading, page_num + 1) in self.structural_index
        has_prev = (art, heading, page_num - 1) in self.structural_index
        return has_next or has_prev

    def stitch_evidence(self, seed_passage: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconstruye la unidad de evidencia contigua alrededor del pasaje semilla.
        
        Reglas de diseño:
        1. El KUN original (passage_id) se mantiene idéntico como identificador primario.
        2. Los source_spans individuales se registran con su KUN, página y URL respectiva.
        3. Se inserta un marcador sintáctico explícito en el punto de transición de página.
        4. Si el artículo excede max_expansion_pages, se documenta que la reconstrucción es parcial.
        """
        if not self.is_eligible_for_stitching(seed_passage):
            record = dict(seed_passage)
            record["is_stitched"] = False
            record["source_spans"] = [{
                "kun": seed_passage.get("passage_id"),
                "page": seed_passage.get("pdf_page_index"),
                "url": seed_passage.get("source_url") or f"#page={seed_passage.get('pdf_page_index')}"
            }]
            return record

        art = self._normalize_article(seed_passage.get("article_id"))
        heading = self._normalize_heading(seed_passage.get("heading_path"))
        seed_page = int(seed_passage.get("pdf_page_index"))
        seed_pid = seed_passage.get("passage_id")

        # Explorar hacia adelante
        forward_pids: List[str] = []
        is_truncated_forward = False
        for next_p in range(seed_page + 1, seed_page + self.max_expansion_pages + 2):
            matches = self.structural_index.get((art, heading, next_p))
            if matches:
                if len(forward_pids) < self.max_expansion_pages:
                    forward_pids.extend(matches)
                else:
                    is_truncated_forward = True
                    break
            else:
                break

        # Explorar hacia atrás
        backward_pids: List[str] = []
        is_truncated_backward = False
        for prev_p in range(seed_page - 1, max(1, seed_page - self.max_expansion_pages - 2), -1):
            matches = self.structural_index.get((art, heading, prev_p))
            if matches:
                if len(backward_pids) < self.max_expansion_pages:
                    backward_pids.extend(matches)
                else:
                    is_truncated_backward = True
                    break
            else:
                break
        backward_pids.reverse()

        if not forward_pids and not backward_pids:
            record = dict(seed_passage)
            record["is_stitched"] = False
            record["source_spans"] = [{
                "kun": seed_pid,
                "page": seed_page,
                "url": seed_passage.get("source_url") or f"#page={seed_page}"
            }]
            return record

        # Ensamblar lista secuencial completa de pasajes
        all_pids = backward_pids + [seed_pid] + forward_pids
        stitched_text_parts: List[str] = []
        source_spans: List[Dict[str, Any]] = []

        for idx, pid in enumerate(all_pids):
            p = self.passages_by_id[pid]
            p_page = p.get("pdf_page_index")
            p_url = p.get("source_url") or f"#page={p_page}"
            source_spans.append({
                "kun": pid,
                "page": p_page,
                "url": p_url
            })

            p_raw_text = p.get("text_original", "").strip()

            if idx > 0:
                prev_pid = all_pids[idx - 1]
                prev_p = self.passages_by_id[prev_pid]
                prev_page = prev_p.get("pdf_page_index")
                marker = (
                    f"\n\n--- [PAGE BREAK: P{prev_page} -> P{p_page} | "
                    f"KUN: {prev_pid} -> {pid}] ---\n\n"
                )
                stitched_text_parts.append(marker)

            stitched_text_parts.append(p_raw_text)

        full_stitched_text = "".join(stitched_text_parts)

        # Construir registro enriquecido preservando identificadores canónicos
        min_p = min(s["page"] for s in source_spans)
        max_p = max(s["page"] for s in source_spans)
        composite_kun = f"SOR-2026-08-P{min_p:03d}-P{max_p:03d}"

        record = dict(seed_passage)
        record["text_original"] = full_stitched_text
        record["is_stitched"] = True
        record["primary_kun"] = seed_pid  # El KUN semilla original se mantiene como primario
        record["composite_kun"] = composite_kun
        record["source_spans"] = source_spans
        record["stitched_kuns"] = all_pids
        record["is_partial_reconstruction"] = bool(is_truncated_forward or is_truncated_backward)
        if record["is_partial_reconstruction"]:
            record["reconstruction_note"] = (
                f"Reconstrucción parcial limitada a {len(source_spans)} páginas por tope de seguridad "
                f"(max_expansion_pages={self.max_expansion_pages})."
            )

        return record
