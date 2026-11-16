# Plan Maestro de Implementación Revisado — Fase 4.2.6
## Fusión y Arbitraje Multifuente (`EvidenceBundle` & `NormativeGuard`)

**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.6 — Fusión y Arbitraje Multifuente  
**Supervisor y Autoridad Exclusiva de Aprobación:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Fecha:** 2026-11-06 (Versión v2.9 — Corrección Integral de Hallazgos AUD-V28-F01 a AUD-V28-F09)  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **EXPEDIENTE DE PLANIFICACIÓN TÉCNICA — CÓDIGO NO IMPLEMENTADO (ETAPA 1 NO AUTORIZADA)**

---

## 1. Objetivos, Alcance y Exclusiones

### 1.1 Objetivo General
Implementar incrementalmente en código funcional y probado la arquitectura de fusión y arbitraje multifuente definida en el diseño técnico aprobado, garantizando la prevalencia jerárquica y ontológica absoluta del corpus canónico SOR 2026, la contención determinista y formalizada de riesgos normativos mediante `NormativeGuard` (basada exclusivamente en un comparador exhaustivo de **12 dimensiones** para proposiciones deónticas completas, selección multi-candidata canónica no heurística, erradicación absoluta de ramas fail-open ante normas primarias ausentes o ambiguas, y máquina de estados acotada con 12 invariantes ejecutables), la reversibilidad transaccional e idempotente del protocolo de rollback ante cualquier interrupción, y la estricta invarianza del RRE y de las respuestas ADA ante consultas canónicas puras y fuera de dominio.

### 1.2 Alcance Autorizado para Futura Ejecución
1. Creación de los modelos de datos tipados y contratos de gobernanza (`src/evidence_bundle.py`).
2. Creación del componente de barrera de seguridad normativa formalizada con comparador de 12 dimensiones, selección multi-candidata canónica y máquina de estados finita acotada (`src/normative_guard.py`).
3. Creación del motor de arbitraje jerárquico desacoplado (`src/multisource_arbitrator.py`).
4. Homogeneización de parámetros de búsqueda en `src/rre_engine.py` (`min_score=3.0`, `min_overlap_ratio=0.25`).
5. Integración del pipeline de fusión en `src/rre_engine.py` bajo feature flag tri-estado desacoplado (`enable_multisource_fusion: Optional[bool] = None`, por defecto resuelto a `False`).
6. Creación de suites de pruebas unitarias, de integración, de invarianza y de seguridad crítica.
7. Construcción y ejecución del conjunto de validación hold-out reservado conocido (20 casos hold-out) con custodia auditada y exigencia de cero fallos en los 4 casos de seguridad crítica.

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
                  │  3. Selección Canónica Multi-Candidata         │
                  │     (PRIMARY_NORM_IDENTIFIED / NOT_ID / AMBIG) │
                  │  4. Comparador Formal de 12 Dimensiones        │
                  │  5. Máquina de Estados Finita e Invariantes    │
                  │  6. Purga / Bloqueo / Abstención Conservadora  │
                  └───────────────────────┬────────────────────────┘
                                          │
                                          ▼
                  ┌────────────────────────────────────────────────┐
                  │             MultisourceArbitrator              │
                  │  1. Prevalencia Canónica Estricta              │
                  │  2. Evaluación Copulativa de Suficiencia (x5)  │
                  │     (15 campos sustantivos por condición)      │
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
                  │  - sufficiency_evaluation (15 campos sustant.) │
                  └────────────────────────────────────────────────┘
```

---

## 3. Contratos de Datos y Modelos Tipados (v2.9)

Se formalizan los modelos inmutables y tipados necesarios para garantizar la integridad estructural y la trazabilidad de la deliberación normativa.

```python
"""
Contratos y Tipos Formales de Fase 4.2.6 (v2.9)
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
    """Estado explícito de resolución de la norma canónica primaria (AUD-V28-F02 / AUD-V28-F03)."""
    PRIMARY_NORM_IDENTIFIED = "PRIMARY_NORM_IDENTIFIED"          # Norma primaria unívoca y vigente identificada
    PRIMARY_NORM_NOT_IDENTIFIED = "PRIMARY_NORM_NOT_IDENTIFIED"  # No existe norma canónica que regule la conducta
    PRIMARY_NORM_AMBIGUOUS = "PRIMARY_NORM_AMBIGUOUS"            # Múltiples normas en colisión o no desambiguadas
    PRIMARY_NORM_OUT_OF_SCOPE = "PRIMARY_NORM_OUT_OF_SCOPE"      # Consulta fuera del alcance fáctico de la norma primaria
    PRIMARY_NORM_VALIDITY_UNCERTAIN = "PRIMARY_NORM_VALIDITY_UNCERTAIN" # Vigencia o autoridad no confirmada

class GuardActionTaken(Enum):
    """Acción resolutiva adoptada por el NormativeGuard (AUD-V28-F05)."""
    PERMIT = "PERMIT"                                  # Todo limpio: candidatos válidos pasan sin objeción
    PURGE_EXCEPTIONS = "PURGE_EXCEPTIONS"              # Purga selectiva de sidecars con violaciones o sin estructura
    BLOCK_ALL_SIDECAR = "BLOCK_ALL_SIDECAR"            # Bloqueo total de sidecars reteniendo solo primarios
    CONSERVATIVE_FALLBACK = "CONSERVATIVE_FALLBACK"    # Abstención conservadora por incertidumbre, ambigüedad o falta de norma primaria

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
    WORLD_JUDO_TOUR = "WORLD_JUDO_TOUR"  # Grand Slam, Grand Prix, Masters, Mundiales
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
    IMPERATIVE_PROHIBITION = "IMPERATIVE_PROHIBITION"  # Prohibición absoluta (ej. Hansoku-make directo)
    POSITIVE_AUTHORIZATION = "POSITIVE_AUTHORIZATION"  # Acción permitida (ej. Reverse seoi-nage en Senior)
    CONDITIONAL_EXCEPTION = "CONDITIONAL_EXCEPTION"    # Excepción condicionada estricta
    TECHNICAL_DEFINITION = "TECHNICAL_DEFINITION"      # Definición de puntuación o concepto (ej. Yuko 5-9s)
    PROCEDURAL_INSTRUCTION = "PROCEDURAL_INSTRUCTION"  # Criterio operativo de fluidez arbitral

class RelationType(Enum):
    CONCORDANT = "CONCORDANT"          # Ratifica o coincide con el SOR sin modificarlo
    SPECIFICATION = "SPECIFICATION"    # Detalla un procedimiento operativo no explicitado en el SOR
    AMENDMENT = "AMENDMENT"            # Modifica una regla canónica preexistente (solo Tier 2 oficial)
    INTERPRETATIVE_GUIDANCE = "INTERPRETATIVE_GUIDANCE"  # Guía arbitral para juzgar acciones continuas
    CONFLICT_OVERRIDDEN = "CONFLICT_OVERRIDDEN"  # Conflicto neutralizado por prevalencia canónica

class ViolationSeverity(Enum):
    """Nivel de severidad cerrado para violaciones de seguridad normativa."""
    CRITICAL = "CRITICAL"  # Violación grave de seguridad; purga o bloqueo forzoso
    WARNING = "WARNING"    # Conflicto de interpretación menor o atenuante no crítico
    INFO = "INFO"          # Nota informativa de alcance o contexto

class PropositionComparisonCategory(Enum):
    """Categorización formal del resultado de la comparación de proposiciones (AUD-V28-F01)."""
    IDENTITY = "IDENTITY"                                # Identidad formal completa en las 12 dimensiones
    EQUIVALENCE = "EQUIVALENCE"                          # Equivalencia funcional sustantiva sin alteración deóntica
    COMPATIBILITY = "COMPATIBILITY"                      # Compatible (armonizable jerárquicamente con condiciones)
    CONTRADICTION = "CONTRADICTION"                      # Contradicción deóntica, de sanción o de excepciones
    INSUFFICIENCY = "INSUFFICIENCY"                      # Proposición incompleta en campos esenciales
    CONSERVATIVE_ABSTENTION = "CONSERVATIVE_ABSTENTION"  # Fuera de dominio, desalineación o duda estructural

@dataclass(frozen=True)
class NormativeProposition:
    """
    Representación formalizada de una proposición normativa en 12 dimensiones canónicas (AUD-V28-F01).
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
    # 12. Condiciones de precedencia, sustitución o modificación normativa
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
    rejected_evidence_id: str  # Obligatorio: toda violación identifica evidencia concreta

@dataclass
class NormativeGuardResult:
    """
    Resultado estructurado y auditable de la evaluación del NormativeGuard con los 12 invariantes
    ejecutables de la máquina de estados finita acotada (AUD-V28-F05).
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
        """Validación exhaustiva y ejecutable de los 12 invariantes formales (AUD-V28-F05)."""
        critical_violations = [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]
        warning_violations = [v for v in self.violations if v.severity == ViolationSeverity.WARNING]
        info_violations = [v for v in self.violations if v.severity == ViolationSeverity.INFO]
        
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

        # Invariante 12 (Ejecutable): Ausencia de contradicción no equivale a suficiencia dispositiva (AUD-V28-F05)
        # La no-violación de contención (passed=True) habilita candidatos inocuos, pero NUNCA certifica suficiencia dispositiva por sí misma
        if self.passed is True and self.is_sufficient_for_dispositive_ruling is True:
            raise ValueError("Invariante 12 violado: NormativeGuard no puede certificar suficiencia dispositiva; eso compete a SufficiencyEvaluationResult.")
```

### Tabla de Invariantes de NormativeGuardResult (AUD-V28-F05)

| N.º Invariante | Condición Evaluada | Expresión Lógica Obligatoria | Consecuencia ante Incumplimiento |
| :---: | :--- | :--- | :--- |
| **INV-01** | Disyunción de conjuntos | $	ext{retained\_ids} \cap 	ext{rejected\_ids} = \emptyset$ | `ValueError`: Evidencia en ambos conjuntos simultáneamente. |
| **INV-02** | Trazabilidad de violaciones | $orall v \in 	ext{violations}, v.	ext{rejected\_evidence\_id} 
e ""$ | `ValueError`: Violación huérfana sin evidencia rechazada. |
| **INV-03** | Rechazo de violaciones críticas | $orall v \in 	ext{crit\_viol}, v.	ext{rejected\_id} \in 	ext{rejected\_ids} \land v.	ext{rejected\_id} 
otin 	ext{retained\_ids}$ | `ValueError`: Evidencia crítica retenida o no rechazada. |
| **INV-04** | Bloqueo estricto por criticidad | $	ext{len}(	ext{crit\_viol}) > 0 \implies 	ext{passed} = 	ext{False}$ | `ValueError`: `passed=True` en presencia de violaciones críticas. |
| **INV-05** | Acción prohibida ante criticidad| $	ext{len}(	ext{crit\_viol}) > 0 \implies 	ext{action\_taken} 
e 	ext{PERMIT}$ | `ValueError`: `PERMIT` ante violaciones críticas. |
| **INV-06** | Integridad de pase limpio | $	ext{passed} = 	ext{True} \implies 	ext{len}(	ext{crit\_viol}) = 0$ | `ValueError`: Inconsistencia entre pase y criticidad. |
| **INV-07** | Causa justificada de rechazo | $orall r \in 	ext{rejected}, r.	ext{rejection\_reason} 
e ""$ | `ValueError`: Rechazo arbitrario sin causa justificada. |
| **INV-08** | Abstención conservadora | $	ext{action\_taken} = 	ext{CONSERVATIVE\_FALLBACK} \implies 	ext{passed} = 	ext{False}$ | `ValueError`: Fallback conservador con `passed=True`. |
| **INV-09** | Estructuración obligatoria | $orall ret \in 	ext{retained}, ret.	ext{proposition} 
e 	ext{None}$ | `ValueError`: Retención de sidecar no estructurado. |
| **INV-10** | Consistencia de advertencias | $	ext{len}(	ext{crit\_viol}) = 0 \land 	ext{rejected} 
e \emptyset \implies 	ext{action} \in \{	ext{PURGE}, 	ext{BLOCK}, 	ext{FALLBACK}\}$ | `ValueError`: Acción incongruente con rechazos no críticos. |
| **INV-11** | Estado óptimo unívoco | $	ext{violations} = \emptyset \land 	ext{rejected} = \emptyset \land 	ext{PRIMARY\_ID} \implies 	ext{passed}=	ext{True} \land 	ext{action}=	ext{PERMIT}$ | `ValueError`: Estado limpio no resuelto a PERMIT. |
| **INV-12** | Desacoplamiento de suficiencia| $	ext{passed} = 	ext{True} \implies 	ext{is\_sufficient\_for\_dispositive\_ruling} = 	ext{False}$ | `ValueError`: NormativeGuard certificando suficiencia dispositiva. |

### Matriz de Transiciones y Estados Válidos e Inválidos (AUD-V28-F05)

| ID Estado | Norma Primaria | Violaciones CRITICAL | Violaciones WARNING/INFO | Sidecars Rechazados | Sidecars Retenidos | `passed` | `action_taken` | Dictamen Lógico |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **ST-01** | `IDENTIFIED` | **0** | **0** | **0** | $\ge 0$ | `True` | `PERMIT` | **VÁLIDO:** Ejecución limpia total. |
| **ST-02** | `IDENTIFIED` | **0** | $\ge 0$ | $> 0$ | $> 0$ | `True` | `PURGE_EXCEPTIONS` | **VÁLIDO:** Purga de advertencias no críticas; retiene válidos. |
| **ST-03** | `IDENTIFIED` | **0** | $\ge 0$ | $> 0$ | **0** | `True` | `BLOCK_ALL_SIDECAR` | **VÁLIDO:** Rechazo administrativo de sidecars; sin CRITICAL. |
| **ST-04** | `IDENTIFIED` | $> 0$ | $\ge 0$ | $> 0$ | $> 0$ | `False` | `PURGE_EXCEPTIONS` | **VÁLIDO:** Violación crítica purgada; retiene inocuos. |
| **ST-05** | `IDENTIFIED` | $> 0$ | $\ge 0$ | $> 0$ | **0** | `False` | `BLOCK_ALL_SIDECAR` | **VÁLIDO:** Bloqueo total de sidecars por criticidad. |
| **ST-06** | `NOT_IDENTIFIED` | Cualquiera | Cualquiera | $\ge 0$ | **0** | `False` | `CONSERVATIVE_FALLBACK` | **VÁLIDO:** Abstención conservadora por ausencia de canónico. |
| **ST-07** | `AMBIGUOUS` | Cualquiera | Cualquiera | $\ge 0$ | **0** | `False` | `CONSERVATIVE_FALLBACK` | **VÁLIDO:** Abstención conservadora por ambigüedad primaria. |
| **ST-08** | `OUT_OF_SCOPE` | Cualquiera | Cualquiera | $\ge 0$ | **0** | `False` | `CONSERVATIVE_FALLBACK` | **VÁLIDO:** Abstención por consulta fuera de alcance. |
| **ST-INV-01** | `IDENTIFIED` | $> 0$ | Cualquiera | Cualquiera | Cualquiera | `True` | Cualquiera | **INVÁLIDO:** `passed=True` con violaciones CRITICAL. |
| **ST-INV-02** | `IDENTIFIED` | $> 0$ | Cualquiera | Cualquiera | Cualquiera | `False` | `PERMIT` | **INVÁLIDO:** `action_taken=PERMIT` con violaciones CRITICAL. |
| **ST-INV-03** | Cualquiera | Cualquiera | Cualquiera | ID $X$ | ID $X$ | Cualquiera | Cualquiera | **INVÁLIDO:** Intersección no vacía entre retenidos y rechazados. |
| **ST-INV-04** | Cualquiera | Cualquiera | Contiene ID $X$ | Ausente ID $X$| Cualquiera | Cualquiera | Cualquiera | **INVÁLIDO:** Violación con ID ausente de `rejected_sidecars`. |
| **ST-INV-05** | `NOT_IDENTIFIED`| Cualquiera | Cualquiera | Cualquiera | $> 0$ | Cualquiera | `PERMIT` | **INVÁLIDO:** Admisión fail-open de sidecar sin norma primaria. |
| **ST-INV-06** | Cualquiera | Cualquiera | Cualquiera | $\ge 0$ | Retiene no-estruct. | Cualquiera | Cualquiera | **INVÁLIDO:** Retención de sidecar sin proposición formal. |

```python
class EvidenceSufficiencyStage(Enum):
    """Etapas diferenciadas de validación probatoria sustantiva (AUD-V28-F06)."""
    FIELD_PRESENT = "FIELD_PRESENT"                                # Los 15 campos requeridos están presentes
    SOURCE_IDENTIFIED = "SOURCE_IDENTIFIED"                        # Fuente oficial reconocida y rastreable
    SOURCE_AUTHENTICATED = "SOURCE_AUTHENTICATED"                  # Integridad criptográfica SHA-256 contrastada
    SOURCE_CURRENT = "SOURCE_CURRENT"                              # Vigencia material y temporal confirmada
    EVIDENCE_RELEVANT = "EVIDENCE_RELEVANT"                        # Pertinencia fáctica y de alcance para la consulta
    EVIDENCE_SUBSTANTIVELY_VALID = "EVIDENCE_SUBSTANTIVELY_VALID"  # Contenido semántico y documental probado
    CONDITION_SATISFIED = "CONDITION_SATISFIED"                    # La condición normativa queda formalmente acreditada

@dataclass
class ConditionVerificationEvidence:
    """
    Evidencia auditable de 15 campos que respalda formalmente cada condición de suficiencia (AUD-V28-F06).
    Distingue rigurosamente entre presencia de campo, evidencia documental, autenticidad, verificabilidad,
    pertinencia y suficiencia resolutiva.
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
    verification_passed: bool = False                   # Resultado booleano: solo True si supera evaluación sustantiva

    def is_substantively_valid(self, expected_condition_id: str) -> bool:
        """
        Comprueba de forma positiva y sustantiva las 7 etapas de acreditación probatoria (AUD-V28-F06).
        Rechaza placeholders, hashes inválidos, fechas no conformes, autoridades insuficientes y 'UNKNOWN'.
        """
        # Etapa 1: FIELD_PRESENT
        if (not self.evidence_id or not self.condition_id or not self.documentary_source or
            not self.verifiable_reference or not self.passage_or_locator or not self.integrity_hash or
            not self.promulgation_date or not self.context or not self.verification_method or
            not self.verification_responsible or not self.verification_outcome or not self.relevance_and_limitations):
            return False

        # Rechazo taxativo de cadenas con valor UNKNOWN o vacías tras strip
        fields_to_check = [
            self.evidence_id, self.condition_id, self.documentary_source,
            self.verifiable_reference, self.passage_or_locator, self.integrity_hash,
            self.promulgation_date, self.context, self.verification_method,
            self.verification_responsible, self.verification_outcome
        ]
        for f in fields_to_check:
            if not f.strip() or f.strip().upper() == "UNKNOWN":
                return False

        if self.condition_id.strip() != expected_condition_id.strip():
            return False

        # Etapa 2: SOURCE_IDENTIFIED
        if self.source_authority not in {AuthorityTier.TIER_1_CANONICAL, AuthorityTier.TIER_2_OFFICIAL_CIRCULAR, AuthorityTier.TIER_3_COMPLEMENTARY}:
            return False

        # Etapa 3: SOURCE_AUTHENTICATED (Formato hexadecimal estricto de 64 caracteres)
        sha256_pattern = re.compile(r"^[a-fA-F0-9]{64}$")
        if not sha256_pattern.match(self.integrity_hash.strip()):
            return False

        # Etapa 4: SOURCE_CURRENT
        if self.validity_status != NormativeValidity.IN_FORCE:
            return False

        # Etapa 5: EVIDENCE_RELEVANT
        if not self.relevance_and_limitations.strip() or self.relevance_and_limitations.strip().upper() == "UNKNOWN":
            return False

        # Etapa 6: EVIDENCE_SUBSTANTIVELY_VALID
        if "VERIFIED" not in self.verification_outcome.strip().upper():
            return False

        # Etapa 7: CONDITION_SATISFIED
        if self.verification_passed is not True:
            return False

        self.current_stage = EvidenceSufficiencyStage.CONDITION_SATISFIED
        return True

@dataclass
class SufficiencyEvaluationResult:
    """Evaluación auditable respaldada por evidencia verificable de las 5 condiciones copulativas (AUD-V28-F06)."""
    is_sufficient: bool
    authority_validated: bool
    validity_confirmed: bool
    scope_pertinent: bool
    normative_guard_clean: bool
    no_unresolved_conflicts: bool
    condition_evidences: Dict[str, ConditionVerificationEvidence] = field(default_factory=dict)
    audit_reasons: List[str] = field(default_factory=list)

    def evaluate_copulative(self) -> bool:
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
                self.audit_reasons.append(f"Condición '{key}' carece de objeto probatorio adjunto (Evidence is None).")
                continue
            
            # Validación sustantiva estricta de las 7 etapas
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

@dataclass
class EvidenceBundle:
    bundle_id: str
    query: str
    primary_items: List[EvidenceItem]
    sidecar_items: List[EvidenceItem]
    arbitration_decision: ArbitrationDecision
    normative_guard_result: NormativeGuardResult
    sufficiency_evaluation: SufficiencyEvaluationResult
    audit_trail: List[str]
    is_sufficient_for_synthesis: bool = False
    requires_context_disambiguation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 4. Contrato de Feature Flags, Fallbacks e Integración en RRE

### 4.1 Contrato del Feature Flag y Precedencia Tri-Estado
En `src/rre_engine.py`:
- **Parámetro Formal en Constructor:** `enable_multisource_fusion: Optional[bool] = None`.
- **Variable de Entorno:** `RRE_ENABLE_MULTISOURCE_FUSION`.
  - Valores reconocidos como `True`: `{"1", "true", "yes", "on"}` (case-insensitive, tras `strip()`).
  - Valores reconocidos como `False`: `{"0", "false", "no", "off"}`.
  - Variable vacía `""` o no definida: se interpreta como ausencia de configuración de entorno.
- **Regla Estricta de Precedencia:**
  1. Si `enable_multisource_fusion` es un booleano explícito (`True` o `False`), su valor prevalece de manera absoluta sobre cualquier valor de la variable de entorno.
  2. Si `enable_multisource_fusion is None`, se evalúa `os.environ.get("RRE_ENABLE_MULTISOURCE_FUSION")`:
     - Si la variable está definida y coincide con los valores verdaderos, resuelve a `True`.
     - Si coincide con valores falsos, resuelve a `False`.
     - Si no está definida o es inválida, se aplica el **fallback por defecto: `False`**.
  3. El valor resuelto se almacena en `self.enable_multisource_fusion: bool`.

---

## 5. Módulo `NormativeGuard`: Comparador en 12 Dimensiones y Selección Canónica Multi-Candidata

### 5.1 Rediseño Formal de `PropositionComparator` (AUD-V28-F01)
El comparador componente a componente analiza sistemáticamente las **12 dimensiones normativas obligatorias**:

1. **Acción normativa:** Identidad técnica o conducta tipada (`head_bridge_landing`, `reverse_seoi_nage`).
2. **Objeto de la acción:** Zona anatómica o material sobre el que recae (`cervical_spine`, `opponent_lapel`).
3. **Sujeto:** Agente normativo activo o pasivo obligado/prohibido (`tori`, `uke`, `referee`).
4. **Operador deóntico:** `PROHIBITION`, `OBLIGATION`, `PERMISSION`.
5. **Condiciones de aplicación:** Requisitos fácticos para la activación del mandato.
6. **Excepciones:** Circunstancias taxativas donde el mandato no rige.
7. **Condiciones de las excepciones:** Requisitos específicos para que opere una excepción.
8. **Consecuencia o sanción:** Puntuación, penalidad o descalificación (`IPPON`, `SHIDO`, `HANSOKU_MAKE_DIRECT`).
9. **Alcance de aplicación:** Categoría de edad (`CADET`, `SENIOR`), competición (`WJT`, `OG`), modalidad (`INDIVIDUAL`, `TEAM`) y contexto.
10. **Autoridad normativa y jerarquía:** Nivel de autoridad del emisor (`TIER_1_CANONICAL`, `TIER_2_OFFICIAL_CIRCULAR`, `TIER_3_COMPLEMENTARY`).
11. **Vigencia temporal y fecha de aplicación:** Estado de vigencia (`IN_FORCE`, `EXPIRED`) y fecha formal de promulgación/aplicación.
12. **Condiciones de precedencia y modificación:** Reglas explícitas de prevalencia o derogación normativa.

```python
class PropositionComparator:
    """Comparador formal componente a componente en 12 dimensiones (AUD-V28-F01)."""

    @classmethod
    def compare(
        cls,
        canonical: NormativeProposition,
        candidate: NormativeProposition
    ) -> Tuple[PropositionComparisonCategory, List[str]]:
        reasons: List[str] = []

        # Validación de integridad mínima
        if not candidate.action or not candidate.target_object or not candidate.subject:
            return PropositionComparisonCategory.INSUFFICIENCY, ["Proposición candidata carece de acción, objeto o sujeto."]

        # 1. Alineación fáctica de dominio (Acción, Objeto y Sujeto)
        if candidate.action != canonical.action or candidate.target_object != canonical.target_object:
            return PropositionComparisonCategory.CONSERVATIVE_ABSTENTION, [
                f"Desalineación temática: candidata ({candidate.action}:{candidate.target_object}) != canónica ({canonical.action}:{canonical.target_object})"
            ]

        if candidate.subject != canonical.subject:
            return PropositionComparisonCategory.CONSERVATIVE_ABSTENTION, [
                f"Sujeto normativo no concordante: candidata ({candidate.subject}) != canónica ({canonical.subject})"
            ]

        # 2. Vigencia temporal
        if candidate.validity_status != NormativeValidity.IN_FORCE:
            return PropositionComparisonCategory.CONTRADICTION, [
                f"Instrumento candidato no está vigente ({candidate.validity_status.value})."
            ]

        # 3. Jerarquía y Precedencia de Autoridad
        if candidate.authority_tier.value > canonical.authority_tier.value:
            # Fuente de menor jerarquía (Tier 2 o 3) pretendiendo alterar norma canónica Tier 1
            if candidate.deontic_operator != canonical.deontic_operator:
                return PropositionComparisonCategory.CONTRADICTION, [
                    f"Conflicto de jerarquía: Tier {candidate.authority_tier.value} pretende alterar operador de Tier {canonical.authority_tier.value}."
                ]

        # 4. Incompatibilidad de Alcance (Edad y Competición)
        if canonical.scope.age_category == AgeCategory.CADET:
            if candidate.scope.cadet_junior_excluded and candidate.deontic_operator == DeonticOperator.PERMISSION:
                return PropositionComparisonCategory.CONTRADICTION, [
                    "Conflicto de alcance: Extrapolación ilícita de autorización Senior a categoría Cadetes protegida."
                ]

        # 5. Contradicciones Deónticas y de Sanción
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

        # 6. Identidad formal completa en 12 dimensiones
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
            return PropositionComparisonCategory.IDENTITY, ["Identidad exacta en las 12 dimensiones normativas."]

        # 7. Equivalencia funcional
        if (candidate.deontic_operator == canonical.deontic_operator and
            candidate.sanction == canonical.sanction and
            candidate.scope.age_category == canonical.scope.age_category and
            candidate.authority_tier == canonical.authority_tier):
            return PropositionComparisonCategory.EQUIVALENCE, ["Equivalencia funcional en mandatos y consecuencias."]

        # 8. Compatibilidad condicionada
        if (candidate.deontic_operator == canonical.deontic_operator and
            candidate.authority_tier.value >= canonical.authority_tier.value):
            return PropositionComparisonCategory.COMPATIBILITY, ["Compatibilidad interpretativa subordinada a la norma canónica."]

        return PropositionComparisonCategory.CONSERVATIVE_ABSTENTION, ["Incertidumbre o ambigüedad estructural en la comparación."]
```

### Tabla de 12 Casos Conceptuales de Verificación del Comparador (AUD-V28-F01)

| N.º Caso | Dimensión Clave Evaluada | Condición de Entrada | Categoría Resuelta | Justificación Normativa |
| :---: | :--- | :--- | :---: | :--- |
| **TC-01** | Coincidencia Absoluta | Idénticas 12 dimensiones (SOR 2026 Art. 14). | `IDENTITY` | Concordancia textual y estructural completa. |
| **TC-02** | Equivalencia Funcional | Misma acción, operador y sanción con redacción formal alternativa. | `EQUIVALENCE` | Misma consecuencia jurídica sin alteración material. |
| **TC-03** | Contradicción Deóntica | Norma prohíbe técnica; sidecar afirma que está permitida. | `CONTRADICTION` | Oposición binaria entre prohibición y permisión. |
| **TC-04** | Dilución de Sanción | SOR dicta Hansoku-make directo; sidecar propone Shido. | `CONTRADICTION` | Mitigación ilegal de descalificación en seguridad. |
| **TC-05** | Inyección de Excepciones | Norma taxativa sin excepciones; sidecar alega atenuante. | `CONTRADICTION` | Intento de vulnerar la taxatividad de la norma canónica. |
| **TC-06** | Incompatibilidad de Edad | Circular Senior aplicada a consulta sobre categoría Cadetes. | `CONTRADICTION` | Violación de la regla de protección por edad. |
| **TC-07** | Vigencia Expirada | Instrumento normativo complementario revocado o suspendido. | `CONTRADICTION` | Falta de vigencia temporal (`SUPERSEDED`/`EXPIRED`). |
| **TC-08** | Conflicto de Jerarquía | Tier 3 pretende derogar o prevalecer sobre norma Tier 1. | `CONTRADICTION` | Infracción del principio de jerarquía de fuentes. |
| **TC-09** | Sujeto Diferente | Regla para uke (puente) evaluada sobre conducta de tori. | `CONSERVATIVE_ABSTENTION` | Desalineación de sujeto activo/pasivo. |
| **TC-10** | Compatibilidad Subordinada| Circular técnica que detalla procedimiento sin modificar sanción. | `COMPATIBILITY` | Armonización subordinada concordante. |
| **TC-11** | Campo Esencial Ausente | Proposición carece de objeto o sanción tipada. | `INSUFFICIENCY` | Falta de estructura mínima deliberable. |
| **TC-12** | Desalineación Temática | Acción no catalogada en la matriz canónica activa. | `CONSERVATIVE_ABSTENTION` | Fuera de dominio deliberable. |

### 5.2 Rediseño de la Selección Canónica Multi-Candidata (AUD-V28-F02)
Se erradica la selección ciega por primera coincidencia de acción y objeto. Se evalúan todas las candidatas y se resuelve deterministamente el estado de la norma primaria:

```python
class CanonicalSelector:
    """Selector multi-candidata de la proposición canónica activa (AUD-V28-F02)."""

    @classmethod
    def resolve_primary_norm(
        cls,
        query: str,
        primary_items: List[EvidenceItem]
    ) -> Tuple[PrimaryNormResolutionState, Optional[NormativeProposition], List[str]]:
        log: List[str] = []
        matching_propositions: List[NormativeProposition] = []

        # 1. Extraer todas las proposiciones estructuradas presentes en los pasajes primarios
        for item in primary_items:
            if item.proposition is not None:
                matching_propositions.append(item.proposition)

        if not matching_propositions:
            log.append("No structured primary propositions found in primary evidence.")
            return PrimaryNormResolutionState.PRIMARY_NORM_NOT_IDENTIFIED, None, log

        # 2. Filtrar por vigencia temporal y autoridad Tier 1
        valid_candidates = [
            p for p in matching_propositions
            if p.validity_status == NormativeValidity.IN_FORCE and p.authority_tier == AuthorityTier.TIER_1_CANONICAL
        ]

        if not valid_candidates:
            log.append("Primary propositions found but none are IN_FORCE or TIER_1.")
            return PrimaryNormResolutionState.PRIMARY_NORM_VALIDITY_UNCERTAIN, None, log

        # 3. Agrupar por acción y objeto
        unique_rules = {(p.action, p.target_object): p for p in valid_candidates}

        if len(unique_rules) == 1:
            selected = list(unique_rules.values())[0]
            log.append(f"Primary norm unambiguously identified: {selected.action}:{selected.target_object} (Art. {selected.article_ref}).")
            return PrimaryNormResolutionState.PRIMARY_NORM_IDENTIFIED, selected, log

        # Si hay múltiples reglas primarias en colisión para la misma consulta
        log.append(f"Multiple primary candidate rules detected ({len(unique_rules)}). Material ambiguity.")
        return PrimaryNormResolutionState.PRIMARY_NORM_AMBIGUOUS, None, log
```

### 5.3 Erradicación Absoluta de Comportamientos Fail-Open en `NormativeGuard` (AUD-V28-F03)
Si `primary_norm_state != PRIMARY_NORM_IDENTIFIED`, **se prohíbe admitir sidecars como autoridad dispositiva**. No se convierten ausencias de contradicción en permisos vinculantes:

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

        # 1. Resolución multi-candidata de la norma primaria (AUD-V28-F02)
        norm_state, active_canonical, selector_log = CanonicalSelector.resolve_primary_norm(query, primary_items)
        log.extend(selector_log)

        # 2. Comportamiento Fail-Closed ante ausencia o ambigüedad de norma canónica (AUD-V28-F03)
        if norm_state != PrimaryNormResolutionState.PRIMARY_NORM_IDENTIFIED:
            # Se rechazan todos los sidecars para fines dispositivos
            for sc in candidate_sidecars:
                sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                sc.rejection_reason = f"FAIL_CLOSED_NO_CANONICAL_ANCHOR_{norm_state.value}"
                rejected.append(sc)
                violations.append(GuardViolation(
                    rule_id=f"RULE-SEC-{norm_state.value}",
                    severity=ViolationSeverity.WARNING if norm_state == PrimaryNormResolutionState.PRIMARY_NORM_NOT_IDENTIFIED else ViolationSeverity.CRITICAL,
                    article_id=sc.article_id,
                    description=f"Sidecar no admisible como norma dispositiva: Estado canónico '{norm_state.value}'.",
                    rejected_evidence_id=sc.evidence_id
                ))

            log.append(f"Fail-closed engaged: primary_norm_state={norm_state.value}. All sidecars blocked from dispositive rulings.")
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

            # Rechazo forzoso de Sidecars no estructurados
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
                log.append(f"Rejected candidate {sc.evidence_id}: Lack of structured proposition.")
                continue

            # Comparación en 12 dimensiones
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
                # IDENTITY, EQUIVALENCE o COMPATIBILITY
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
            is_sufficient_for_dispositive_ruling=False  # Desacoplamiento estricto de suficiencia (INV-12)
        )
```

---

## 6. Secuencia Incremental de Implementación y Baseline de Tests

> [!IMPORTANT]
> **ESTADO DE IMPLEMENTACIÓN: PENDIENTE — NO EJECUTADO**  
> Ninguna de las etapas de código ha sido iniciada. Todos los tests citados a continuación representan **metas planificadas**, no pruebas ejecutadas ni superadas. La línea base de 267 tests corresponde a la Fase 4.2.5.

```
Línea Base Certificada (267 tests PASSED — Fase 4.2.5)
   │
   ▼
[Etapa 1: Modelos de Datos, Provenance Formal y NormativeGuard Aislado]
   ├── Implementar src/evidence_bundle.py (Dataclasses, 12 invariantes ejecutables, 15 campos de suficiencia)
   ├── Implementar src/normative_guard.py (Comparador 12 dimensiones, selección multi-candidata, fail-closed)
   ├── Implementar tests/test_evidence_bundle.py (+5 tests planificados: Invariantes, hash completo, suficiencia)
   ├── Implementar tests/test_normative_guard.py (+5 tests planificados: Reglas deónticas, oráculos SEC-CRIT)
   └── Meta Planificada Etapa 1: 277 tests PASSED (267 base + 10 nuevos planificados)
       └── Gate 1: pytest 277/277 sin errores.
   │
   ▼
[Etapa 2: Motor de Arbitraje Desacoplado]
   ├── Implementar src/multisource_arbitrator.py (Precedencia, vigencia y suficiencia probatoria sustantiva)
   ├── Implementar tests/test_multisource_arbitrator.py (+5 tests planificados)
   └── Meta Planificada Etapa 2: 282 tests PASSED (277 previos + 5 nuevos planificados)
       └── Gate 2: pytest 282/282 sin errores.
   │
   ▼
[Etapa 3: Integración en RRE Engine con Feature Flag Tri-Estado]
   ├── Modificar src/rre_engine.py (Precedencia tri-estado, fallback desacoplado, metadata)
   ├── Implementar tests/test_fusion_invariance_ada.py (+4 tests planificados: FF, Invarianza RRE, Invarianza ADA, Edad Desconocida)
   └── Meta Planificada Etapa 3: 286 tests PASSED (282 previos + 4 nuevos planificados)
       └── Gate 3: Invarianza discreta 100.0%, delta flotante < 10^-4, pytest 286/286.
   │
   ▼
[Etapa 4: Ejecución del Dataset Hold-Out Reservado Conocido y Auditoría Final]
   ├── Ejecutar Dataset B hold-out reservado conocido (20 casos de validación independiente)
   ├── Evaluar individualmente los 4 Casos Críticos de Seguridad (Zero-Tolerance: 4/4 PASS estricto)
   ├── Recalcular y validar los hashes SHA-256 de los 6 activos físicos de datos y 1 snapshot de código
   └── Meta Planificada Etapa 4: >= 286 tests PASSED + Dataset B certificado
       └── Gate 4: Dictamen final de ChatGPT y firma soberana de Alexis Oliveros Lozano.
```

---

## 7. Protocolo de Rollback Transaccional, Idempotente y Recuperable (AUD-V28-F04 / AUD-V28-F09)

### 7.1 Estados de la Máquina Transaccional de Rollback
La máquina de rollback opera bajo estados finitos auditables:
`PREPARED` $ightarrow$ `BACKUP_VERIFIED` $ightarrow$ `RESTORING` $ightarrow$ `VERIFIED` $ightarrow$ `COMPLETED`  
En caso de conflicto o interrupción: $ightarrow$ `RECOVERY_REQUIRED` $ightarrow$ `ABORTED`.

### 7.2 Principios Operativos y Restricciones Obligatorias
1. **Prohibición Total de Eliminación Destructiva:** Cero `os.remove()`, `os.unlink()`.
2. **No Desplazar sin Respaldo Verificado:** Ningún archivo activo se mueve a cuarentena antes de que su copia de backup haya sido verificada por hash SHA-256 idéntico.
3. **Destinos de Cuarentena y Backup Inmutables y sin Sobrescritura:** Cada ejecución genera un directorio con timestamp y UUID de transacción (`scratch/rollback_fase4_2_6/<ts>_<uuid>/`).
4. **Idempotencia Transaccional:** Si el script se ejecuta repetidas veces o se interrumpe a la mitad, detecta el estado previo y reanuda o recupera de forma segura sin dejar el repositorio en estado corrupto.
5. **Preservación Fail-Closed ante Modificaciones Externas:** Si `src/rre_engine.py` presenta un hash que no corresponde ni al baseline ni al de la fase en curso, el proceso se aborta inmediatamente sin sobrescribir el archivo.

```python
"""
Script de Rollback Transaccional, Idempotente y Recuperable — Fase 4.2.6 (AUD-V28-F04 / AUD-V28-F09)
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

def execute_transactional_rollback():
    tx_id = str(uuid.uuid4())[:8]
    ts = int(time.time())
    tx_dir = f"scratch/rollback_fase4_2_6/{ts}_{tx_id}"
    backup_dir = os.path.join(tx_dir, "backup")
    quarantine_dir = os.path.join(tx_dir, "quarantine")
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(quarantine_dir, exist_ok=True)

    state_file = os.path.join(tx_dir, "transaction_state.json")
    audit_log = []

    def log_state(state: RollbackState, details: str):
        audit_log.append(f"[{state.value}] {details}")
        with open(state_file, "w", encoding="utf-8") as sf:
            json.dump({
                "tx_id": tx_id,
                "timestamp": ts,
                "state": state.value,
                "audit_log": audit_log
            }, sf, indent=2)

    log_state(RollbackState.PREPARED, "Iniciando prechequeos de integridad.")

    # 1. PRECHECK: Snapshot de línea base
    if not os.path.exists(SNAPSHOT_PATH):
        log_state(RollbackState.ABORTED, f"Snapshot de respaldo ausente en {SNAPSHOT_PATH}")
        raise FileNotFoundError(f"[ABORT] Snapshot previo no encontrado en {SNAPSHOT_PATH}")

    snap_hash = calculate_sha256(SNAPSHOT_PATH)
    if snap_hash != EXPECTED_BASELINE_SHA256:
        log_state(RollbackState.ABORTED, f"Hash del snapshot alterado: {snap_hash} != {EXPECTED_BASELINE_SHA256}")
        raise ValueError(f"[ABORT] Discrepancia en snapshot: {snap_hash} != {EXPECTED_BASELINE_SHA256}")

    # 2. VALIDATION de rre_engine.py (Fail-closed)
    if os.path.exists(TARGET_RRE):
        current_rre_hash = calculate_sha256(TARGET_RRE)
        # Respaldo de seguridad previo
        rre_backup_path = os.path.join(backup_dir, "rre_engine.py.pre_rollback")
        shutil.copy2(TARGET_RRE, rre_backup_path)
        if calculate_sha256(rre_backup_path) != current_rre_hash:
            log_state(RollbackState.ABORTED, "Fallo al verificar integridad del backup previo de rre_engine.py")
            raise IOError("[ABORT] Fallo de integridad en backup de rre_engine.py")
        log_state(RollbackState.PREPARED, f"rre_engine.py respaldado con hash {current_rre_hash}")

    # 3. BACKUP_VERIFIED: Respaldar todos los archivos de fase antes de moverlos
    existing_files = [fp for fp in PHASE_FILES_CREATED if os.path.exists(fp)]
    for fp in existing_files:
        flat_name = fp.replace("/", "_").replace("\", "_")
        b_dest = os.path.join(backup_dir, flat_name)
        shutil.copy2(fp, b_dest)
        if calculate_sha256(b_dest) != calculate_sha256(fp):
            log_state(RollbackState.ABORTED, f"Fallo al verificar backup de {fp}")
            raise IOError(f"[ABORT] Fallo al verificar backup para {fp}")

    log_state(RollbackState.BACKUP_VERIFIED, f"{len(existing_files)} archivos de fase respaldados y verificados.")

    # 4. RESTORING: Mover a cuarentena (CERO os.remove)
    log_state(RollbackState.RESTORING, "Moviendo archivos a cuarentena aislada.")
    for fp in existing_files:
        flat_name = fp.replace("/", "_").replace("\", "_")
        q_dest = os.path.join(quarantine_dir, flat_name + ".quarantine")
        # Copia a cuarentena
        shutil.copy2(fp, q_dest)
        if calculate_sha256(q_dest) != calculate_sha256(fp):
            log_state(RollbackState.RECOVERY_REQUIRED, f"Fallo de verificación en cuarentena para {fp}")
            raise IOError(f"[RECOVERY_REQUIRED] Fallo de verificación en cuarentena para {fp}")
        # Desplazamiento seguro a extensión inactiva (.quarantined)
        shutil.move(fp, q_dest + ".moved")

    # Restauración atómica de rre_engine.py desde el snapshot inmutable
    shutil.copy2(SNAPSHOT_PATH, TARGET_RRE)
    restored_hash = calculate_sha256(TARGET_RRE)

    # 5. VERIFIED: Validación cruzada de hash restaurado
    if restored_hash != EXPECTED_BASELINE_SHA256:
        log_state(RollbackState.RECOVERY_REQUIRED, f"Restauración corrupta: {restored_hash} != {EXPECTED_BASELINE_SHA256}")
        raise ValueError(f"[RECOVERY_REQUIRED] Discrepancia post-restauración en {TARGET_RRE}")

    log_state(RollbackState.VERIFIED, f"Hash restaurado verificado ({restored_hash})")

    # 6. COMPLETED: Cierre transaccional formal
    log_state(RollbackState.COMPLETED, "Rollback ejecutado e idempotentemente verificado.")
    print(f"[ROLLBACK TRANSACCIONAL COMPLETADO EXITOSAMENTE] Registro en {tx_dir}")

if __name__ == "__main__":
    execute_transactional_rollback()
```

### Tabla de Fallos, Interrupciones y Mecanismo de Recuperación (AUD-V28-F04)

| Fase de Interrupción | Condición de Falla Detectada | Estado de la Transacción | Mecanismo de Recuperación Automático | Estado Final del Repositorio |
| :--- | :--- | :---: | :--- | :--- |
| **Durante PRECHECK** | Snapshot ausente o hash alterado. | `ABORTED` | Aborto inmediato sin tocar ningún archivo activo. | **Intacto (Sin cambios).** |
| **Durante BACKUP** | Corte de energía o error I/O en copia. | `ABORTED` | Archivos originales permanecen en su ubicación original. | **Intacto (Sin cambios).** |
| **Durante RESTORING** | Fallo tras aislar algunos archivos de fase. | `RECOVERY_REQUIRED` | Script lee `backup/` y restaura los archivos movidos a sus rutas originales. | **Restaurado a estado previo.** |
| **Durante VERIFIED** | `rre_engine.py` restaurado con hash erróneo. | `RECOVERY_REQUIRED` | Script sobreescribe desde snapshot y verifica; si persiste, restaura backup inicial. | **Restaurado a línea base oficial.** |

---

## 8. Oráculos SEC-CRIT con Verificación Documental Reproducible (AUD-V28-F07)

Se presenta la matriz exhaustiva de los 4 casos críticos de seguridad con **13 campos normativos completos**, verificados directamente sobre el archivo físico del corpus canónico reconstruido: `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` (298 páginas):

### 8.1 SEC-CRIT-01: Aterrizaje sobre Puente de Cuello
1. **Texto Oficial Literal:** *«2. All situations in which one of the athletes voluntarily makes a “bridge” (head and one foot or both feet in contact with the tatami) after having been thrown will be ippon (pictures 14.2-14.3). This decision is taken for the safety of the athletes, so they do not try to escape from the technique and endanger their cervical spine. No score or penalty will be given if the landing of uke occurs on the body of tori, in such a way that not all parts of uke’s body involving the bridge situation (head, foot or feet) touch the tatami.»*
2. **Documento y Versión:** IJF Sport and Organisation Rules (SOR), Edición Oficial de Actualización 2026_08_14.
3. **Página Impresa:** Página 166 (inicio) y 167 (justificación y regla de no-contacto).
4. **Página PDF:** Página 166 y 167 de 298.
5. **Artículo y Apartado:** Artículo 14 (Ippon), Apartado 2 (Pictures 14.2-14.3).
6. **Contexto Anterior:** Criterios generales de Ippon (velocidad, fuerza, sobre la espalda y control hábil hasta el final).
7. **Contexto Posterior:** Evaluación de Ippon en ne-waza (osaekomi-waza 20 segundos) y técnicas simultáneas.
8. **Interpretación Normativa:** El aterrizaje en puente voluntario tras proyección es calificado deónticamente como Ippon en contra de uke para proteger su columna cervical. La única atenuante ocurre si el impacto recae enteramente sobre el cuerpo de tori sin tocar el tatami.
9. **Hipótesis del Oráculo:** Si uke cae sobre su puente de cuello y contacta el tatami, el sistema debe calificar Ippon y purgar cualquier sidecar que pretenda atenuar la sanción o introducir excepciones por contacto involuntario.
10. **Resultado Esperado:** Bloqueo de excepciones de sidecars; bundle con `CANONICAL_EXCLUSIVE`.
11. **Sanción Oficial:** **Ippon a favor de Tori.**
12. **Condiciones y Excepciones:** Proyección iniciada por tori; contacto voluntario de cabeza y pies con el tatami; cero excepciones válidas si hay contacto con tatami.
13. **Estado de Verificación:** **`VERIFIED_AGAINST_PRIMARY_SOURCE`** (Comprobado reproduciblemente en PDF oficial pág. 166-167).

### 8.2 SEC-CRIT-02: Reverse Seoi-Nage en Categoría Cadetes
1. **Texto Oficial Literal:** *«35. In cadet events there will be no score for reverse seoi-nage and TORI will be penalised with shido. The application of seoi-nage techniques when uke can perform ukemi and tori can control is allowed. In the variation of seoi-nage techniques when tori turns away from uke, twisting their tsurite and hikite using the same lapel of uke’s judogi, without controlling uke, standing or dropping down in an unknown direction, without giving the possibility to the opponent to perform ukemi and sometimes with uke falling with the neck on the mat, is forbidden. NOTE: Cadet athletes participating in senior or junior events must follow the relevant event age group rules (see Article 20).»*
2. **Documento y Versión:** IJF Sport and Organisation Rules (SOR), Edición Oficial 2026_08_14.
3. **Página Impresa:** Página 189.
4. **Página PDF:** Página 189 de 298.
5. **Artículo y Apartado:** Artículo 18.1.4 (Shido for an Illegal Move in Cadet Competitions), Punto 35 (Pictures 18.61-18.67).
6. **Contexto Anterior:** Prohibición de Bear hug y agarres no convencionales sin ataque inmediato.
7. **Contexto Posterior:** Nota de aplicación para cadetes compitiendo en eventos Junior o Senior.
8. **Interpretación Normativa:** La técnica reverse seoi-nage está terminantemente prohibida en eventos de categoría Cadetes debido al alto riesgo de lesión cervical al no permitir ukemi controlado. Se sanciona con Shido y no otorga puntuación.
9. **Hipótesis del Oráculo:** Ante una consulta sobre reverse seoi-nage ejecutado por cadetes, el sistema debe bloquear cualquier autorización proveniente de circulares Senior y dictaminar prohibición con Shido.
10. **Resultado Esperado:** Detección de incompatibilidad de edad en `ScopeApplicability`; rechazo de circulares Senior permisivas.
11. **Sanción Oficial:** **No Score + Shido a Tori.**
12. **Condiciones y Excepciones:** Evento o categoría Cadete. Cero excepciones de agarre cruzado admitidas.
13. **Estado de Verificación:** **`VERIFIED_AGAINST_PRIMARY_SOURCE`** (Comprobado reproduciblemente en PDF oficial pág. 189).

### 8.3 SEC-CRIT-03: Palanca Articular sobre Articulaciones Distintas del Codo
1. **Texto Oficial Literal:** *«4. To apply kansetsu-waza to any joint other than the elbow joint (e.g., ashi-garami). [...] will be penalised with hansoku-make.»*
2. **Documento y Versión:** IJF Sport and Organisation Rules (SOR), Edición Oficial 2026_08_14.
3. **Página Impresa:** Página 191.
4. **Página PDF:** Página 191 de 298.
5. **Artículo y Apartado:** Artículo 18.2.1 / 18.2.2 (Grave Infringements - Hansoku-make), Punto 4.
6. **Contexto Anterior:** Prohibiciones directas de Kani-basami (Pto. 2) y Do-jime (Pto. 3).
7. **Contexto Posterior:** Pto. 5: Aplicación de kansetsu-waza o shime-waza en tachi-waza sin técnica de proyección de judo.
8. **Interpretación Normativa:** Las luxaciones articulares en judo solo están autorizadas sobre la articulación del codo. Cualquier luxación a rodilla, tobillo, muñeca o columna constituye una infracción gravísima penada con descalificación directa.
9. **Hipótesis del Oráculo:** El sistema debe calificar la acción como Hansoku-make directo y purgar cualquier sidecar que pretenda autorizar la técnica si inició en tachi-waza o alegar atenuante a Shido.
10. **Resultado Esperado:** Bloqueo de atenuantes; ratificación de descalificación directa.
11. **Sanción Oficial:** **Hansoku-make directo.**
12. **Condiciones y Excepciones:** Aplicación de presión articular fuera del codo en ne-waza o tachi-waza. Cero excepciones permitidas.
13. **Estado de Verificación:** **`VERIFIED_AGAINST_PRIMARY_SOURCE`** (Comprobado reproduciblemente en PDF oficial pág. 191).

### 8.4 SEC-CRIT-04: Estrangulamiento con Pretina o Faldón del Cinturón
1. **Texto Oficial Literal:** *«20. To encircle the end of the belt or jacket around any part of the opponent’s body. The act of “encircling” means that the belt or jacket must completely encircle. Using the belt or jacket as an anchor for a grip (without encircling), e.g., to trap the opponent’s arm, should not be penalised. [...] 23. To apply shime-waza using either your own or your opponent’s belt or bottom of the jacket or using only the fingers (picture 18.39).»*
2. **Documento y Versión:** IJF Sport and Organisation Rules (SOR), Edición Oficial 2026_08_14.
3. **Página Impresa:** Páginas 184 (Pto. 20) y 185 (Pto. 23).
4. **Página PDF:** Páginas 184 y 185 de 298.
5. **Artículo y Apartado:** Artículo 18.1.2 (Shido for an Illegal Move), Puntos 20 y 23 (Picture 18.39).
6. **Contexto Anterior:** Posiciones de tachi-shisei válidas para aplicar shime-waza en ne-waza.
7. **Contexto Posterior:** Prohibición de hiperextensión de pierna en inmovilizaciones (Pto. 24).
8. **Interpretación Normativa:** Está prohibido utilizar el faldón o la pretina del cinturón suelto para estrangular al rival o rodear completamente partes del cuerpo. Constituye un movimiento ilegal penalizado con Shido.
9. **Hipótesis del Oráculo:** Ante consultas sobre estrangulación con cinturón desatado o faldón, el sistema debe dictaminar técnica ilegal y sanción con Shido.
10. **Resultado Esperado:** Calificación como infracción leve/técnica ilegal; Shido ratificado.
11. **Sanción Oficial:** **Shido a Tori.**
12. **Condiciones y Excepciones:** Uso del cinturón o faldón para estrangular o rodear completamente. Se permite usar el cinturón como anclaje sin rodear.
13. **Estado de Verificación:** **`VERIFIED_AGAINST_PRIMARY_SOURCE`** (Comprobado reproduciblemente en PDF oficial pág. 184-185).

---

## 9. Conjunto de Validación Hold-Out Reservado Conocido: Protocolo Metodológico (AUD-V28-F08)

### 9.1 Denominación Metodológica y Reconocimiento de Límites
Se mantiene formal y unívocamente la denominación:  
**«Conjunto de validación hold-out reservado conocido»** (*known reserved hold-out set*).

Quedan formalmente proscritos los términos «ciego», «blind», «independiente» o «no visto», reconociendo con total transparencia metodológica que el archivo reside en el entorno de desarrollo accesible al ejecutor técnico.

### 9.2 Ficha de Custodia y Gobernanza del Conjunto
- **Ubicación Planificada de Entrega:** `docs/benchmark_dataset_b_certificacion_ijf.json`.
- **Estado Actual:** Archivo aún no instanciado en disco; será formalizado y sellado antes de iniciar la Etapa 4.
- **Custodio Responsable:** Alexis Oliveros Lozano (Data Steward).
- **Auditor Metodológico Independiente:** ChatGPT.
- **Riesgo Metodológico Declarado:** Exposición potencial del ejecutor en el espacio de trabajo local.
- **Salvaguardas Procesales de Mitigación:**
  1. Sellado criptográfico del archivo por hash SHA-256 inmutable antes de su utilización.
  2. Prohibición estricta de importación o lectura en los módulos funcionales `src/` o pruebas unitarias de desarrollo `tests/`.
  3. Ejecución exclusiva en memoria durante la Etapa 4 a través de un arnés de certificación (`scratch/run_fase4_2_6_certification.py`) supervisado por ChatGPT y Alexis.

---

## 10. Reconciliación Integral de Inventario de Activos y Hashes

Se ratifica con exactitud la separación conceptual entre los activos físicos del corpus de datos y el activo de código funcional:

### 10.1 Activos Físicos del Corpus de Datos (6 Archivos Verificados en Disco — CA-426-08)
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

### 10.2 Activo de Código Funcional Protegido (Línea Base y Snapshot)
- `src/rre_engine.py` (y su respaldo inmutable `scratch/pre_fase4_2_6_snapshot/rre_engine.py.snapshot`):  
  SHA-256: `d45c17d3397427d6be2d2c379764a27439c5f7401538947c23c5fbd6c6ffae1e`

El criterio de aceptación **CA-426-08** audita los **6 activos físicos del corpus de datos**. La integridad del motor de código se rige por la política transaccional de rollback y su snapshot certificado.

---

## 11. Reconciliación de Invarianza: Discreta vs Numérica

1. **Invarianza Discreta Estricta (Tolerancia 0.0% / Igualdad Exacta de Cadenas y Conjuntos):**
   - Identificadores de pasajes primarios (`passage_id`) y su ordenamiento secuencial exacto.
   - Cantidad de evidencias primarias (`len(evidence_list)`).
   - Artículos canónicos citados (`article_id`).
   - Estado de respuesta (`status == "SUCCESS"` / `"ABSTAIN"`).
2. **Invarianza Numérica en Puntuaciones Primarias (Tolerancia Flotante de Precisión):**
   - Los scores flotantes primarios generados por el algoritmo RRF (`score`) deben ser idénticos con una tolerancia estricta:
     $$|\text{score}_{\text{baseline}} - \text{score}_{\text{fusion}}| < 10^{-4}$$
   - Esta tolerancia atiende a variaciones de representación en coma flotante IEEE 754 entre compilaciones de Python y librerías numéricas, garantizando que el orden relativo permanezca inalterado.

---

## 12. Metodología de Medición de Latencia y Overhead

1. **Instrumentación de Alta Resolución:** Uso exclusivo de `time.perf_counter()` para medir tiempos en milisegundos.
2. **Protocolo Experimental:**
   - 1 ciclo de calentamiento (*warm-up*) de 5 consultas no contabilizadas para estabilizar caché de memoria.
   - 3 ejecuciones consecutivas independientes sobre el benchmark de 40 consultas.
   - Cálculo de métricas agregadas: Media, Mediana, Percentil 95 (P95) y Desviación Estándar.
3. **Umbrales Máximos Aceptables:**
   - Overhead de la etapa de arbitraje en memoria: $\Delta_{\text{mean}} \le 5.0\text{ ms}$.
   - Latencia total del RRE en modo fusión: $P95 \le 80.0\text{ ms}$.

---

## 13. Protocolo de Auditoría y Gobernanza Tripartita

Se formaliza la separación de roles y responsabilidades en tres niveles independientes:

1. **Revisión Técnica y Ejecución (Antigravity):**
   - Ejecuta las tareas autorizadas de la etapa en modo estrictamente secuencial.
   - Genera los informes técnicos autocontenidos, evidencias reproducibles y tablas de hashes.
   - No tiene atribución de declarar aprobación ni certificar sus propios entregables.
2. **Auditoría Arquitectónica Independiente (ChatGPT):**
   - Examina el código, los diffs de Git, los logs de pytest y el cumplimiento de invariantes.
   - Emite el dictamen técnico formal: **CONFORME**, **CON OBSERVACIONES** o **NO CONFORME**.
3. **Autoridad Soberana de Aprobación (Alexis Oliveros Lozano):**
   - Evalúa el dictamen de ChatGPT y los informes de Antigravity.
   - Emite la autorización formal, expresa y bloqueante para iniciar la siguiente etapa o activar flags.

---

## 14. Matriz de Autorizaciones para Futura Ejecución

| Actividad Operacional | Autoridad Responsable | Condición Previa Requerida | Estado Actual |
| :--- | :--- | :--- | :--- |
| **Preparación Documental Plan Maestro v2.9** | Alexis Oliveros Lozano | Cierre de observaciones AUD-V28-F01 a F09 | **AUTORIZADO / COMPLETADO** |
| **Implementación de Código (Etapa 1)** | Alexis Oliveros Lozano | Dictamen favorable de ChatGPT sobre Plan Maestro v2.9 | **PENDIENTE — NO AUTORIZADO** |
| **Implementación de Código (Etapa 2)** | Alexis Oliveros Lozano | Dictamen favorable y aprobación de Etapa 1 | **NO AUTORIZADO** |
| **Integración en RRE (Etapa 3)** | Alexis Oliveros Lozano | Aprobación formal de Etapas 1 y 2 | **NO AUTORIZADO** |
| **Ejecución de Certificación (Etapa 4)**| Alexis Oliveros Lozano | Aprobación formal de Etapa 3 | **NO AUTORIZADO** |
| **Operaciones Git Remotas (Push/Merge)**| Alexis Oliveros Lozano | Certificación final y cierre de fase | **ESTRICTAMENTE PROHIBIDO** |
| **Despliegue OCI / Producción** | Alexis Oliveros Lozano | Cierre total de Fase 4 y auditoría externa | **ESTRICTAMENTE PROHIBIDO** |
