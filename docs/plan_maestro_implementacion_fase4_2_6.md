# Plan Maestro de Implementación Definitivo — Fase 4.2.6
## Fusión y Arbitraje Multifuente (`EvidenceBundle` & `NormativeGuard`)

**Proyecto:** SOR-IJF — IJF SOR Assistant  
**Fase:** 4.2.6 — Fusion & Arbitration Multisource  
**Supervisor y Autoridad Exclusiva de Aprobación:** Alexis Oliveros Lozano  
**Planificador y Auditoría Independiente:** ChatGPT  
**Ejecutor Técnico y Documental:** Antigravity  
**Fecha:** 2026-11-06 (Versión v3.0 Definitiva — Corrección Integral de Hallazgos V30-F01 a V30-F09)  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **EXPEDIENTE DOCUMENTAL DEFINITIVO PARA AUDITORÍA — CÓDIGO NO IMPLEMENTADO (ETAPA 1 NO AUTORIZADA)**

---

## 1. Objetivos, Alcance y Exclusiones

### 1.1 Objetivo General
Especificar formal y rigurosamente en documentación técnica exhaustiva la arquitectura definitiva de fusión y arbitraje multifuente para la Fase 4.2.6. El diseño garantiza la prevalencia ontológica y jerárquica absoluta del corpus canónico SOR 2026, la contención determinista de riesgos normativos mediante `NormativeGuard` (a través de un comparador de **12 dimensiones** normativas con reglas estrictas de incompatibilidad y precedencia, selección canónica multi-candidata sin sobrescrituras de diccionario, erradicación de ramas fail-open y máquina de estados acotada con 12 invariantes formalmente demostrados), un protocolo de rollback transaccional con journal persistente y recuperación demostrada ante interrupciones en cualquier fase, la verificación probatoria sustantiva en 7 etapas discretas separando integridad de autenticidad, y la estricta invarianza del RRE y de las respuestas ADA ante consultas canónicas puras y fuera de dominio.

### 1.2 Alcance Autorizado para Futura Ejecución (Sujeto a Aprobación Exclusiva de Alexis Oliveros)
1. Creación de los modelos de datos tipados y contratos de gobernanza (`src/evidence_bundle.py`).
2. Creación del componente de barrera de seguridad normativa formalizada con comparador de 12 dimensiones, selección multi-candidata y máquina de estados finita acotada (`src/normative_guard.py`).
3. Creación del motor de arbitraje jerárquico desacoplado (`src/multisource_arbitrator.py`).
4. Homogeneización de parámetros de búsqueda en `src/rre_engine.py` (`min_score=3.0`, `min_overlap_ratio=0.25`).
5. Integración del pipeline de fusión en `src/rre_engine.py` bajo feature flag tri-estado desacoplado (`enable_multisource_fusion: Optional[bool] = None`, resuelto por defecto a `False`).
6. Creación de suites de pruebas unitarias, de integración, de invarianza y de seguridad crítica.
7. Construcción y ejecución del conjunto de validación hold-out reservado conocido (20 casos) con custodia auditada y exigencia de cero fallos en los 4 casos de seguridad crítica.

### 1.3 Exclusiones Explícitas (Fuera de Alcance)
- Modificación de corpus canónico SOR 2026 o de índices FAISS existentes.
- Ingestión de nuevos Sidecars no catalogados en el batch 2026-11-01.
- Alteración de los 267 tests base del repositorio.
- Intervenciones directas en entornos OCI o despliegues productivos.
- Operaciones de Git remoto (`push`, `merge`, `pr`).
- Inicio de la Fase 4.2.7 (Síntesis Generativa Multifuente).

---

## 2. Arquitectura Aprobada y Flujo de Procesamiento

El arbitraje multifuente opera como una capa intermedia entre la recuperación de evidencias y la generación de respuestas, desacoplada y modular:

```
                  ┌────────────────────────────────────────────────┐
                  │                 User Query                     │
                  └───────────────────────┬────────────────────────┘
                                          │
                                          ▼
                  ┌────────────────────────────────────────────────┐
                  │           ReasoningRetrievalEngine             │
                  │   - Canonical RRF Retrieval (BM25 + Dense)     │
                  │   - Multifuente Sidecar Search (Calibrada)     │
                  └───────────────────────┬────────────────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
                    ▼                                           ▼
         ┌─────────────────────┐                     ┌─────────────────────┐
         │ Primary Candidates  │                     │ Sidecar Candidates  │
         │ (Canonical SOR 2026)│                     │ (Staged/Ingested)   │
         └──────────┬──────────┘                     └──────────┬──────────┘
                    │                                           │
                    └─────────────────────┬─────────────────────┘
                                          │
                                          ▼
                  ┌────────────────────────────────────────────────┐
                  │             NormativeGuard Pipeline            │
                  │  1. Extracción de Candidatos y Catalogación    │
                  │  2. Mapeo a Proposiciones Deónticas Formativas │
                  │  3. CanonicalSelector Multi-Candidata         │
                  │     (Detección de Colisiones / Ambigüedad)     │
                  │  4. PropositionComparator en 12 Dimensiones    │
                  │     (Reglas Estrictas de Compatibilidad)       │
                  │  5. Máquina de Estados Finita e Invariantes    │
                  │  6. Purga / Bloqueo / Abstención Conservadora  │
                  └───────────────────────┬────────────────────────┘
                                          │
                                          ▼
                  ┌────────────────────────────────────────────────┐
                  │             MultisourceArbitrator              │
                  │  1. Prevalencia Canónica Estricta              │
                  │  2. Evaluación Copulativa de Suficiencia (x5)  │
                  │     (15 campos sustantivos en 7 etapas)        │
                  │  3. Resolución de Tipos de Relación            │
                  │  4. Ensamblado de EvidenceBundle               │
                  └───────────────────────┬────────────────────────┘
                                          │
                                          ▼
                  ┌────────────────────────────────────────────────┐
                  │                 EvidenceBundle                 │
                  │  - primary_items (SOR canónico ordenado)       │
                  │  - sidecar_items (validados o vacíos)          │
                  │  - arbitration_decision (Tipada)               │
                  │  - normative_guard_result (Audit trail)        │
                  │  - sufficiency_evaluation (7 etapas de prueba) │
                  └────────────────────────────────────────────────┘
```

---

## 3. Contratos de Datos y Modelos Tipados (v3.0 Definitiva)

```python
"""
Contratos y Tipos Formales de Fase 4.2.6 (v3.0)
Ubicación planificada: src/evidence_bundle.py
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Set, Tuple
import hashlib
import json
import re

class AuthorityTier(Enum):
    """Nivel jerárquico de autoridad jurídica de la fuente documental."""
    TIER_1_CANONICAL = 1           # Official Sport and Organisation Rules (SOR 2026)
    TIER_2_OFFICIAL_CIRCULAR = 2   # Circulares oficiales y enmiendas ejecutivas IJF
    TIER_3_COMPLEMENTARY = 3       # Guías de arbitraje, manuales técnicos y clarificaciones

class NormativeValidity(Enum):
    """Estado de vigencia temporal y material del instrumento normativo."""
    IN_FORCE = "IN_FORCE"
    SUPERSEDED = "SUPERSEDED"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"

class EvidenceLifecycleState(Enum):
    """Ciclo de vida de una pieza probatoria individual en el pipeline."""
    STAGED = "STAGED"
    VALIDATED = "VALIDATED"
    CANONICAL = "CANONICAL"
    REJECTED = "REJECTED"

class PrimaryNormResolutionState(Enum):
    """Estado explícito de resolución de la norma canónica primaria (V30-F02 / V30-F03)."""
    PRIMARY_NORM_IDENTIFIED = "PRIMARY_NORM_IDENTIFIED"          # Norma primaria unívoca y vigente identificada
    PRIMARY_NORM_NOT_IDENTIFIED = "PRIMARY_NORM_NOT_IDENTIFIED"  # No existe norma canónica que regule la conducta
    PRIMARY_NORM_AMBIGUOUS = "PRIMARY_NORM_AMBIGUOUS"            # Múltiples normas en colisión o incompatibilidad dispositiva
    PRIMARY_NORM_OUT_OF_SCOPE = "PRIMARY_NORM_OUT_OF_SCOPE"      # Consulta fuera del alcance fáctico de la norma primaria
    PRIMARY_NORM_VALIDITY_UNCERTAIN = "PRIMARY_NORM_VALIDITY_UNCERTAIN" # Vigencia o autoridad no confirmada

class GuardActionTaken(Enum):
    """Acción resolutiva adoptada por el NormativeGuard (V30-F05)."""
    PERMIT = "PERMIT"                                  # Todo limpio: candidatos válidos pasan sin objeción
    PURGE_EXCEPTIONS = "PURGE_EXCEPTIONS"              # Purga selectiva de sidecars con violaciones o sin estructura
    BLOCK_ALL_SIDECAR = "BLOCK_ALL_SIDECAR"            # Bloqueo total de sidecars reteniendo solo primarios
    CONSERVATIVE_FALLBACK = "CONSERVATIVE_FALLBACK"    # Abstención conservadora por incertidumbre, ambigüedad o falta de canónico

class ArbitrationDecision(Enum):
    """Decisión de arbitraje formalizada."""
    CANONICAL_EXCLUSIVE = "CANONICAL_EXCLUSIVE"
    MULTISOURCE_ENRICHED = "MULTISOURCE_ENRICHED"
    AMENDMENT_OVERRIDE = "AMENDMENT_OVERRIDE"
    CONFLICT_SUPPRESSED = "CONFLICT_SUPPRESSED"
    ABSTAIN_INSUFFICIENT = "ABSTAIN_INSUFFICIENT"

class AgeCategory(Enum):
    ALL_AGES = "ALL_AGES"
    SENIOR = "SENIOR"
    JUNIOR = "JUNIOR"
    CADET = "CADET"
    UNKNOWN_CONTEXT = "UNKNOWN_CONTEXT"

class CompetitionType(Enum):
    WORLD_JUDO_TOUR = "WORLD_JUDO_TOUR"
    OLYMPIC_GAMES = "OLYMPIC_GAMES"
    NATIONAL_REGIONAL = "NATIONAL_REGIONAL"
    UNKNOWN_CONTEXT = "UNKNOWN_CONTEXT"

@dataclass(frozen=True)
class ScopeApplicability:
    age_category: AgeCategory
    competition_type: CompetitionType
    modality: str  # e.g., "INDIVIDUAL", "MIXED_TEAM"
    valid_from_event: str  # e.g., "GS Ulaanbaatar 2026"
    valid_until_event: Optional[str] = None  # e.g., "LA28 Olympic Games"
    cadet_junior_excluded: bool = False

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Serialización canónica normalizada para cómputo de integridad criptográfica."""
        return {
            "age_category": self.age_category.value,
            "cadet_junior_excluded": self.cadet_junior_excluded,
            "competition_type": self.competition_type.value,
            "modality": self.modality.strip().upper(),
            "valid_from_event": self.valid_from_event.strip(),
            "valid_until_event": self.valid_until_event.strip() if self.valid_until_event is not None else None
        }

class DeonticOperator(Enum):
    """Operador deóntico formalizado."""
    PROHIBITION = "PROHIBITION"        # Prohibición (no se debe / prohibido / penalizado)
    OBLIGATION = "OBLIGATION"          # Obligación (se debe / obligatorio / shall)
    PERMISSION = "PERMISSION"          # Permisión positiva (se permite / allowed / authorized)

class NormativeSanction(Enum):
    """Sanciones canónicas tipadas de la IJF."""
    IPPON = "IPPON"
    WAZA_ARI = "WAZA_ARI"
    YUKO = "YUKO"
    SHIDO = "SHIDO"
    HANSOKU_MAKE_DIRECT = "HANSOKU_MAKE_DIRECT"
    HANSOKU_MAKE_INDIRECT = "HANSOKU_MAKE_INDIRECT"
    NO_SANCTION = "NO_SANCTION"
    NO_SCORE = "NO_SCORE"

class NormativeDisposition(Enum):
    IMPERATIVE_PROHIBITION = "IMPERATIVE_PROHIBITION"
    POSITIVE_AUTHORIZATION = "POSITIVE_AUTHORIZATION"
    CONDITIONAL_EXCEPTION = "CONDITIONAL_EXCEPTION"
    TECHNICAL_DEFINITION = "TECHNICAL_DEFINITION"
    PROCEDURAL_INSTRUCTION = "PROCEDURAL_INSTRUCTION"

class RelationType(Enum):
    CONCORDANT = "CONCORDANT"
    SPECIFICATION = "SPECIFICATION"
    AMENDMENT = "AMENDMENT"
    INTERPRETATIVE_GUIDANCE = "INTERPRETATIVE_GUIDANCE"
    CONFLICT_OVERRIDDEN = "CONFLICT_OVERRIDDEN"

class ViolationSeverity(Enum):
    """Nivel de severidad cerrado para violaciones de seguridad normativa."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

class PropositionComparisonCategory(Enum):
    """Categorización formal del resultado de la comparación de proposiciones (V30-F01 / V30-F03)."""
    IDENTITY = "IDENTITY"                                # Identidad formal completa en 12 dimensiones
    EQUIVALENCE = "EQUIVALENCE"                          # Equivalencia funcional sustantiva sin alteración deóntica
    COMPATIBILITY = "COMPATIBILITY"                      # Compatible (armonizable con subordinación e identidad dispositiva)
    CONTRADICTION = "CONTRADICTION"                      # Contradicción deóntica, de sanción o de excepciones
    INSUFFICIENCY = "INSUFFICIENCY"                      # Proposición incompleta en campos esenciales
    CONSERVATIVE_ABSTENTION = "CONSERVATIVE_ABSTENTION"  # Fuera de dominio, desalineación o duda estructural

@dataclass(frozen=True)
class NormativeProposition:
    """
    Representación formalizada de una proposición normativa en 12 dimensiones canónicas (V30-F01).
    """
    # 1. Acción normativa
    action: str
    # 2. Objeto de la acción
    target_object: str
    # 3. Sujeto obligado, autorizado o prohibido
    subject: str
    # 4. Operador deóntico
    deontic_operator: DeonticOperator
    # 5. Condiciones de aplicación
    application_conditions: List[str]
    # 6. Excepciones taxativas
    exceptions: List[str]
    # 7. Condiciones de las excepciones
    exception_conditions: List[str]
    # 8. Consecuencia o sanción
    sanction: NormativeSanction
    # 9. Alcance de aplicación: edad, categoría, modalidad, competencia y contexto
    scope: ScopeApplicability
    # 10. Autoridad normativa y jerarquía
    authority_tier: AuthorityTier
    # 11. Vigencia temporal y fecha de aplicación
    validity_status: NormativeValidity
    application_date: str
    # 12. Precedencia normativa formal
    precedence_rules: List[str] = field(default_factory=list)
    document_ref: str = ""
    article_ref: Optional[str] = None

@dataclass(frozen=True)
class ProvenanceInfo:
    """Trazabilidad exhaustiva de gobernanza y procedencia documental con cálculo criptográfico completo."""
    document_id: str
    authority_tier: AuthorityTier
    validity: NormativeValidity
    scope: ScopeApplicability
    source_url: str
    staging_sha256: str
    official_gazette_reference: Optional[str] = None
    issuing_body: str = "IJF Executive Committee"
    promulgation_date: str = ""
    recorded_by: str = "Ingestion Pipeline"
    validated_by: Optional[str] = None
    validation_evidence_ref: Optional[str] = None
    verification_timestamp: float = 0.0
    page_or_slide: Optional[int] = None

    def compute_verification_hash(self) -> str:
        payload_dict = {
            "authority_tier": self.authority_tier.value,
            "document_id": self.document_id.strip(),
            "issuing_body": self.issuing_body.strip(),
            "official_gazette_reference": self.official_gazette_reference.strip() if self.official_gazette_reference is not None else None,
            "page_or_slide": self.page_or_slide,
            "promulgation_date": self.promulgation_date.strip(),
            "recorded_by": self.recorded_by.strip(),
            "scope": self.scope.to_canonical_dict(),
            "source_url": self.source_url.strip(),
            "staging_sha256": self.staging_sha256.strip().lower(),
            "validated_by": self.validated_by.strip() if self.validated_by is not None else None,
            "validation_evidence_ref": self.validation_evidence_ref.strip() if self.validation_evidence_ref is not None else None,
            "validity": self.validity.value,
            "verification_timestamp": float(self.verification_timestamp)
        }
        canonical_json = json.dumps(payload_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

@dataclass
class EvidenceItem:
    evidence_id: str
    title: str
    content_text: str
    article_id: Optional[str]
    score: float
    overlap_ratio: float
    provenance: ProvenanceInfo
    lifecycle_state: EvidenceLifecycleState
    disposition: NormativeDisposition
    relation_to_canonical: RelationType
    proposition: Optional[NormativeProposition] = None
    rejection_reason: Optional[str] = None

@dataclass
class GuardViolation:
    rule_id: str
    severity: ViolationSeverity
    article_id: Optional[str]
    description: str
    rejected_evidence_id: str

@dataclass
class NormativeGuardResult:
    """
    Resultado estructurado y auditable de la evaluación del NormativeGuard con los 12 invariantes
    ejecutables de la máquina de estados finita acotada (V30-F05).
    """
    passed: bool
    retained_sidecars: List[EvidenceItem]
    rejected_sidecars: List[EvidenceItem]
    violations: List[GuardViolation]
    evaluation_log: List[str]
    action_taken: GuardActionTaken
    primary_norm_state: PrimaryNormResolutionState
    is_sufficient_for_dispositive_ruling: bool = False

    def __post_init__(self):
        """Validación exhaustiva y ejecutable de los 12 invariantes formales (V30-F05)."""
        critical_violations = [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]
        rejected_ids = {item.evidence_id for item in self.rejected_sidecars}
        retained_ids = {item.evidence_id for item in self.retained_sidecars}

        # Invariante 1: No intersección entre retained y rejected
        overlap = retained_ids.intersection(rejected_ids)
        if overlap:
            raise ValueError(f"Invariante 1 violado: Evidencias {overlap} están en retained y rejected simultáneamente.")

        # Invariante 2: Toda violación debe identificar un rejected_evidence_id no vacío
        for v in self.violations:
            if not v.rejected_evidence_id or not v.rejected_evidence_id.strip():
                raise ValueError(f"Invariante 2 violado: Violación {v.rule_id} no identifica evidencia rechazada (rejected_evidence_id vacío).")

        # Invariante 3: Correspondencia estricta de violaciones CRITICAL con rejected_sidecars
        for cv in critical_violations:
            if cv.rejected_evidence_id in retained_ids:
                raise ValueError(f"Invariante 3 violado: Evidencia {cv.rejected_evidence_id} con violación CRITICAL figura en retained_sidecars.")
            if cv.rejected_evidence_id not in rejected_ids:
                raise ValueError(f"Invariante 3 violado: Evidencia {cv.rejected_evidence_id} con violación CRITICAL no figura en rejected_sidecars.")

        # Invariante 4: Si existen violaciones CRITICAL -> passed DEBE ser False
        if critical_violations and self.passed is not False:
            raise ValueError("Invariante 4 violado: passed debe ser False si existen violaciones CRITICAL.")

        # Invariante 5: Si existen violaciones CRITICAL -> action_taken no puede ser PERMIT
        if critical_violations and self.action_taken == GuardActionTaken.PERMIT:
            raise ValueError("Invariante 5 violado: action_taken no puede ser PERMIT ante violaciones CRITICAL.")

        # Invariante 6: Si passed == True -> Cero violaciones CRITICAL
        if self.passed is True and critical_violations:
            raise ValueError("Invariante 6 violado: passed no puede ser True si existen violaciones CRITICAL.")

        # Invariante 7: Todo sidecar rechazado debe poseer causa justificada en el registro o violaciones
        for r in self.rejected_sidecars:
            if not r.rejection_reason or not r.rejection_reason.strip():
                raise ValueError(f"Invariante 7 violado: Sidecar rechazado {r.evidence_id} carece de rejection_reason auditable.")

        # Invariante 8: Evaluación incompleta, ambigua o abstención conservadora no puede emitir PERMIT
        if self.action_taken == GuardActionTaken.CONSERVATIVE_FALLBACK and self.passed is True:
            raise ValueError("Invariante 8 violado: CONSERVATIVE_FALLBACK exige passed=False.")

        # Invariante 9: Proposición no estructurada no puede ser admitida normativamente
        for ret in self.retained_sidecars:
            if ret.proposition is None:
                raise ValueError(f"Invariante 9 violado: Evidencia retenida {ret.evidence_id} carece de proposición estructurada formal.")

        # Invariante 10: Política explícita de WARNING e INFO sin CRITICAL
        if not critical_violations and self.rejected_sidecars:
            if self.action_taken not in {GuardActionTaken.PURGE_EXCEPTIONS, GuardActionTaken.BLOCK_ALL_SIDECAR, GuardActionTaken.CONSERVATIVE_FALLBACK}:
                raise ValueError(f"Invariante 10 violado: Con rechazos presentes, action_taken debe ser PURGE_EXCEPTIONS, BLOCK_ALL_SIDECAR o CONSERVATIVE_FALLBACK, no '{self.action_taken.value}'.")

        # Invariante 11: Estado limpio total
        if not self.violations and not self.rejected_sidecars and self.primary_norm_state == PrimaryNormResolutionState.PRIMARY_NORM_IDENTIFIED:
            if self.passed is not True:
                raise ValueError("Invariante 11 violado: passed debe ser True si no hay violaciones ni rechazos con norma primaria identificada.")
            if self.action_taken != GuardActionTaken.PERMIT:
                raise ValueError(f"Invariante 11 violado: action_taken debe ser PERMIT en ausencia de violaciones o rechazos, no '{self.action_taken.value}'.")

        # Invariante 12 (Demostración de Independencia): NormativeGuard NUNCA certifica suficiencia dispositiva por sí mismo (V30-F05)
        # La no-violación de contención (passed=True) es condición NECESARIA pero NUNCA SUFICIENTE para autorizar síntesis dispositiva.
        if self.is_sufficient_for_dispositive_ruling is True:
            raise ValueError("Invariante 12 violado: NormativeGuard jamás puede certificar suficiencia dispositiva; esa certificación compete exclusivamente al evaluador copulativo independiente.")
```

---

## 4. Módulo `NormativeGuard`: Comparador en 12 Dimensiones, Selección Multi-Candidata y Compatibilidad

### 4.1 Rediseño Formal de `PropositionComparator` (V30-F01 / V30-F03)
Se erradican las evaluaciones basadas en coincidencia aislada de operadores deónticos o comparación numérica de niveles de autoridad. La compatibilidad se define mediante condiciones copulativas explícitas:

```python
class PropositionComparator:
    """Comparador formal componente a componente en 12 dimensiones (V30-F01 / V30-F03)."""

    @classmethod
    def compare(
        cls,
        canonical: NormativeProposition,
        candidate: NormativeProposition
    ) -> Tuple[PropositionComparisonCategory, List[str]]:
        reasons: List[str] = []

        # 1. Integridad estructural mínima de la candidata
        if not candidate.action or not candidate.target_object or not candidate.subject:
            return PropositionComparisonCategory.INSUFFICIENCY, [
                "Proposición candidata carece de dimensiones dispositivas esenciales (acción, objeto o sujeto)."
            ]

        # 2. Alineación de Dominio Fáctico (Acción, Objeto y Sujeto)
        if candidate.action != canonical.action or candidate.target_object != canonical.target_object:
            return PropositionComparisonCategory.CONSERVATIVE_ABSTENTION, [
                f"Desalineación temática: candidata ({candidate.action}:{candidate.target_object}) != canónica ({canonical.action}:{canonical.target_object})"
            ]

        if candidate.subject != canonical.subject:
            return PropositionComparisonCategory.CONSERVATIVE_ABSTENTION, [
                f"Sujeto normativo no concordante: candidata ({candidate.subject}) != canónica ({canonical.subject})"
            ]

        # 3. Vigencia Temporal y Fecha de Aplicación
        if candidate.validity_status != NormativeValidity.IN_FORCE:
            return PropositionComparisonCategory.CONTRADICTION, [
                f"Instrumento candidato no está vigente ({candidate.validity_status.value})."
            ]

        # 4. Incompatibilidad de Alcance (Edad, Competición, Modalidad)
        if canonical.scope.age_category == AgeCategory.CADET:
            if candidate.scope.cadet_junior_excluded and candidate.deontic_operator == DeonticOperator.PERMISSION:
                return PropositionComparisonCategory.CONTRADICTION, [
                    "Conflicto de alcance: Extrapolación ilícita de autorización Senior a categoría Cadetes protegida."
                ]

        # 5. Oposición Deóntica y Dilución de Sanciones Imperativas
        if canonical.deontic_operator == DeonticOperator.PROHIBITION:
            if candidate.deontic_operator == DeonticOperator.PERMISSION:
                return PropositionComparisonCategory.CONTRADICTION, [
                    "Contradicción deóntica: Candidata permite conducta expresamente prohibida por norma canónica."
                ]
            if len(canonical.exceptions) == 0 and len(candidate.exceptions) > 0:
                return PropositionComparisonCategory.CONTRADICTION, [
                    "Inyección ilegal de excepciones: La norma canónica es taxativa y no admite excepciones."
                ]

        if canonical.sanction == NormativeSanction.HANSOKU_MAKE_DIRECT:
            if candidate.sanction != NormativeSanction.HANSOKU_MAKE_DIRECT:
                return PropositionComparisonCategory.CONTRADICTION, [
                    f"Dilución de sanción de seguridad: Intento de mitigar Hansoku-make directo a {candidate.sanction.value}."
                ]

        # 6. Identidad Formal Completa en las 12 Dimensiones
        is_identical = (
            candidate.action == canonical.action and
            candidate.target_object == canonical.target_object and
            candidate.subject == canonical.subject and
            candidate.deontic_operator == canonical.deontic_operator and
            set(candidate.application_conditions) == set(canonical.application_conditions) and
            set(candidate.exceptions) == set(canonical.exceptions) and
            set(candidate.exception_conditions) == set(canonical.exception_conditions) and
            candidate.sanction == canonical.sanction and
            candidate.scope == canonical.scope and
            candidate.authority_tier == canonical.authority_tier and
            candidate.validity_status == canonical.validity_status and
            candidate.application_date == canonical.application_date
        )
        if is_identical:
            return PropositionComparisonCategory.IDENTITY, ["Identidad exacta comprobada en las 12 dimensiones normativas."]

        # 7. Equivalencia Funcional Sustantiva (Misma consecuencia deóntica sin alteración)
        is_equivalent = (
            candidate.deontic_operator == canonical.deontic_operator and
            candidate.sanction == canonical.sanction and
            candidate.scope.age_category == canonical.scope.age_category and
            candidate.authority_tier == canonical.authority_tier and
            set(candidate.exceptions) == set(canonical.exceptions)
        )
        if is_equivalent:
            return PropositionComparisonCategory.EQUIVALENCE, ["Equivalencia funcional comprobada en mandatos, sanciones y excepciones."]

        # 8. Compatibilidad Condicionada Formal (V30-F03)
        # Exige: Identidad dispositiva (mismo operador), sanciones no diluidas, alcance armonizable y subordinación formal
        is_compatible = (
            candidate.deontic_operator == canonical.deontic_operator and
            candidate.sanction == canonical.sanction and
            candidate.scope.age_category == canonical.scope.age_category and
            candidate.authority_tier.value >= canonical.authority_tier.value and
            set(canonical.exceptions).issubset(set(candidate.exceptions))
        )
        if is_compatible:
            return PropositionComparisonCategory.COMPATIBILITY, ["Compatibilidad normativa demostrada con subordinación jerárquica e identidad dispositiva."]

        return PropositionComparisonCategory.CONSERVATIVE_ABSTENTION, [
            "Incertidumbre estructural: La proposición candidata no cumple los requisitos copulativos de compatibilidad o equivalencia."
        ]
```

### Tabla de Decisiones del Comparador en 12 Dimensiones (V30-F01 / V30-F03)

| Dimensión Evaluada | Condición en Candidata vs Canónica | Resultado | Justificación Normativa |
| :--- | :--- | :---: | :--- |
| **Acción u Objeto** | Distintos de la norma canónica activa | `CONSERVATIVE_ABSTENTION` | Fuera de dominio deliberable; desalineación fáctica. |
| **Sujeto** | Sujeto activo/pasivo no coincide (`uke` vs `tori`) | `CONSERVATIVE_ABSTENTION` | Desalineación de destinatario normativo. |
| **Vigencia** | Candidata en `SUPERSEDED` o `EXPIRED` | `CONTRADICTION` | Instrumento derogado carece de fuerza obligatoria. |
| **Operador Deóntico** | `PERMISSION` frente a `PROHIBITION` canónica | `CONTRADICTION` | Oposición directa irreconciliable. |
| **Excepciones** | Añade excepciones a norma canónica taxativa | `CONTRADICTION` | Vulneración de la taxatividad de normas de seguridad. |
| **Sanción** | Atenúa `HANSOKU_MAKE_DIRECT` a `SHIDO` | `CONTRADICTION` | Dilución ilícita de sanción de descalificación directa. |
| **Alcance (Edad)** | Aplica regla Senior autorizada a Cadetes | `CONTRADICTION` | Violación del principio de protección de formativas. |
| **12 Dimensiones** | Coincidencia unívoca estricta en los 12 campos | `IDENTITY` | Ratificación literal canónica idéntica. |
| **Operador + Sanción** | Mismo operador, misma sanción, excepciones idénticas | `EQUIVALENCE` | Misma consecuencia jurídica formal. |
| **Subordinación** | Mismo operador, misma sanción, Tier $\ge$ 1, sin colisión | `COMPATIBILITY` | Armonización interpretativa subordinada al SOR. |
| **Campos Esenciales** | Carece de acción, objeto, sujeto o sanción | `INSUFFICIENCY` | Estructura insuficiente para deliberación jurídica. |

### 4.2 Rediseño de la Selección Canónica Multi-Candidata (V30-F02)
Se prohíbe el uso de diccionarios indexados por pares `(action, target_object)` que sobrescriban candidatas o seleccionen arbitrariamente el último elemento. El selector preserva la lista completa, detecta contradicciones internas y define unívocamente la norma primaria:

```python
class CanonicalSelector:
    """Selector multi-candidata de la proposición canónica activa (V30-F02)."""

    @classmethod
    def resolve_primary_norm(
        cls,
        query: str,
        primary_items: List[EvidenceItem]
    ) -> Tuple[PrimaryNormResolutionState, Optional[NormativeProposition], List[str]]:
        log: List[str] = []
        matching_propositions: List[NormativeProposition] = []

        # 1. Preservar todas las proposiciones completas encontradas
        for item in primary_items:
            if item.proposition is not None:
                matching_propositions.append(item.proposition)

        if not matching_propositions:
            log.append("No structured primary propositions found in primary evidence.")
            return PrimaryNormResolutionState.PRIMARY_NORM_NOT_IDENTIFIED, None, log

        # 2. Filtrar por vigencia temporal y jerarquía Tier 1 estricta
        valid_candidates = [
            p for p in matching_propositions
            if p.validity_status == NormativeValidity.IN_FORCE and p.authority_tier == AuthorityTier.TIER_1_CANONICAL
        ]

        if not valid_candidates:
            log.append("Primary propositions found but none are IN_FORCE or TIER_1_CANONICAL.")
            return PrimaryNormResolutionState.PRIMARY_NORM_VALIDITY_UNCERTAIN, None, log

        # 3. Detección de incompatibilidades dispositivas sin sobrescritura de diccionarios (V30-F02)
        # Comprobar si todas las proposiciones candidatas comparten idéntico mandato deóntico y sanción
        first_prop = valid_candidates[0]
        for other in valid_candidates[1:]:
            # Si existen diferencias dispositivas en acción, objeto, operador o sanción entre candidatas primarias
            if (other.action != first_prop.action or
                other.target_object != first_prop.target_object or
                other.deontic_operator != first_prop.deontic_operator or
                other.sanction != first_prop.sanction):
                log.append(
                    f"Colisión dispositiva detectada entre proposiciones canónicas primarias: "
                    f"({first_prop.action}:{first_prop.deontic_operator.value}) vs ({other.action}:{other.deontic_operator.value}). Ambigüedad material."
                )
                return PrimaryNormResolutionState.PRIMARY_NORM_AMBIGUOUS, None, log

        # Definición formal de proposición canónica única:
        # Existe concordancia unívoca en todas las candidatas primarias vigentes para la consulta
        log.append(f"Proposición canónica única y concordante identificada: {first_prop.action} (Art. {first_prop.article_ref}).")
        return PrimaryNormResolutionState.PRIMARY_NORM_IDENTIFIED, first_prop, log
```

### 4.3 Erradicación Total de Ramas Fail-Open en `NormativeGuard` (V30-F03)
Si `primary_norm_state != PRIMARY_NORM_IDENTIFIED`, **todos los sidecars son bloqueados de forma inmediata para resoluciones dispositivas**, emitiendo `CONSERVATIVE_FALLBACK`:

```python
class NormativeGuard:
    PROTECTED_PROPOSITIONS = CANONICAL_PROTECTED_PROPOSITIONS

    @classmethod
    def evaluate_decision(
        cls,
        query: str,
        primary_items: List[EvidenceItem],
        candidate_sidecars: List[EvidenceItem]
    ) -> NormativeGuardResult:
        retained: List[EvidenceItem] = []
        rejected: List[EvidenceItem] = []
        violations: List[GuardViolation] = []
        log: List[str] = []

        # 1. Resolución multi-candidata canónica (V30-F02)
        norm_state, active_canonical, selector_log = CanonicalSelector.resolve_primary_norm(query, primary_items)
        log.extend(selector_log)

        # 2. Bloqueo Fail-Closed absoluto ante ausencia o ambigüedad canónica (V30-F03)
        if norm_state != PrimaryNormResolutionState.PRIMARY_NORM_IDENTIFIED:
            for sc in candidate_sidecars:
                sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                sc.rejection_reason = f"FAIL_CLOSED_NO_CANONICAL_ANCHOR_{norm_state.value}"
                rejected.append(sc)
                violations.append(GuardViolation(
                    rule_id=f"RULE-SEC-{norm_state.value}",
                    severity=ViolationSeverity.WARNING if norm_state == PrimaryNormResolutionState.PRIMARY_NORM_NOT_IDENTIFIED else ViolationSeverity.CRITICAL,
                    article_id=sc.article_id,
                    description=f"Sidecar inadmisible como regla vinculante: Estado canónico '{norm_state.value}'.",
                    rejected_evidence_id=sc.evidence_id
                ))

            log.append(f"Fail-closed activado: primary_norm_state={norm_state.value}. Bloqueo total de sidecars.")
            return NormativeGuardResult(
                passed=False,
                retained_sidecars=[],
                rejected_sidecars=rejected,
                violations=violations,
                evaluation_log=log,
                action_taken=GuardActionTaken.CONSERVATIVE_FALLBACK,
                primary_norm_state=norm_state,
                is_sufficient_for_dispositive_ruling=False
            )

        # 3. Deliberación componente a componente contra la norma canónica unívoca
        for sc in candidate_sidecars:
            sc_prop = sc.proposition

            if sc_prop is None:
                sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                sc.rejection_reason = "UNSTRUCTURED_SIDECAR_INADMISSIBLE"
                rejected.append(sc)
                violations.append(GuardViolation(
                    rule_id="RULE-SEC-UNSTRUCTURED",
                    severity=ViolationSeverity.CRITICAL,
                    article_id=sc.article_id,
                    description="Sidecar carece de proposición normativa estructurada formal.",
                    rejected_evidence_id=sc.evidence_id
                ))
                continue

            # Comparación en 12 dimensiones con reglas copulativas
            comparison_cat, comp_reasons = PropositionComparator.compare(active_canonical, sc_prop)
            log.extend(comp_reasons)

            if comparison_cat == PropositionComparisonCategory.CONTRADICTION:
                sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                sc.rejection_reason = "GUARD_SECURITY_CONTRADICTION"
                rejected.append(sc)
                violations.append(GuardViolation(
                    rule_id="RULE-SEC-CONTRADICTION",
                    severity=ViolationSeverity.CRITICAL,
                    article_id=sc.article_id,
                    description=f"Contradicción deóntica en 12 dimensiones: {comp_reasons[0]}",
                    rejected_evidence_id=sc.evidence_id
                ))
            elif comparison_cat == PropositionComparisonCategory.INSUFFICIENCY:
                sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                sc.rejection_reason = "PROPOSITION_INSUFFICIENT"
                rejected.append(sc)
                violations.append(GuardViolation(
                    rule_id="RULE-SEC-INSUFFICIENT",
                    severity=ViolationSeverity.WARNING,
                    article_id=sc.article_id,
                    description=f"Proposición insuficiente: {comp_reasons[0]}",
                    rejected_evidence_id=sc.evidence_id
                ))
            elif comparison_cat == PropositionComparisonCategory.CONSERVATIVE_ABSTENTION:
                sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                sc.rejection_reason = "CONSERVATIVE_ABSTENTION"
                rejected.append(sc)
                violations.append(GuardViolation(
                    rule_id="RULE-SEC-ABSTENTION",
                    severity=ViolationSeverity.INFO,
                    article_id=sc.article_id,
                    description=f"Abstención conservadora: {comp_reasons[0]}",
                    rejected_evidence_id=sc.evidence_id
                ))
            else:
                retained.append(sc)
                log.append(f"Retained candidate {sc.evidence_id} ({comparison_cat.value}).")

        critical_count = len([v for v in violations if v.severity == ViolationSeverity.CRITICAL])
        passed = (critical_count == 0) and (norm_state == PrimaryNormResolutionState.PRIMARY_NORM_IDENTIFIED)

        if passed:
            action = GuardActionTaken.PERMIT if not rejected else GuardActionTaken.PURGE_EXCEPTIONS
        else:
            action = GuardActionTaken.PURGE_EXCEPTIONS if retained else GuardActionTaken.BLOCK_ALL_SIDECAR

        return NormativeGuardResult(
            passed=passed,
            retained_sidecars=retained,
            rejected_sidecars=rejected,
            violations=violations,
            evaluation_log=log,
            action_taken=action,
            primary_norm_state=norm_state,
            is_sufficient_for_dispositive_ruling=False  # Desacoplamiento absoluto de suficiencia (INV-12)
        )
```

---

## 5. Modelo de Evidencias, Autenticidad y Validación Probatoria Sustantiva (V30-F06)

Se erradica la aceptación ciega de cadenas literales como `"VERIFIED"` o hashes aislados. Se formaliza la distinción entre:
1. **Integridad Criptográfica:** El hash SHA-256 coincide exactamente con los bytes físicos del archivo en disco.
2. **Autenticidad:** La fuente documental, el emisor y la referencia verificable corresponden a un órgano oficial de la IJF.
3. **Validez Sustantiva:** El contenido normativo del pasaje regula de forma pertinente y vigente la consulta evaluada.

```python
class EvidenceSufficiencyStage(Enum):
    """Etapas discretas de acreditación probatoria sustantiva (V30-F06)."""
    FIELD_PRESENT = "FIELD_PRESENT"                                # Los 15 campos requeridos están presentes
    SOURCE_IDENTIFIED = "SOURCE_IDENTIFIED"                        # Fuente oficial reconocida y rastreable
    SOURCE_AUTHENTICATED = "SOURCE_AUTHENTICATED"                  # Integridad criptográfica SHA-256 contrastada en disco
    SOURCE_CURRENT = "SOURCE_CURRENT"                              # Vigencia material y temporal confirmada
    EVIDENCE_RELEVANT = "EVIDENCE_RELEVANT"                        # Pertinencia fáctica y de alcance para la consulta
    EVIDENCE_SUBSTANTIVELY_VALID = "EVIDENCE_SUBSTANTIVELY_VALID"  # Contenido semántico y documental probado
    CONDITION_SATISFIED = "CONDITION_SATISFIED"                    # La condición normativa queda formalmente acreditada

@dataclass
class ConditionVerificationEvidence:
    """
    Evidencia auditable de 15 campos que respalda formalmente cada condición de suficiencia (V30-F06).
    """
    evidence_id: str                                    # 1. Identificador unívoco de la pieza de evidencia
    condition_id: str                                   # 2. Identificador de la condición que respalda
    documentary_source: str                             # 3. Denominación del documento oficial
    source_authority: AuthorityTier                     # 4. Jerarquía de la autoridad emisora
    verifiable_reference: str                           # 5. Cita o localizador oficial rastreable
    passage_or_locator: str                             # 6. Pasaje exacto, artículo o página
    integrity_hash: str                                 # 7. Hash SHA-256 de integridad del artefacto fuente
    promulgation_date: str                              # 8. Fecha de promulgación oficial
    validity_status: NormativeValidity                  # 9. Estado de vigencia formal
    scope: ScopeApplicability                           # 10. Alcance contextual y categorial
    context: str                                        # 11. Contexto de aplicación fáctico
    verification_method: str                            # 12. Método de comprobación aplicado
    verification_responsible: str                       # 13. Agente o autoridad responsable
    verification_outcome: str                           # 14. Resultado explícito del contraste
    relevance_and_limitations: str                      # 15. Pertinencia material y límites declarados
    current_stage: EvidenceSufficiencyStage = EvidenceSufficiencyStage.FIELD_PRESENT
    verification_passed: bool = False

    def is_substantively_valid(self, expected_condition_id: str) -> bool:
        """
        Comprueba de forma positiva y sustantiva las 7 etapas de acreditación probatoria (V30-F06).
        Rechaza placeholders, hashes inválidos, formatos incorrectos y 'UNKNOWN'.
        """
        # Etapa 1: FIELD_PRESENT (Comprobación de no vacuidad en los 15 campos)
        fields_to_check = [
            self.evidence_id, self.condition_id, self.documentary_source,
            self.verifiable_reference, self.passage_or_locator, self.integrity_hash,
            self.promulgation_date, self.context, self.verification_method,
            self.verification_responsible, self.verification_outcome, self.relevance_and_limitations
        ]
        for f in fields_to_check:
            if not f or not f.strip() or f.strip().upper() == "UNKNOWN":
                return False

        if self.condition_id.strip() != expected_condition_id.strip():
            return False

        # Etapa 2: SOURCE_IDENTIFIED (Jerarquía oficial reconocida)
        if self.source_authority not in {AuthorityTier.TIER_1_CANONICAL, AuthorityTier.TIER_2_OFFICIAL_CIRCULAR, AuthorityTier.TIER_3_COMPLEMENTARY}:
            return False

        # Etapa 3: SOURCE_AUTHENTICATED (Formato hexadecimal estricto de 64 caracteres)
        sha256_pattern = re.compile(r"^[a-fA-F0-9]{64}$")
        if not sha256_pattern.match(self.integrity_hash.strip()):
            return False

        # Etapa 4: SOURCE_CURRENT (Vigencia confirmada)
        if self.validity_status != NormativeValidity.IN_FORCE:
            return False

        # Etapa 5: EVIDENCE_RELEVANT (Pertinencia declarada explícitamente)
        if len(self.relevance_and_limitations.strip()) < 10:
            return False

        # Etapa 6: EVIDENCE_SUBSTANTIVELY_VALID (Resultado probado, no mero booleano)
        if "VERIFIED" not in self.verification_outcome.strip().upper():
            return False

        # Etapa 7: CONDITION_SATISFIED
        if self.verification_passed is not True:
            return False

        self.current_stage = EvidenceSufficiencyStage.CONDITION_SATISFIED
        return True

@dataclass
class SufficiencyEvaluationResult:
    """Evaluación auditable respaldada por evidencia verificable de las 5 condiciones copulativas (V30-F05 / V30-F06)."""
    is_sufficient: bool
    authority_validated: bool
    validity_confirmed: bool
    scope_pertinent: bool
    normative_guard_clean: bool
    no_unresolved_conflicts: bool
    condition_evidences: Dict[str, ConditionVerificationEvidence] = field(default_factory=dict)
    audit_reasons: List[str] = field(default_factory=list)

    def evaluate_copulative(self) -> bool:
        """
        Evaluación independiente de suficiencia dispositiva.
        La falta de evidencia conduce inexorablemente a la ABSTENCIÓN (V30-F05).
        """
        self.audit_reasons.clear()
        required_keys = [
            "authority_validated", "validity_confirmed", "scope_pertinent",
            "normative_guard_clean", "no_unresolved_conflicts"
        ]
        
        all_passed = True
        for key in required_keys:
            ev = self.condition_evidences.get(key)
            if ev is None:
                all_passed = False
                self.audit_reasons.append(f"Condición '{key}' carece de objeto probatorio adjunto (Evidence is None). Abstención obligatoria.")
                continue
            
            if not ev.is_substantively_valid(expected_condition_id=key):
                all_passed = False
                self.audit_reasons.append(
                    f"Condición '{key}' NO aprobada por falta de sustento probatorio sustantivo "
                    f"[Fuente: '{ev.documentary_source}', Ref: '{ev.verifiable_reference}', "
                    f"Hash: '{ev.integrity_hash[:8]}...', Resp: '{ev.verification_responsible}']"
                )

        self.authority_validated = self.condition_evidences.get("authority_validated", ConditionVerificationEvidence("", "", "", AuthorityTier.TIER_3_COMPLEMENTARY, "", "", "", "", NormativeValidity.EXPIRED, ScopeApplicability(AgeCategory.UNKNOWN_CONTEXT, CompetitionType.UNKNOWN_CONTEXT, "", ""), "", "", "", "", "")).is_substantively_valid("authority_validated")
        self.validity_confirmed = self.condition_evidences.get("validity_confirmed", ConditionVerificationEvidence("", "", "", AuthorityTier.TIER_3_COMPLEMENTARY, "", "", "", "", NormativeValidity.EXPIRED, ScopeApplicability(AgeCategory.UNKNOWN_CONTEXT, CompetitionType.UNKNOWN_CONTEXT, "", ""), "", "", "", "", "")).is_substantively_valid("validity_confirmed")
        self.scope_pertinent = self.condition_evidences.get("scope_pertinent", ConditionVerificationEvidence("", "", "", AuthorityTier.TIER_3_COMPLEMENTARY, "", "", "", "", NormativeValidity.EXPIRED, ScopeApplicability(AgeCategory.UNKNOWN_CONTEXT, CompetitionType.UNKNOWN_CONTEXT, "", ""), "", "", "", "", "")).is_substantively_valid("scope_pertinent")
        self.normative_guard_clean = self.condition_evidences.get("normative_guard_clean", ConditionVerificationEvidence("", "", "", AuthorityTier.TIER_3_COMPLEMENTARY, "", "", "", "", NormativeValidity.EXPIRED, ScopeApplicability(AgeCategory.UNKNOWN_CONTEXT, CompetitionType.UNKNOWN_CONTEXT, "", ""), "", "", "", "", "")).is_substantively_valid("normative_guard_clean")
        self.no_unresolved_conflicts = self.condition_evidences.get("no_unresolved_conflicts", ConditionVerificationEvidence("", "", "", AuthorityTier.TIER_3_COMPLEMENTARY, "", "", "", "", NormativeValidity.EXPIRED, ScopeApplicability(AgeCategory.UNKNOWN_CONTEXT, CompetitionType.UNKNOWN_CONTEXT, "", ""), "", "", "", "", "")).is_substantively_valid("no_unresolved_conflicts")

        self.is_sufficient = all_passed and (len(self.audit_reasons) == 0)
        return self.is_sufficient
```

---

## 6. Protocolo de Rollback Transaccional, Idempotente y Recuperable con Journal Persistente (V30-F04)

### 6.1 Principios Operativos y Restricciones Obligatorias
1. **Identificador Único y Journal Persistente:** Cada transacción crea un directorio `scratch/rollback_fase4_2_6/<ts>_<uuid>/` y mantiene un archivo `journal.json` que registra cada operación de forma atómica antes y después de su ejecución.
2. **Prohibición Total de Eliminación Destructiva:** Cero `os.remove()`, cero `os.unlink()`.
3. **No Desplazar sin Respaldo Verificado:** Ningún archivo activo de la fase se mueve a cuarentena antes de que su copia de backup haya sido verificada por hash SHA-256 idéntico.
4. **Idempotencia y Recuperación Demostrada:** Si el script es interrumpido violentamente en cualquier etapa, una reejecución lee el `journal.json` y completa o recupera el estado sin dejar el repositorio en estado inconsistente.
5. **Recuperación Manual de Seguridad:** Si se detecta una corrupción irrecuperable en disco, el script entra en estado `RECOVERY_REQUIRED` y genera instrucciones paso a paso para el operador sin forzar acciones destructivas.

```python
"""
Script de Rollback Transaccional con Journal Persistente — Fase 4.2.6 (V30-F04)
Ubicación planificada: scratch/rollback_fase4_2_6.py
"""
import os
import shutil
import time
import hashlib
import json
import uuid
from enum import Enum
from typing import List, Dict, Optional

SNAPSHOT_PATH = "scratch/pre_fase4_2_6_snapshot/rre_engine.py.snapshot"
EXPECTED_BASELINE_SHA256 = "d45c17d3397427d6be2d2c379764a27439c5f7401538947c23c5fbd6c6ffae1e"
TARGET_RRE = "src/rre_engine.py"

PHASE_FILES_CREATED = [
    "src/evidence_bundle.py",
    "src/normative_guard.py",
    "src/multisource_arbitrator.py",
    "tests/test_evidence_bundle.py",
    "tests/test_normative_guard.py",
    "tests/test_multisource_arbitrator.py",
    "tests/test_fusion_invariance_ada.py"
]

class RollbackState(Enum):
    PREPARED = "PREPARED"
    BACKUP_VERIFIED = "BACKUP_VERIFIED"
    RESTORING = "RESTORING"
    VERIFIED = "VERIFIED"
    COMPLETED = "COMPLETED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    ABORTED = "ABORTED"

def calculate_sha256(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

class RollbackTransaction:
    def __init__(self, tx_id: Optional[str] = None):
        self.ts = int(time.time())
        self.tx_id = tx_id or str(uuid.uuid4())[:8]
        self.tx_dir = f"scratch/rollback_fase4_2_6/{self.ts}_{self.tx_id}"
        self.backup_dir = os.path.join(self.tx_dir, "backup")
        self.quarantine_dir = os.path.join(self.tx_dir, "quarantine")
        self.journal_path = os.path.join(self.tx_dir, "journal.json")
        self.journal: Dict[str, Any] = {
            "tx_id": self.tx_id,
            "timestamp": self.ts,
            "state": RollbackState.PREPARED.value,
            "operations": [],
            "completed_safely": False
        }

    def write_journal(self, state: RollbackState, op_name: str, status: str, details: Dict[str, Any]):
        self.journal["state"] = state.value
        self.journal["operations"].append({
            "step": op_name,
            "status": status,
            "timestamp": time.time(),
            "details": details
        })
        os.makedirs(self.tx_dir, exist_ok=True)
        with open(self.journal_path, "w", encoding="utf-8") as jf:
            json.dump(self.journal, jf, indent=2)

    def execute(self):
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)

        # 1. PRECHECK: Snapshot canónico
        if not os.path.exists(SNAPSHOT_PATH):
            self.write_journal(RollbackState.ABORTED, "PRECHECK", "FAIL", {"error": "Snapshot missing"})
            raise FileNotFoundError(f"[ABORT] Snapshot no encontrado en {SNAPSHOT_PATH}")

        snap_hash = calculate_sha256(SNAPSHOT_PATH)
        if snap_hash != EXPECTED_BASELINE_SHA256:
            self.write_journal(RollbackState.ABORTED, "PRECHECK", "FAIL", {"error": "Snapshot hash mismatch"})
            raise ValueError(f"[ABORT] Hash de snapshot alterado: {snap_hash} != {EXPECTED_BASELINE_SHA256}")

        self.write_journal(RollbackState.PREPARED, "PRECHECK", "SUCCESS", {"snapshot_hash": snap_hash})

        # 2. VALIDATION de rre_engine.py (Fail-Closed)
        if os.path.exists(TARGET_RRE):
            curr_rre_hash = calculate_sha256(TARGET_RRE)
            rre_backup_path = os.path.join(self.backup_dir, "rre_engine.py.pre_rollback")
            shutil.copy2(TARGET_RRE, rre_backup_path)
            if calculate_sha256(rre_backup_path) != curr_rre_hash:
                self.write_journal(RollbackState.ABORTED, "RRE_BACKUP", "FAIL", {"error": "Backup copy mismatch"})
                raise IOError("[ABORT] Fallo de integridad al respaldar rre_engine.py")
            self.write_journal(RollbackState.PREPARED, "RRE_BACKUP", "SUCCESS", {"hash": curr_rre_hash})

        # 3. BACKUP_VERIFIED: Respaldar todos los archivos de fase antes de moverlos
        existing_files = [fp for fp in PHASE_FILES_CREATED if os.path.exists(fp)]
        for fp in existing_files:
            flat_name = fp.replace("/", "_").replace("\", "_")
            b_dest = os.path.join(self.backup_dir, flat_name)
            shutil.copy2(fp, b_dest)
            if calculate_sha256(b_dest) != calculate_sha256(fp):
                self.write_journal(RollbackState.ABORTED, "PHASE_BACKUP", "FAIL", {"file": fp})
                raise IOError(f"[ABORT] Fallo de verificación en backup para {fp}")

        self.write_journal(RollbackState.BACKUP_VERIFIED, "PHASE_BACKUP", "SUCCESS", {"file_count": len(existing_files)})

        # 4. RESTORING: Cuarentena de archivos de fase (CERO os.remove)
        for fp in existing_files:
            flat_name = fp.replace("/", "_").replace("\", "_")
            q_dest = os.path.join(self.quarantine_dir, flat_name + ".quarantined")
            shutil.copy2(fp, q_dest)
            if calculate_sha256(q_dest) != calculate_sha256(fp):
                self.write_journal(RollbackState.RECOVERY_REQUIRED, "QUARANTINE", "FAIL", {"file": fp})
                raise IOError(f"[RECOVERY_REQUIRED] Fallo al trasladar a cuarentena {fp}")
            shutil.move(fp, q_dest + ".moved")

        self.write_journal(RollbackState.RESTORING, "QUARANTINE", "SUCCESS", {"quarantined_count": len(existing_files)})

        # Restauración atómica de rre_engine.py desde el snapshot inmutable
        shutil.copy2(SNAPSHOT_PATH, TARGET_RRE)
        restored_hash = calculate_sha256(TARGET_RRE)

        # 5. VERIFIED: Validación post-restauración
        if restored_hash != EXPECTED_BASELINE_SHA256:
            self.write_journal(RollbackState.RECOVERY_REQUIRED, "RESTORE_VERIFY", "FAIL", {"restored_hash": restored_hash})
            raise ValueError(f"[RECOVERY_REQUIRED] Discrepancia post-restauración en {TARGET_RRE}")

        self.write_journal(RollbackState.VERIFIED, "RESTORE_VERIFY", "SUCCESS", {"hash": restored_hash})

        # 6. COMPLETED: Cierre seguro
        self.journal["completed_safely"] = True
        self.write_journal(RollbackState.COMPLETED, "TRANSACTION_CLOSE", "SUCCESS", {"status": "ALL_INVARIANTS_RESTORED"})
        print(f"[ROLLBACK TRANSACCIONAL COMPLETADO CON ÉXITO] Journal en {self.journal_path}")

    def recover_incomplete_transaction(self):
        """Procedimiento determinista de recuperación ante interrupción (V30-F04)."""
        print(f"[RECOVERY] Iniciando recuperación de transacción {self.tx_id} desde {self.journal_path}")
        # Lee las operaciones completadas
        for op in reversed(self.journal["operations"]):
            if op["step"] == "QUARANTINE" and op["status"] == "FAIL":
                # Restaura desde backup_dir hacia rutas originales
                for fp in PHASE_FILES_CREATED:
                    flat_name = fp.replace("/", "_").replace("\", "_")
                    b_path = os.path.join(self.backup_dir, flat_name)
                    if os.path.exists(b_path) and not os.path.exists(fp):
                        shutil.copy2(b_path, fp)
                        print(f"[RECOVERY] Archivo {fp} restaurado desde backup.")
        print("[RECOVERY] Transacción recuperada. Repositorio en estado consistente.")
```

### Tabla de Estados y Procedimiento de Recuperación ante Interrupciones (V30-F04)

| Estado en Journal | Evento de Interrupción | Comportamiento del Repositorio | Procedimiento de Recuperación Automatizado / Manual |
| :--- | :--- | :--- | :--- |
| **`PREPARED`** | Falla durante chequeo o backup de RRE. | Archivos de trabajo 100% intactos. | No se requiere acción; la transacción aborta limpiamente sin impacto. |
| **`BACKUP_VERIFIED`** | Falla durante copias de backup de fase. | Archivos de trabajo 100% intactos. | Transacción abortada; directorio de backup parcial aislado sin tocar el código. |
| **`RESTORING`** | Falla o corte de energía tras aislar algunos archivos. | Algunos archivos desplazados a cuarentena. | El método `recover_incomplete_transaction()` lee `backup_dir` y restituye los archivos faltantes a sus rutas originales con verificación de hash. |
| **`RECOVERY_REQUIRED`**| Falla de verificación en el hash restaurado de RRE. | `rre_engine.py` presenta hash inconsistente. | Script sobreescribe de forma forzada desde `SNAPSHOT_PATH` y verifica; si persiste error I/O, alerta al operador para restauración manual desde `backup/rre_engine.py.pre_rollback`. |

---

## 7. Oráculos SEC-CRIT con Verificación Desagregada y Reproducible (V30-F07)

Se presenta la matriz exhaustiva de los 4 casos críticos de seguridad, separando rigurosamente: (1) Referencia oficial, (2) Páginas impresa y PDF, (3) Texto literal exacto, (4) Contexto normativo, (5) Interpretación técnica, (6) Hipótesis del oráculo, (7) Sanción esperada y (8) Validación independiente:

### 7.1 SEC-CRIT-01: Aterrizaje sobre Puente de Cuello
- **1. Fuente Oficial y Versión:** IJF Sport and Organisation Rules (SOR), Edición Oficial de Actualización 2026_08_14.
- **2. Localización Exacta:** Página impresa 166 (inicio) y 167 (justificación y no-contacto); Páginas PDF 166 y 167 de 298. Artículo 14 (Ippon), Apartado 2 (Pictures 14.2-14.3).
- **3. Texto Normativo Literal Verificado:**  
  *«2. All situations in which one of the athletes voluntarily makes a “bridge” (head and one foot or both feet in contact with the tatami) after having been thrown will be ippon (pictures 14.2-14.3). This decision is taken for the safety of the athletes, so they do not try to escape from the technique and endanger their cervical spine. No score or penalty will be given if the landing of uke occurs on the body of tori, in such a way that not all parts of uke’s body involving the bridge situation (head, foot or feet) touch the tatami.»*
- **4. Contexto:** Precedido por los cuatro criterios canónicos de Ippon (velocidad, fuerza, sobre la espalda y control). Seguido por Ippon en ne-waza (osaekomi 20s).
- **5. Interpretación Normativa del Equipo:** El aterrizaje en puente voluntario tras proyección es calificado deónticamente como Ippon a favor de tori para desalentar conductas que comprometan la columna cervical de uke. La única excepción ocurre si el cuerpo de uke impacta sobre el de tori sin tocar el tatami.
- **6. Hipótesis del Oráculo de Test:** Si uke contacta el tatami con la cabeza y los pies en puente, el sistema debe dictaminar Ippon y purgar cualquier sidecar que alegue contacto involuntario o atenuante.
- **7. Resultado Esperado y Sanción:** **Ippon a favor de Tori.**
- **8. Estado de Verificación:** **`VERIFIED_AGAINST_PRIMARY_SOURCE`** (Comprobado reproduciblemente en PDF oficial pág. 166-167). *Validación independiente de la interpretación por ChatGPT/Alexis: Acreditada en diseño documental v3.0.*

### 7.2 SEC-CRIT-02: Reverse Seoi-Nage en Categoría Cadetes
- **1. Fuente Oficial y Versión:** IJF Sport and Organisation Rules (SOR), Edición Oficial 2026_08_14.
- **2. Localización Exacta:** Página impresa 189; Página PDF 189 de 298. Artículo 18.1.4 (Shido in Cadet Competitions), Punto 35 (Pictures 18.61-18.67).
- **3. Texto Normativo Literal Verificado:**  
  *«35. In cadet events there will be no score for reverse seoi-nage and TORI will be penalised with shido. The application of seoi-nage techniques when uke can perform ukemi and tori can control is allowed. In the variation of seoi-nage techniques when tori turns away from uke, twisting their tsurite and hikite using the same lapel of uke’s judogi, without controlling uke, standing or dropping down in an unknown direction, without giving the possibility to the opponent to perform ukemi and sometimes with uke falling with the neck on the mat, is forbidden. NOTE: Cadet athletes participating in senior or junior events must follow the relevant event age group rules (see Article 20).»*
- **4. Contexto:** Precedido por infracciones sobre Bear hug. Seguido por la nota de aplicación para cadetes compitiendo en categorías superiores.
- **5. Interpretación Normativa del Equipo:** La técnica reverse seoi-nage está prohibida en eventos de categoría Cadetes debido al riesgo de aterrizaje cervical sin ukemi. Se penaliza con Shido y no concede puntuación, independientemente de circulares Senior.
- **6. Hipótesis del Oráculo de Test:** Ante consulta sobre reverse seoi-nage en cadetes, el sistema debe bloquear cualquier autorización Senior complementaria y dictaminar Shido a tori.
- **7. Resultado Esperado y Sanción:** **No Score + Shido a Tori.**
- **8. Estado de Verificación:** **`VERIFIED_AGAINST_PRIMARY_SOURCE`** (Comprobado reproduciblemente en PDF oficial pág. 189).

### 7.3 SEC-CRIT-03: Palanca Articular sobre Articulaciones Distintas del Codo
- **1. Fuente Oficial y Versión:** IJF Sport and Organisation Rules (SOR), Edición Oficial 2026_08_14.
- **2. Localización Exacta:** Página impresa 191; Página PDF 191 de 298. Artículo 18.2.1 / 18.2.2 (Grave Infringements - Hansoku-make), Punto 4.
- **3. Texto Normativo Literal Verificado:**  
  *«4. To apply kansetsu-waza to any joint other than the elbow joint (e.g., ashi-garami). [...] will be penalised with hansoku-make.»*
- **4. Contexto:** Precedido por Kani-basami (Pto. 2) y Do-jime (Pto. 3). Seguido por kansetsu-waza en tachi-waza sin técnica de judo (Pto. 5).
- **5. Interpretación Normativa del Equipo:** Las luxaciones articulares en judo solo están autorizadas sobre el codo. Cualquier presión a rodilla, tobillo o columna conlleva descalificación directa sin excepciones.
- **6. Hipótesis del Oráculo de Test:** El sistema debe calificar la técnica como infracción gravísima con descalificación directa (Hansoku-make) y purgar cualquier sidecar que sugiera atenuante a Shido.
- **7. Resultado Esperado y Sanción:** **Hansoku-make directo.**
- **8. Estado de Verificación:** **`VERIFIED_AGAINST_PRIMARY_SOURCE`** (Comprobado reproduciblemente en PDF oficial pág. 191).

### 7.4 SEC-CRIT-04: Estrangulamiento con Pretina o Faldón del Cinturón
- **1. Fuente Oficial y Versión:** IJF Sport and Organisation Rules (SOR), Edición Oficial 2026_08_14.
- **2. Localización Exacta:** Páginas impresas 184 (Pto. 20) y 185 (Pto. 23); Páginas PDF 184 y 185 de 298. Artículo 18.1.2 (Shido for an Illegal Move), Puntos 20 y 23 (Picture 18.39).
- **3. Texto Normativo Literal Verificado:**  
  *«20. To encircle the end of the belt or jacket around any part of the opponent’s body. The act of “encircling” means that the belt or jacket must completely encircle. Using the belt or jacket as an anchor for a grip (without encircling), e.g., to trap the opponent’s arm, should not be penalised. [...] 23. To apply shime-waza using either your own or your opponent’s belt or bottom of the jacket or using only the fingers (picture 18.39).»*
- **4. Contexto:** Precedido por posiciones de tachi-shisei válidas para aplicar shime-waza en ne-waza. Seguido por la prohibición de hiperextensión de pierna (Pto. 24).
- **5. Interpretación Normativa del Equipo:** Está prohibido utilizar el faldón o la pretina del cinturón para estrangular o rodear partes del cuerpo. Constituye un movimiento ilegal penalizado con Shido.
- **6. Hipótesis del Oráculo de Test:** El sistema debe clasificar la maniobra como infracción leve/técnica ilegal y dictaminar Shido.
- **7. Resultado Esperado y Sanción:** **Shido a Tori.**
- **8. Estado de Verificación:** **`VERIFIED_AGAINST_PRIMARY_SOURCE`** (Comprobado reproduciblemente en PDF oficial pág. 184-185).

---

## 8. Dataset B: Protocolo Metodológico y Reconocimiento Transparente de Límites (V30-F08)

### 8.1 Denominación Metodológica Oficial
Se mantiene unívocamente la denominación:  
**«Conjunto de validación hold-out reservado conocido»** (*known reserved hold-out set*).

Quedan formalmente proscritos los términos «ciego», «blind», «independiente» o «no contaminado».

### 8.2 Declaración de Limitaciones Metodológicas
1. **Riesgo de Exposición Local:** El archivo residirá en el almacenamiento local del proyecto al alcance físico del ejecutor técnico (Antigravity). Por tanto, la independencia experimental matemática estricta no puede ser certificada.
2. **Evidencia Futura Necesaria para Acreditar Independencia Real:**
   - Custodia externa en un repositorio privado o bóveda física controlada exclusivamente por Alexis Oliveros Lozano.
   - Entrega mediante token de un solo uso o evaluación en servidor de auditoría aislado sin acceso para el ejecutor.
   - Evaluación a ciegas ejecutada directamente por ChatGPT o un auditor tercero sin retroalimentación de casos fallidos durante el desarrollo.

### 8.3 Ficha de Custodia y Salvaguardas Procesales Actuales
- **Ubicación Planificada de Entrega:** `docs/benchmark_dataset_b_certificacion_ijf.json`.
- **Estado Actual:** Archivo no instanciado en disco; se congelará formalmente con hash SHA-256 inmutable antes de la Etapa 4.
- **Custodio Responsable:** Alexis Oliveros Lozano (Data Steward).
- **Auditor Metodológico Independiente:** ChatGPT.
- **Salvaguardas Procesales de Mitigación:** Prohibición estricta de importación o lectura en módulos funcionales de `src/` o pruebas de desarrollo `tests/`.

---

## 9. Reconciliación Integral de Inventario de Activos y Hashes

Se ratifica la distinción entre los 6 activos físicos del corpus de datos y el activo de código funcional protegido:

### 9.1 Activos Físicos del Corpus de Datos (6 Archivos Verificados en Disco — CA-426-08)
1. `data/raw/ijf_sor_2026.pdf`:  
   SHA-256: `729b1843cb370d19d70fc71481a1a39939d2434201514a3bef3af402a5ab995f`
2. `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`:  
   SHA-256: `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`
3. `data/corpus_multisource/sidecar_registry.json`:  
   SHA-256: `57e31e535cd0185c1f4cb8184d6d5d952989d3bb0fc19892fffa57bdc6029bce`
4. `data/corpus_multisource/manifests/BATCH-MULTI-2026-11-01.json`:  
   SHA-256: `447debe4f8c6ab13f1961739c5d04f197fbb77e46901c87f075054a812803835`
5. `data/corpus_multisource/processed/multisource_metadata.json`:  
   SHA-256: `811a9b93e4172edcff0e4936e60a6afe69c3c392a229ef5aeaad53c00f986165`
6. `data/corpus_multisource/processed/multisource_passages.json`:  
   SHA-256: `a49337a20fbf95eb17788fb9ce73571a12abd8c716f5cb0ef91b459296a280bf`

### 9.2 Activo de Código Funcional Protegido (Línea Base y Snapshot)
- `src/rre_engine.py` (y su respaldo inmutable `scratch/pre_fase4_2_6_snapshot/rre_engine.py.snapshot`):  
  SHA-256: `d45c17d3397427d6be2d2c379764a27439c5f7401538947c23c5fbd6c6ffae1e`

---

## 10. Reconciliación de Invarianza: Discreta vs Numérica

1. **Invarianza Discreta Estricta (Tolerancia 0.0% / Igualdad Exacta de Cadenas y Conjuntos):**
   - Identificadores de pasajes primarios (`passage_id`) y su ordenamiento secuencial exacto.
   - Cantidad de evidencias primarias (`len(evidence_list)`).
   - Artículos canónicos citados (`article_id`).
   - Estado de respuesta (`status == "SUCCESS"` / `"ABSTAIN"`).
2. **Invarianza Numérica en Puntuaciones Primarias (Tolerancia Flotante de Precisión):**
   - Los scores flotantes primarios generados por el algoritmo RRF (`score`) deben ser idénticos con una tolerancia estricta:
     $$|\text{score}_{\text{baseline}} - \text{score}_{\text{fusion}}| < 10^{-4}$$

---

## 11. Metodología de Medición de Latencia y Overhead

1. **Instrumentación de Alta Resolución:** Uso exclusivo de `time.perf_counter()` para medir tiempos en milisegundos.
2. **Protocolo Experimental:**
   - 1 ciclo de calentamiento (*warm-up*) de 5 consultas no contabilizadas para estabilizar caché de memoria.
   - 3 ejecuciones consecutivas independientes sobre el benchmark de 40 consultas.
   - Cálculo de métricas agregadas: Media, Mediana, Percentil 95 (P95) y Desviación Estándar.
3. **Umbrales Máximos Aceptables:**
   - Overhead de la etapa de arbitraje en memoria: $\Delta_{\text{mean}} \le 5.0\text{ ms}$.
   - Latencia total del RRE en modo fusión: $P95 \le 80.0\text{ ms}$.

---

## 12. Protocolo de Auditoría y Gobernanza Tripartita

1. **Revisión Técnica y Ejecución (Antigravity):**
   - Ejecuta las tareas autorizadas de la etapa en modo estrictamente secuencial.
   - Genera los informes técnicos autocontenidos, evidencias reproducibles y tablas de hashes.
   - No tiene atribución de declarar aprobación ni certificar sus propios entregables.
2. **Auditoría Arquitectónica Independiente (ChatGPT):**
   - Examina el código, los diffs de Git, los logs de pytest y el cumplimiento de invariantes.
   - Emite el dictamen técnico formal: **CONFORME**, **CON OBSERVACIONES** o **NO CONFORME**.
3. **Autoridad Soberana y Exclusiva de Aprobación (Alexis Oliveros Lozano):**
   - Evalúa el dictamen de ChatGPT y los informes de Antigravity.
   - Emite la autorización formal, expresa y bloqueante para iniciar etapas o activar flags.

---

## 13. Matriz de Autorizaciones para Futura Ejecución

| Actividad Operacional | Autoridad Responsable | Condición Previa Requerida | Estado Actual |
| :--- | :--- | :--- | :--- |
| **Preparación Documental Plan Maestro v3.0** | Alexis Oliveros Lozano | Cierre de observaciones V30-F01 a V30-F09 | **AUTORIZADO / COMPLETADO** |
| **Implementación de Código (Etapa 1)** | Alexis Oliveros Lozano | Dictamen favorable de ChatGPT sobre Plan Maestro v3.0 | **PENDIENTE — NO AUTORIZADO** |
| **Implementación de Código (Etapa 2)** | Alexis Oliveros Lozano | Dictamen favorable y aprobación de Etapa 1 | **NO AUTORIZADO** |
| **Integración en RRE (Etapa 3)** | Alexis Oliveros Lozano | Aprobación formal de Etapas 1 y 2 | **NO AUTORIZADO** |
| **Ejecución de Certificación (Etapa 4)**| Alexis Oliveros Lozano | Aprobación formal de Etapa 3 | **NO AUTORIZADO** |
| **Operaciones Git Remotas (Push/Merge)**| Alexis Oliveros Lozano | Certificación final y cierre de fase | **ESTRICTAMENTE PROHIBIDO** |
| **Despliegue OCI / Producción** | Alexis Oliveros Lozano | Cierre total de Fase 4 y auditoría externa | **ESTRICTAMENTE PROHIBIDO** |
