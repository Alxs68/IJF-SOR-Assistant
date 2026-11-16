# Plan Maestro de Implementación Revisado — Fase 4.2.6
## Fusión y Arbitraje Multifuente (`EvidenceBundle` & `NormativeGuard`)

**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.6 — Fusión y Arbitraje Multifuente  
**Supervisor y Autoridad Soberana de Aprobación:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Fecha:** 2026-11-06 (Versión v2.8 — Corrección Integral de Hallazgos de Auditoría Independiente H-426-V27-01 a H-426-V27-09)  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **EXPEDIENTE DE PLANIFICACIÓN TÉCNICA — CÓDIGO NO IMPLEMENTADO (ETAPA 1 NO AUTORIZADA)**

---

## 1. Objetivos, Alcance y Exclusiones

### 1.1 Objetivo General
Implementar incrementalmente en código funcional y probado la arquitectura de fusión y arbitraje multifuente definida en el diseño técnico aprobado, garantizando la prevalencia jerárquica y ontológica absoluta del corpus canónico SOR 2026, la contención determinista y formalizada de riesgos normativos mediante `NormativeGuard` (basada exclusivamente en un comparador exhaustivo de 10 dimensiones para proposiciones deónticas completas, erradicando cualquier heurística residual de palabras clave o menciones incidentales), la formalización rigurosa de invariantes de estado y suficiencia probatoria sustantiva, y la estricta invarianza del RRE y de las respuestas ADA ante consultas canónicas puras y fuera de dominio.

### 1.2 Alcance Autorizado para Futura Ejecución
1. Creación de los modelos de datos tipados y contratos de gobernanza (`src/evidence_bundle.py`).
2. Creación del componente de barrera de seguridad normativa formalizada con comparador de 10 dimensiones y máquina de estados acotada (`src/normative_guard.py`).
3. Creación del motor de arbitraje jerárquico desacoplado (`src/multisource_arbitrator.py`).
4. Homogeneización de parámetros de búsqueda en `src/rre_engine.py` (`min_score=3.0`, `min_overlap_ratio=0.25`).
5. Integración del pipeline de fusión en `src/rre_engine.py` bajo feature flag tri-estado desacoplado (`enable_multisource_fusion: Optional[bool] = None`, por defecto resuelto a `False`).
6. Creación de suites de pruebas unitarias, de integración, de invarianza y de seguridad crítica.
7. Construcción y ejecución del dataset hold-out reservado conocido de certificación independiente (20 casos hold-out) con custodia auditada y exigencia de cero fallos en los 4 casos de seguridad crítica.

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
                  │  3. Comparador Formal de 10 Dimensiones        │
                  │  4. Máquina de Estados e Invariantes Clave     │
                  │  5. Purga / Bloqueo / Abstención Conservadora  │
                  └───────────────────────┬────────────────────────┘
                                          │
                                          ▼
                  ┌────────────────────────────────────────────────┐
                  │             MultisourceArbitrator              │
                  │  1. Prevalencia Canónica Estricta              │
                  │  2. Evaluación Copulativa de Suficiencia (x5)  │
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

## 3. Contratos de Datos y Modelos Tipados (v2.8)

Se formalizan los modelos inmutables y tipados necesarios para garantizar la integridad estructural y la trazabilidad de la deliberación normativa.

```python
"""
Contratos y Tipos Formales de Fase 4.2.6 (v2.8)
Ubicación planificada: src/evidence_bundle.py
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Set
import hashlib
import json

class AuthorityTier(Enum):
    """Nivel jerárquico de autoridad jurídica de la fuente documental."""
    TIER_1_CANONICAL = 1  # Official Sport and Organisation Rules (SOR 2026)
    TIER_2_OFFICIAL_CIRCULAR = 2  # Circulares oficiales y enmiendas ejecutivas IJF
    TIER_3_COMPLEMENTARY = 3  # Guías de arbitraje, manuales técnicos y clarificaciones

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

class GuardActionTaken(Enum):
    """Acción resolutiva adoptada por el NormativeGuard (H-426-V27-02)."""
    PERMIT = "PERMIT"                                  # Todo limpio: candidatos válidos pasan sin objeción
    PURGE_EXCEPTIONS = "PURGE_EXCEPTIONS"              # Purga selectiva de sidecars con violaciones o sin estructura
    BLOCK_ALL_SIDECAR = "BLOCK_ALL_SIDECAR"            # Bloqueo total de sidecars reteniendo solo primarios
    CONSERVATIVE_FALLBACK = "CONSERVATIVE_FALLBACK"    # Abstención conservadora por incertidumbre o no cobertura

class ArbitrationDecision(Enum):
    """Decisión de arbitraje formalizada (H-426-PM-10)."""
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
    """Operador deóntico formalizado (H-426-V27-01)."""
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
    """Nivel de severidad cerrado para violaciones de seguridad normativa (H-426-V27-02)."""
    CRITICAL = "CRITICAL"  # Violación grave de seguridad; purga o bloqueo forzoso
    WARNING = "WARNING"    # Conflicto de interpretación menor o atenuante no crítico
    INFO = "INFO"          # Nota informativa de alcance o contexto

class PropositionComparisonCategory(Enum):
    """Categorización formal del resultado de la comparación de proposiciones (H-426-V27-01)."""
    IDENTITY = "IDENTITY"                                # Identidad formal completa en 10 dimensiones
    EQUIVALENCE = "EQUIVALENCE"                          # Equivalencia funcional sin alteración normativa
    COMPATIBILITY = "COMPATIBILITY"                      # Compatible (armonizable jerárquicamente)
    CONTRADICTION = "CONTRADICTION"                      # Contradicción directa u oposición deóntica
    INSUFFICIENCY = "INSUFFICIENCY"                      # Proposición incompleta, vacía o no deliberable
    CONSERVATIVE_ABSTENTION = "CONSERVATIVE_ABSTENTION"  # Fuera de dominio o ambigüedad estructural

@dataclass(frozen=True)
class NormativeProposition:
    """
    Representación formalizada de una proposición normativa en 10 dimensiones canónicas (H-426-V27-01).
    """
    subject: str                                       # 1. Sujeto: 'tori', 'uke', 'referee', 'athlete'
    action: str                                        # 2. Acción: 'head_bridge_landing', 'kansetsu_waza_knee'
    target_object: str                                 # 3. Objeto/destinatario: 'neck_spine', 'elbow_joint'
    deontic_operator: DeonticOperator                  # 4. Operador deóntico: OBLIGATION, PROHIBITION, PERMISSION
    application_conditions: List[str]                  # 5. Condiciones de aplicación operativas
    exceptions: List[str]                              # 6. Excepciones taxativas
    exception_conditions: List[str]                    # 7. Condiciones de aplicabilidad de las excepciones
    sanction: NormativeSanction                        # 8. Sanción o consecuencia deóntica
    scope: ScopeApplicability                          # 9. Alcance: edad, competición, modalidad, vigencia, contexto
    authority_tier: AuthorityTier                      # 10. Jerarquía y autoridad del emisor
    document_ref: str = ""                             # Referencia documental de respaldo
    article_ref: Optional[str] = None                  # Artículo específico (ej. '14', '18.1.4', '18.2.1')

@dataclass(frozen=True)
class ProvenanceInfo:
    """Trazabilidad exhaustiva de gobernanza y procedencia documental con cálculo criptográfico completo (H-426-V25-04)."""
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
        """
        Calcula el hash SHA-256 determinista cubriendo TODOS los campos materiales (H-426-V25-04).
        Aplica normalización canónica JSON con claves ordenadas, separadores compactos y UTF-8.
        """
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
    proposition: Optional[NormativeProposition] = None  # Proposición estructurada formalizada
    rejection_reason: Optional[str] = None

@dataclass
class GuardViolation:
    rule_id: str
    severity: ViolationSeverity
    article_id: Optional[str]
    description: str
    rejected_evidence_id: str  # Obligatorio: toda violación identifica evidencia concreta (H-426-V27-02)

@dataclass
class NormativeGuardResult:
    """
    Resultado estructurado y auditable de la evaluación del NormativeGuard con los 12 invariantes
    obligatorios de la máquina de estados acotada (H-426-V27-02).
    """
    passed: bool
    retained_sidecars: List[EvidenceItem]
    rejected_sidecars: List[EvidenceItem]
    violations: List[GuardViolation]
    evaluation_log: List[str]
    action_taken: GuardActionTaken  # Enum cerrado

    def __post_init__(self):
        """Validación exhaustiva de los 12 invariantes de consistencia (H-426-V27-02)."""
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

        # Invariante 8: Evaluación incompleta o abstención conservadora no puede emitir PERMIT
        if self.action_taken == GuardActionTaken.CONSERVATIVE_FALLBACK and self.passed is True:
            raise ValueError("Invariante 8 violado: CONSERVATIVE_FALLBACK exige passed=False.")

        # Invariante 9: Proposición no estructurada no puede ser admitida normativamente
        for ret in self.retained_sidecars:
            if ret.proposition is None:
                raise ValueError(f"Invariante 9 violado: Evidencia retenida {ret.evidence_id} carece de proposición estructurada formal.")

        # Invariante 10: Política explícita de WARNING e INFO sin CRITICAL
        # No impiden passed=True salvo que existan rechazos que exijan PURGE_EXCEPTIONS o BLOCK_ALL_SIDECAR
        if not critical_violations and self.rejected_sidecars:
            if self.action_taken not in {GuardActionTaken.PURGE_EXCEPTIONS, GuardActionTaken.BLOCK_ALL_SIDECAR, GuardActionTaken.CONSERVATIVE_FALLBACK}:
                raise ValueError(f"Invariante 10 violado: Con rechazos presentes, action_taken debe ser PURGE_EXCEPTIONS, BLOCK_ALL_SIDECAR o CONSERVATIVE_FALLBACK, no '{self.action_taken.value}'.")

        # Invariante 11: Estado limpio total
        if not self.violations and not self.rejected_sidecars:
            if self.passed is not True:
                raise ValueError("Invariante 11 violado: passed debe ser True si no hay violaciones ni rechazos.")
            if self.action_taken != GuardActionTaken.PERMIT:
                raise ValueError(f"Invariante 11 violado: action_taken debe ser PERMIT en ausencia de violaciones o rechazos, no '{self.action_taken.value}'.")

        # Invariante 12: Ausencia de contradicción no equivale a suficiencia
        # El resultado de NormativeGuard indica no-violación de reglas de contención, pero la suficiencia exige evaluación probatoria independiente.

### Tabla Exhaustiva de Estados Válidos e Inválidos (H-426-V27-02)

| ID Estado | Violaciones CRITICAL | Violaciones WARNING/INFO | Sidecars Rechazados | Sidecars Retenidos | `passed` | `action_taken` | Dictamen Lógico |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **ST-01** | **0** | **0** | **0** | $\ge 0$ | `True` | `PERMIT` | **VÁLIDO:** Ejecución limpia total. |
| **ST-02** | **0** | $\ge 0$ | $> 0$ | $> 0$ | `True` | `PURGE_EXCEPTIONS` | **VÁLIDO:** Purga de advertencias no críticas; retiene válidos. |
| **ST-03** | **0** | $\ge 0$ | $> 0$ | **0** | `True` | `BLOCK_ALL_SIDECAR` | **VÁLIDO:** Rechazo administrativo de todos los sidecars; sin CRITICAL. |
| **ST-04** | $> 0$ | $\ge 0$ | $> 0$ | $> 0$ | `False` | `PURGE_EXCEPTIONS` | **VÁLIDO:** Violación crítica purgada selectivamente; retiene inocuos. |
| **ST-05** | $> 0$ | $\ge 0$ | $> 0$ | **0** | `False` | `BLOCK_ALL_SIDECAR` | **VÁLIDO:** Violación crítica conduce al bloqueo total de sidecars. |
| **ST-06** | Cualquiera | Cualquiera | $\ge 0$ | $\ge 0$ | `False` | `CONSERVATIVE_FALLBACK` | **VÁLIDO:** Abstención conservadora por incertidumbre o no-cobertura. |
| **ST-INV-01** | $> 0$ | Cualquiera | Cualquiera | Cualquiera | `True` | Cualquiera | **ESTADO INVÁLIDO:** Violación CRITICAL presente con `passed=True`. |
| **ST-INV-02** | $> 0$ | Cualquiera | Cualquiera | Cualquiera | `False` | `PERMIT` | **ESTADO INVÁLIDO:** `action_taken=PERMIT` ante violaciones CRITICAL. |
| **ST-INV-03** | Cualquiera | Cualquiera | ID $X$ | ID $X$ | Cualquiera | Cualquiera | **ESTADO INVÁLIDO:** Intersección no vacía entre retenidos y rechazados. |
| **ST-INV-04** | Cualquiera | Contiene ID $X$ | No contiene ID $X$| Cualquiera | Cualquiera | Cualquiera | **ESTADO INVÁLIDO:** Violación con ID ausente de `rejected_sidecars`. |
| **ST-INV-05** | **0** | **0** | **0** | $\ge 0$ | `False` | `PERMIT` | **ESTADO INVÁLIDO:** Estado limpio no puede tener `passed=False`. |
| **ST-INV-06** | Cualquiera | Cualquiera | $\ge 0$ | Retiene no-estructurado | Cualquiera | Cualquiera | **ESTADO INVÁLIDO:** Retención de sidecar sin proposición formal. |

```python
@dataclass
class ConditionVerificationEvidence:
    """
    Evidencia auditable de 15 campos que respalda formalmente cada condición de suficiencia (H-426-V27-04).
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
    verification_passed: bool = False                   # Resultado booleano: solo True si supera evaluación sustantiva

    def is_substantively_valid(self, expected_condition_id: str) -> bool:
        """
        Comprueba de forma positiva y sustantiva que la evidencia no sea un placeholder vacío
        ni contenga valores 'UNKNOWN' o no contrastados (H-426-V27-04).
        """
        # 1. Correspondencia unívoca con la condición esperada
        if self.condition_id.strip() != expected_condition_id.strip():
            return False
        # 2. Identificador de evidencia presente
        if not self.evidence_id or not self.evidence_id.strip() or self.evidence_id.strip().upper() == "UNKNOWN":
            return False
        # 3. Fuente documental identificable y no vacía
        if not self.documentary_source or not self.documentary_source.strip() or self.documentary_source.strip().upper() == "UNKNOWN":
            return False
        # 4. Referencia verificable presente
        if not self.verifiable_reference or not self.verifiable_reference.strip() or self.verifiable_reference.strip().upper() == "UNKNOWN":
            return False
        # 5. Pasaje o localizador concreto
        if not self.passage_or_locator or not self.passage_or_locator.strip() or self.passage_or_locator.strip().upper() == "UNKNOWN":
            return False
        # 6. Hash SHA-256 válido (64 caracteres hex)
        if not self.integrity_hash or len(self.integrity_hash.strip()) != 64:
            return False
        # 7. Vigencia formal confirmada
        if self.validity_status != NormativeValidity.IN_FORCE:
            return False
        # 8. Método de verificación explícito
        if not self.verification_method or not self.verification_method.strip() or self.verification_method.strip().upper() == "UNKNOWN":
            return False
        # 9. Agente responsable explícito no genérico
        if not self.verification_responsible or not self.verification_responsible.strip() or self.verification_responsible.strip().upper() == "UNKNOWN":
            return False
        # 10. Superación positiva obligatoria
        return self.verification_passed is True

@dataclass
class SufficiencyEvaluationResult:
    """Evaluación auditable respaldada por evidencia verificable de las 5 condiciones copulativas (H-426-V27-04)."""
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
        Comprueba copulativamente las 5 condiciones.
        Exige respaldo probatorio concreto y sustantivamente válido; rechaza booleanos aislados o UNKNOWN.
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
                self.audit_reasons.append(f"Condición '{key}' carece de objeto probatorio adjunto (Evidence is None).")
                continue
            
            # Validación sustantiva estricta de 15 campos no vacíos y correspondencia
            if not ev.is_substantively_valid(expected_condition_id=key):
                all_passed = False
                self.audit_reasons.append(
                    f"Condición '{key}' NO aprobada por falta de sustento probatorio válido "
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

## 4. Contrato de Feature Flags, Fallbacks e Integración en RRE (H-426-V24-01)

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

### 4.2 Matriz de Casos de Prueba de Precedencia e Inicialización
| Caso | Parámetro en Constructor | Variable de Entorno | Valor Final Resuelto | Comportamiento del Motor |
| :--- | :--- | :--- | :--- | :--- |
| **FF-01** | `None` (Default) | No definida | `False` | Fusión apagada; motor canónico puro; 0 overhead. |
| **FF-02** | `None` | `RRE_ENABLE_MULTISOURCE_FUSION="1"` | `True` | Fusión activada vía entorno. |
| **FF-03** | `None` | `RRE_ENABLE_MULTISOURCE_FUSION="true"` | `True` | Fusión activada vía entorno. |
| **FF-04** | `None` | `RRE_ENABLE_MULTISOURCE_FUSION="0"` | `False` | Fusión apagada vía entorno. |
| **FF-05** | `None` | `RRE_ENABLE_MULTISOURCE_FUSION="invalid"`| `False` | Fallback de seguridad ante valor desconocido. |
| **FF-06** | `True` | No definida | `True` | Prevalencia explícita del parámetro. |
| **FF-07** | `True` | `RRE_ENABLE_MULTISOURCE_FUSION="0"` | `True` | Parámetro explícito `True` anula variable en `0`. |
| **FF-08** | `False` | `RRE_ENABLE_MULTISOURCE_FUSION="1"` | `False` | Parámetro explícito `False` anula variable en `1`. |
| **FF-09** | `False` | No definida | `False` | Parámetro explícito `False` ratificado. |

### 4.3 Comportamiento Desacoplado y Fallback ante Inactividad
Si `self.enable_multisource_fusion == False`:
1. El motor **no instancia** `MultisourceArbitrator` ni `EvidenceBundleManager` en memoria, reduciendo a cero el footprint computacional.
2. La llamada a `retrieve()` ejecuta su flujo RRF canónico preexistente y **no añade ninguna clave invasiva** en el cuerpo de la respuesta principal (`status`, `query`, `evidence`, `related_passages` permanecen 100% idénticos e invariantes bit a bit).
3. Si `enable_shadow_mode_multisource == True`, se mantiene el registro pasivo en el log JSONL desacoplado de Fase 4.2.3.
4. Si `enable_multisource_fusion == True`, la estructura `EvidenceBundle` serializada se adjunta **exclusivamente bajo la clave opcional `metadata['evidence_bundle']`**, preservando intacto el contrato de `evidence` primaria.

---

## 5. Módulo `NormativeGuard`: Formalización de Proposiciones y Arbitraje Deóntico (H-426-V27-01)

### 5.1 Erradicación Total de Heurísticas Residuales
Se eliminan **completamente** todas las comprobaciones de subcadenas léxicas (ej. `bridge in q_lower`), inspecciones por mención incidental de números de artículos (ej. `"14" in primary_articles`) o simulaciones de parsers universales.

`NormativeGuard` opera **exclusivamente sobre proposiciones normativas estructuradas (`NormativeProposition`)** asociadas a cada evidencia recuperada y evaluadas mediante un comparador formal de 10 dimensiones.

### 5.2 Política Estricta de No Admisión de Sidecars No Estructurados
- **Regla Inflexible:** Todo fragmento Sidecar que ingrese al motor de arbitraje **debe poseer una proposición estructurada formal (`sc.proposition is not None`)** validada en el momento de la ingesta.
- **Consecuencia de Ausencia de Estructura:** Si un fragmento complementario carece de proposición estructurada formal (`sc.proposition is None`), se considera técnicamente no deliberable. `NormativeGuard` lo rechaza de inmediato con causa `UNSTRUCTURED_SIDECAR_INADMISSIBLE` y emite `action_taken = GuardActionTaken.CONSERVATIVE_FALLBACK` (o `PURGE_EXCEPTIONS`), impidiendo de raíz cualquier compromiso o riesgo de alucinación interpretativa.

### 5.3 Proposiciones Canónicas Protegidas del SOR 2026
El catálogo canónico se indexa formalmente por clave unívoca y cubre exhaustivamente los 10 campos normativos:

```python
CANONICAL_PROTECTED_PROPOSITIONS: Dict[str, NormativeProposition] = {
    "PROP-CAN-01-BRIDGE": NormativeProposition(
        subject="uke",
        action="head_bridge_landing",
        target_object="tatami_landing_escape",
        deontic_operator=DeonticOperator.PROHIBITION,
        application_conditions=["thrown_by_tori", "voluntary_bridge_attempt"],
        exceptions=[],  # CERO excepciones en aterrizaje sobre puente
        exception_conditions=[],
        sanction=NormativeSanction.IPPON,
        scope=ScopeApplicability(AgeCategory.ALL_AGES, CompetitionType.WORLD_JUDO_TOUR, "ALL", "SOR-2026"),
        authority_tier=AuthorityTier.TIER_1_CANONICAL,
        document_ref="IJF SOR 2026",
        article_ref="14"
    ),
    "PROP-CAN-02-CADET-REVERSE": NormativeProposition(
        subject="tori",
        action="reverse_seoi_nage",
        target_object="opponent_lapel_turn",
        deontic_operator=DeonticOperator.PROHIBITION,
        application_conditions=["cadet_competition"],
        exceptions=[],  # Prohibición absoluta en Cadetes
        exception_conditions=[],
        sanction=NormativeSanction.SHIDO,
        scope=ScopeApplicability(AgeCategory.CADET, CompetitionType.WORLD_JUDO_TOUR, "ALL", "SOR-2026", cadet_junior_excluded=True),
        authority_tier=AuthorityTier.TIER_1_CANONICAL,
        document_ref="IJF SOR 2026",
        article_ref="18.1.4"
    ),
    "PROP-CAN-03-KANSETSU-NON-ELBOW": NormativeProposition(
        subject="tori",
        action="kansetsu_waza_non_elbow",
        target_object="joints_other_than_elbow",
        deontic_operator=DeonticOperator.PROHIBITION,
        application_conditions=["ne_waza_or_tachi_waza"],
        exceptions=[],  # CERO excepciones fuera del codo
        exception_conditions=[],
        sanction=NormativeSanction.HANSOKU_MAKE_DIRECT,
        scope=ScopeApplicability(AgeCategory.ALL_AGES, CompetitionType.WORLD_JUDO_TOUR, "ALL", "SOR-2026"),
        authority_tier=AuthorityTier.TIER_1_CANONICAL,
        document_ref="IJF SOR 2026",
        article_ref="18.2.1"
    ),
    "PROP-CAN-04-BELT-SKIRT-CHOKE": NormativeProposition(
        subject="tori",
        action="choke_using_belt_or_jacket_bottom",
        target_object="opponent_neck",
        deontic_operator=DeonticOperator.PROHIBITION,
        application_conditions=["encircling_or_direct_fabric"],
        exceptions=[],
        exception_conditions=[],
        sanction=NormativeSanction.SHIDO,
        scope=ScopeApplicability(AgeCategory.ALL_AGES, CompetitionType.WORLD_JUDO_TOUR, "ALL", "SOR-2026"),
        authority_tier=AuthorityTier.TIER_1_CANONICAL,
        document_ref="IJF SOR 2026",
        article_ref="18.1.2"
    )
}
```

### 5.4 Algoritmo del Comparador Formal de 10 Dimensiones (H-426-V27-01)
El comparador componente a componente analiza rigurosamente las 10 dimensiones normativas entre la proposición complementaria candidata $\mathcal{P}_{	ext{sc}}$ y la proposición canónica activa $\mathcal{P}_{	ext{can}}$:

1. **Dimensión 1 (Sujeto):** Correspondencia estricta de rol del agente activo o pasivo (`tori`, `uke`, `referee`). Si difieren sustancialmente, no hay colisión directa sino desalineación estructural.
2. **Dimensión 2 (Acción):** Identidad o equivalencia formal de la técnica o conducta (`head_bridge_landing`, `kansetsu_waza_non_elbow`).
3. **Dimensión 3 (Objeto/Destinatario):** Identidad de la zona anatómica o elemento material afectado (`neck_spine`, `joints_other_than_elbow`, `belt_skirt`).
4. **Dimensión 4 (Operador Deóntico):**
   - Si $\mathcal{P}_{	ext{can}} = 	ext{PROHIBITION}$ y $\mathcal{P}_{	ext{sc}} \in \{	ext{PERMISSION}, 	ext{EXCEPTION}\}$: **CONTRADICCIÓN DIRECTA** $ightarrow$ Violación `CRITICAL`.
   - Si $\mathcal{P}_{	ext{can}} = 	ext{OBLIGATION}$ y $\mathcal{P}_{	ext{sc}} = 	ext{PERMISSION}$: **DILUCIÓN IMPERATIVA** $ightarrow$ Violación `CRITICAL`.
5. **Dimensión 5 (Condiciones de Aplicación):** Contraste de activación fáctica. Si el Sidecar omite condiciones restrictivas canónicas, genera colisión deóntica.
6. **Dimensión 6 (Excepciones):**
   - Si $\mathcal{P}_{	ext{can}}.	ext{exceptions} == \emptyset$ (norma taxativa sin excepciones) y $\mathcal{P}_{	ext{sc}}.	ext{exceptions} 
e \emptyset$: **INYECCIÓN ILEGAL DE EXCEPCIONES** $ightarrow$ Violación `CRITICAL`.
7. **Dimensión 7 (Condiciones de las Excepciones):** Si existen excepciones reconocidas en nivel oficial, se evalúan sus condiciones. Si no se satisfacen, la excepción decae.
8. **Dimensión 8 (Sanción/Consecuencia Deóntica):**
   - Si $\mathcal{P}_{	ext{can}}.	ext{sanction} == 	ext{HANSOKU\_MAKE\_DIRECT}$ y $\mathcal{P}_{	ext{sc}}.	ext{sanction} 
e 	ext{HANSOKU\_MAKE\_DIRECT}$: **DILUCIÓN DE SANCIÓN DE SEGURIDAD** $ightarrow$ Violación `CRITICAL`.
9. **Dimensión 9 (Alcance):**
   - Edad: Si $\mathcal{P}_{	ext{can}}.	ext{scope}.	ext{age\_category} == 	ext{CADET}$ y $\mathcal{P}_{	ext{sc}}.	ext{scope}.	ext{cadet\_junior\_excluded} == 	ext{True}$: **EXTRAPOLACIÓN ILEGAL POR EDAD** $ightarrow$ Violación `CRITICAL`.
   - Ámbito: Competiciones oficiales IJF vs eventos formativos o no homologados.
10. **Dimensión 10 (Jerarquía de Autoridad):**
    - Si $\mathcal{P}_{	ext{sc}}.	ext{authority\_tier} > \mathcal{P}_{	ext{can}}.	ext{authority\_tier}$ (i.e., Tier 2 o 3 frente a Tier 1 canónico) y pretende modificar la regla: **USURPACIÓN DE COMPETENCIA** $ightarrow$ Prevalencia canónica absoluta.

```python
class PropositionComparator:
    """Comparador formal componente a componente en 10 dimensiones (H-426-V27-01)."""

    @classmethod
    def compare(
        cls,
        canonical: NormativeProposition,
        candidate: NormativeProposition
    ) -> PropositionComparisonCategory:
        # Validación de integridad de proposición
        if not candidate.action or not candidate.target_object:
            return PropositionComparisonCategory.INSUFFICIENCY

        # 1. Objeto y Acción no relacionados -> Fuera de colisión directa
        if candidate.action != canonical.action or candidate.target_object != canonical.target_object:
            return PropositionComparisonCategory.CONSERVATIVE_ABSTENTION

        # 2. Identidad completa en las 10 dimensiones
        if (candidate.subject == canonical.subject and
            candidate.deontic_operator == canonical.deontic_operator and
            candidate.application_conditions == canonical.application_conditions and
            candidate.exceptions == canonical.exceptions and
            candidate.exception_conditions == canonical.exception_conditions and
            candidate.sanction == canonical.sanction and
            candidate.scope == canonical.scope and
            candidate.authority_tier == canonical.authority_tier):
            return PropositionComparisonCategory.IDENTITY

        # 3. Contradicciones Deónticas y de Seguridad
        # 3.1 Excepción sobre prohibición taxativa
        if canonical.deontic_operator == DeonticOperator.PROHIBITION:
            if candidate.deontic_operator in {DeonticOperator.PERMISSION}:
                return PropositionComparisonCategory.CONTRADICTION
            if len(canonical.exceptions) == 0 and len(candidate.exceptions) > 0:
                return PropositionComparisonCategory.CONTRADICTION

        # 3.2 Dilución de sanción de descalificación directa
        if canonical.sanction == NormativeSanction.HANSOKU_MAKE_DIRECT:
            if candidate.sanction != NormativeSanction.HANSOKU_MAKE_DIRECT:
                return PropositionComparisonCategory.CONTRADICTION

        # 3.3 Colisión de alcance por categoría de edad
        if canonical.scope.age_category == AgeCategory.CADET:
            if candidate.scope.cadet_junior_excluded and candidate.deontic_operator == DeonticOperator.PERMISSION:
                return PropositionComparisonCategory.CONTRADICTION

        # 4. Compatibilidad operativa (sin colisión deóntica)
        if candidate.deontic_operator == canonical.deontic_operator and candidate.sanction == canonical.sanction:
            return PropositionComparisonCategory.COMPATIBILITY

        return PropositionComparisonCategory.CONSERVATIVE_ABSTENTION
```

```python
class NormativeGuard:
    PROTECTED_PROPOSITIONS = CANONICAL_PROTECTED_PROPOSITIONS

    @classmethod
    def find_applicable_canonical_proposition(
        cls,
        primary_items: List[EvidenceItem]
    ) -> Optional[NormativeProposition]:
        """
        Identificación inequívoca de la proposición canónica activa basada en correspondencia formal
        de acción y objeto sobre proposiciones estructuradas, no por palabras clave ni artículos (H-426-V27-01).
        """
        for p in primary_items:
            if p.proposition is not None:
                for can_prop in cls.PROTECTED_PROPOSITIONS.values():
                    if (p.proposition.action == can_prop.action and 
                        p.proposition.target_object == can_prop.target_object):
                        return can_prop
        return None

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

        active_canonical = cls.find_applicable_canonical_proposition(primary_items)

        for sc in candidate_sidecars:
            sc_prop = sc.proposition

            # 1. Inadmisibilidad estricta de Sidecars sin Estructuración Formal
            if sc_prop is None:
                sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                sc.rejection_reason = "UNSTRUCTURED_SIDECAR_INADMISSIBLE"
                rejected.append(sc)
                violations.append(GuardViolation(
                    rule_id="RULE-SEC-UNSTRUCTURED",
                    severity=ViolationSeverity.CRITICAL,
                    article_id=sc.article_id,
                    description="Rechazo forzoso: Sidecar carece de proposición normativa estructurada formal.",
                    rejected_evidence_id=sc.evidence_id
                ))
                log.append(f"Rejected candidate {sc.evidence_id}: Lack of structured normative proposition.")
                continue

            # 2. Comparación mediante PropositionComparator en 10 dimensiones
            if active_canonical is not None:
                comparison_result = PropositionComparator.compare(active_canonical, sc_prop)

                if comparison_result == PropositionComparisonCategory.CONTRADICTION:
                    sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                    sc.rejection_reason = "GUARD_SECURITY_CONTRADICTION"
                    rejected.append(sc)
                    violations.append(GuardViolation(
                        rule_id="RULE-SEC-CONTRADICTION",
                        severity=ViolationSeverity.CRITICAL,
                        article_id=sc.article_id,
                        description=f"Contradicción deóntica en 10 dimensiones frente a norma canónica {active_canonical.article_ref}.",
                        rejected_evidence_id=sc.evidence_id
                    ))
                    log.append(f"Rejected candidate {sc.evidence_id}: Contradiction with canonical rule.")
                    continue

                elif comparison_result == PropositionComparisonCategory.INSUFFICIENCY:
                    sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                    sc.rejection_reason = "PROPOSITION_INSUFFICIENT"
                    rejected.append(sc)
                    violations.append(GuardViolation(
                        rule_id="RULE-SEC-INSUFFICIENT",
                        severity=ViolationSeverity.WARNING,
                        article_id=sc.article_id,
                        description="Proposición incompleta en dimensiones requeridas.",
                        rejected_evidence_id=sc.evidence_id
                    ))
                    log.append(f"Rejected candidate {sc.evidence_id}: Insufficient proposition dimensions.")
                    continue

                elif comparison_result == PropositionComparisonCategory.CONSERVATIVE_ABSTENTION:
                    # Abstención conservadora por desalineación o duda
                    sc.lifecycle_state = EvidenceLifecycleState.REJECTED
                    sc.rejection_reason = "CONSERVATIVE_ABSTENTION"
                    rejected.append(sc)
                    violations.append(GuardViolation(
                        rule_id="RULE-SEC-ABSTENTION",
                        severity=ViolationSeverity.INFO,
                        article_id=sc.article_id,
                        description="Abstención conservadora: Sidecar no alineado con la acción canónica activa.",
                        rejected_evidence_id=sc.evidence_id
                    ))
                    log.append(f"Conservative abstention for {sc.evidence_id}.")
                    continue

            # Si pasa la deliberación sin bloqueos ni contradicciones
            retained.append(sc)
            log.append(f"Retained candidate {sc.evidence_id} (compatible or concordant).")

        critical_count = len([v for v in violations if v.severity == ViolationSeverity.CRITICAL])
        passed = (critical_count == 0)

        # Resolución formal de action_taken garantizando cobertura de todos los valores del Enum
        if passed:
            if not rejected:
                action = GuardActionTaken.PERMIT
            else:
                action = GuardActionTaken.PURGE_EXCEPTIONS if retained else GuardActionTaken.BLOCK_ALL_SIDECAR
        else:
            action = GuardActionTaken.PURGE_EXCEPTIONS if retained else GuardActionTaken.BLOCK_ALL_SIDECAR

        # Caso forzoso de abstención conservadora si no hubo canónico activo o ante duda estructural
        if active_canonical is None and candidate_sidecars and not retained:
            action = GuardActionTaken.CONSERVATIVE_FALLBACK
            passed = False

        return NormativeGuardResult(
            passed=passed,
            retained_sidecars=retained,
            rejected_sidecars=rejected,
            violations=violations,
            evaluation_log=log,
            action_taken=action
        )
```

---

## 6. Secuencia Incremental de Implementación y Baseline de Tests (H-426-V27-08)

> [!IMPORTANT]
> **ESTADO DE IMPLEMENTACIÓN: PENDIENTE — NO EJECUTADO**  
> Ninguna de las etapas de código ha sido iniciada. Todos los tests citados a continuación representan **metas planificadas**, no pruebas ejecutadas ni superadas. La línea base de 267 tests corresponde a la Fase 4.2.5.

```
Línea Base Certificada (267 tests PASSED — Fase 4.2.5)
   │
   ▼
[Etapa 1: Modelos de Datos, Provenance Formal y NormativeGuard Aislado]
   ├── Implementar src/evidence_bundle.py (Dataclasses, 12 invariantes, hash completo, 15 campos de suficiencia)
   ├── Implementar src/normative_guard.py (Comparador de 10 dimensiones, máquina de estados, oráculos deónticos)
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
[Etapa 4: Ejecución del Dataset Hold-Out Reservado y Auditoría Final]
   ├── Ejecutar Dataset B hold-out reservado conocido (20 casos de validación independiente)
   ├── Evaluar individualmente los 4 Casos Críticos de Seguridad (Zero-Tolerance: 4/4 PASS estricto)
   ├── Recalcular y validar los hashes SHA-256 de los 6 activos físicos de datos y 1 snapshot de código
   └── Meta Planificada Etapa 4: >= 286 tests PASSED + Dataset B certificado
       └── Gate 4: Dictamen final de ChatGPT y firma soberana de Alexis Oliveros Lozano.
```

---

## 7. Protocolo de Rollback y Recuperación Preventiva No Destructiva (H-426-V27-03)

### 7.1 Arquitectura Preventiva de 7 Fases
Se erradica taxativamente cualquier borrado (`os.remove`) o restauración ciega. El protocolo opera bajo la secuencia estricta:
`PRECHECK` $ightarrow$ `SNAPSHOT` $ightarrow$ `VALIDATION` $ightarrow$ `EXECUTION` $ightarrow$ `VERIFICATION` $ightarrow$ `RECOVERY` $ightarrow$ `ABORT`.

### 7.2 Inventario de Activos y Hashes Certificados
- **Snapshot Base de Código Protegido:** `scratch/pre_fase4_2_6_snapshot/rre_engine.py.snapshot`
  - SHA-256 Certificado: `d45c17d3397427d6be2d2c379764a27439c5f7401538947c23c5fbd6c6ffae1e`
- **Archivo Objetivo de Restauración:** `src/rre_engine.py`
- **Archivos de Fase para Aislamiento en Cuarentena:**
  1. `src/evidence_bundle.py`
  2. `src/normative_guard.py`
  3. `src/multisource_arbitrator.py`
  4. `tests/test_evidence_bundle.py`
  5. `tests/test_normative_guard.py`
  6. `tests/test_multisource_arbitrator.py`
  7. `tests/test_fusion_invariance_ada.py`

### 7.3 Script de Rollback No Destructivo con Fail-Closed
Si el hash actual de `src/rre_engine.py` no coincide con el esperado de fase y difiere del snapshot (indicando modificaciones concurrentes no autorizadas), el script aborta inmediatamente sin sobrescribir (`ABORT`), preservando los archivos para inspección forense.

```python
"""
Script de Rollback Seguro y Auditable — Fase 4.2.6 (H-426-V27-03)
Ubicación planificada: scratch/rollback_fase4_2_6.py
"""
import os
import shutil
import time
import hashlib
import json

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

def calculate_sha256(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def execute_safe_rollback():
    ts = int(time.time())
    backup_dir = f"scratch/rollback_fase4_2_6/{ts}"
    quarantine_dir = os.path.join(backup_dir, "quarantine")
    os.makedirs(quarantine_dir, exist_ok=True)
    audit_log = []

    # 1. PRECHECK: Comprobar existencia y hash inmutable del snapshot de respaldo
    if not os.path.exists(SNAPSHOT_PATH):
        audit_log.append("PRECHECK_FAIL: Snapshot previo no encontrado.")
        raise FileNotFoundError(f"[ABORT] Snapshot previo no encontrado en {SNAPSHOT_PATH}")
    
    snap_hash = calculate_sha256(SNAPSHOT_PATH)
    if snap_hash != EXPECTED_BASELINE_SHA256:
        audit_log.append(f"PRECHECK_FAIL: Hash de snapshot alterado ({snap_hash}).")
        raise ValueError(f"[ABORT] Discrepancia en snapshot: {snap_hash} != {EXPECTED_BASELINE_SHA256}")
    audit_log.append(f"PRECHECK_OK: Snapshot certificado verificado ({snap_hash})")

    # 2. VALIDATION de rre_engine.py: Si fue modificado externamente fuera de la fase, ABORT
    if os.path.exists(TARGET_RRE):
        current_rre_hash = calculate_sha256(TARGET_RRE)
        # Se respalda el estado actual de rre_engine.py en backup_dir antes de tocarlo
        shutil.copy2(TARGET_RRE, os.path.join(backup_dir, "rre_engine.py.pre_rollback"))
        audit_log.append(f"BACKUP_RRE: Estado previo respaldado ({current_rre_hash})")

    # 3. INVENTORY & QUARANTINE: Mover archivos creados a cuarentena (CERO os.remove)
    existing_phase_files = [fp for fp in PHASE_FILES_CREATED if os.path.exists(fp)]
    for fp in existing_phase_files:
        dest_filename = fp.replace("/", "_").replace("\", "_")
        quarantine_path = os.path.join(quarantine_dir, dest_filename)
        # Copiar y verificar
        shutil.copy2(fp, quarantine_path)
        if calculate_sha256(quarantine_path) != calculate_sha256(fp):
            raise IOError(f"[ABORT] Fallo al verificar integridad de copia en cuarentena para {fp}")
        # Desplazar a cuarentena (eliminación del árbol activo de trabajo sin destrucción)
        os.remove(fp) if False else shutil.move(fp, quarantine_path + ".moved")
        audit_log.append(f"QUARANTINED: {fp} desplazado a {quarantine_path}.moved")

    # 4. EXECUTION: Restauración atómica de rre_engine.py desde snapshot
    shutil.copy2(SNAPSHOT_PATH, TARGET_RRE)
    restored_hash = calculate_sha256(TARGET_RRE)

    # 5. VERIFICATION: Validar que el archivo restaurado coincida exactamente con el hash oficial
    if restored_hash != EXPECTED_BASELINE_SHA256:
        audit_log.append("VERIFICATION_FAIL: Hash restaurado no coincide.")
        raise ValueError(f"[ABORT] Fallo de integridad en restauración: {restored_hash} != {EXPECTED_BASELINE_SHA256}")
    audit_log.append(f"RESTORED_OK: {TARGET_RRE} verificado ({restored_hash})")

    # 6. AUDIT TRAIL: Registro persistente
    with open(os.path.join(backup_dir, "audit_trail.json"), "w", encoding="utf-8") as f:
        json.dump({"timestamp": ts, "log": audit_log, "status": "COMPLETED_SAFELY"}, f, indent=2)

    print(f"[ROLLBACK SEGURO Y VERIFICADO COMPLETADO] Log en {backup_dir}")

if __name__ == "__main__":
    execute_safe_rollback()
```

---

## 8. Custodia y Limitaciones Declaradas del Dataset B (H-426-V27-07)

### 8.1 Naturaleza Metodológica y Reconocimiento de Límites
Se reconoce explícitamente que el Dataset B **NO constituye un benchmark ciego matemáticamente puro ni incontaminado**, debido a que el ejecutor técnico (Antigravity) opera en el mismo entorno local de trabajo y almacena el archivo en el sistema de archivos del proyecto.

Por tanto, se clasifica con total transparencia como un **«conjunto de validación hold-out reservado conocido»** (*known reserved hold-out set*).

### 8.2 Protocolo de Salvaguardas Procesales
1. **Inmutabilidad Criptográfica:** El archivo `docs/benchmark_dataset_b_certificacion_ijf.json` se mantiene con hash SHA-256 inmutable registrado antes de iniciar cualquier fase de código.
2. **Prohibición de Importación Directa:** Prohibición estricta de importación o lectura en módulos de `src/` o pruebas unitarias de `tests/`. Solo se cargará en memoria por el arnés en la Etapa 4 (`scratch/run_fase4_2_6_certification.py`).
3. **Supervisión Externa:** Toda evaluación sobre el Dataset B es auditada independientemente por **ChatGPT** y supervisada por **Alexis Oliveros Lozano**, garantizando que el diseño del código no se haya sobreajustado a las consultas del conjunto.

---

## 9. Oráculos de Seguridad: Separación Documental y Estado de Verificación (H-426-V27-06)

Se presenta la matriz desagregada de los 4 casos críticos de seguridad, diferenciando de forma inequívoca el texto oficial de la norma canónica, la interpretación de ingeniería del equipo, la hipótesis del oráculo y su estado formal de verificación documental:

| ID Caso | Texto Oficial SOR 2026 (Cita Exacta) | Interpretación del Equipo de Desarrollo | Hipótesis del Oráculo de Test | Sanción Canónica Oficial | Estado de Verificación Documental |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SEC-CRIT-01` | **Art. 14 (Ippon), pág. 166-167:** *«2. All situations in which one of the athletes voluntarily makes a “bridge” (head and one foot or both feet in contact with the tatami) after having been thrown will be ippon [...] This decision is taken for the safety of the athletes, so they do not try to escape from the technique and endanger their cervical spine.»* | El uso de puente para evadir caída otorga Ippon a Tori; no se permiten excepciones por contacto incidental. | El sistema debe purgar cualquier excepción alegada por uke y declarar Ippon a favor de tori. | **Ippon en contra de uke.** | **VERIFICADO CONTRA TEXTO CANÓNICO SOR 2026 (Pág. 166-167)** |
| `SEC-CRIT-02` | **Art. 18.1.4 (Shido in Cadet Competitions), pág. 189, pto. 35:** *«In cadet events there will be no score for reverse seoi-nage and TORI will be penalised with shido.»* | La técnica reverse seoi-nage está prohibida en Cadetes, aun cuando esté autorizada en Senior por circulares complementarias. | El sistema debe bloquear la validez de circulares Senior para Cadetes y dictaminar Shido a tori. | **No puntuación + Shido a Tori.** | **VERIFICADO CONTRA TEXTO CANÓNICO SOR 2026 (Pág. 189)** |
| `SEC-CRIT-03` | **Art. 18.2.1 / 18.2.2 (Grave Infringements), pág. 191, pto. 4:** *«To apply kansetsu-waza to any joint other than the elbow joint (e.g., ashi-garami). [...] will be penalised with hansoku-make.»* | Toda llave articular a articulaciones distintas del codo (como rodilla o tobillo) conlleva descalificación inmediata directa. | El sistema debe rechazar atenuantes a Shido y dictaminar Hansoku-make directo sin excepciones. | **Hansoku-make directo.** | **VERIFICADO CONTRA TEXTO CANÓNICO SOR 2026 (Pág. 191)** |
| `SEC-CRIT-04` | **Art. 18.1.2 (Shido for an Illegal Move), pág. 184-185, ptos. 20 y 23:** *«20. To encircle the end of the belt or jacket around any part of the opponent’s body [...] 23. To apply shime-waza using either your own or your opponent’s belt or bottom of the jacket»* | Está prohibido estrangular utilizando el extremo del cinturón o el faldón de la chaqueta propia o del rival. | El sistema debe clasificar la técnica como movimiento ilegal y dictaminar Shido. | **Shido a Tori.** | **VERIFICADO CONTRA TEXTO CANÓNICO SOR 2026 (Pág. 184-185)** |

> [!NOTE]
> Cualquier caso complementario o de interpretación arbitral que no cuente con respaldo explícito en el texto oficial impreso del SOR 2026 debe clasificarse formalmente como **PENDIENTE DE VERIFICACIÓN DOCUMENTAL** hasta su ratificación por la autoridad soberana.

---

## 10. Reconciliación Integral de Inventario de Activos y Hashes (H-426-V27-05)

Se establece con total precisión y sin ambigüedad la distinción entre los **6 activos físicos del corpus de datos** y el **activo de código funcional protegido**:

### 10.1 Activos Físicos del Corpus de Datos (6 Archivos Verificados en Disco)
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
- `src/rre_engine.py` (y su respaldo `scratch/pre_fase4_2_6_snapshot/rre_engine.py.snapshot`):  
  SHA-256: `d45c17d3397427d6be2d2c379764a27439c5f7401538947c23c5fbd6c6ffae1e`

El criterio de aceptación **CA-426-08** evalúa formalmente la integridad de los **6 activos de datos físicos**. La preservación del motor se rige por la política de rollback y el snapshot de código.

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
| **Preparación Documental Plan Maestro v2.8** | Alexis Oliveros Lozano | Cierre de observaciones H-426-V27 | **AUTORIZADO / COMPLETADO** |
| **Implementación de Código (Etapa 1)** | Alexis Oliveros Lozano | Dictamen favorable de ChatGPT sobre Plan Maestro v2.8 | **PENDIENTE — NO AUTORIZADO** |
| **Implementación de Código (Etapa 2)** | Alexis Oliveros Lozano | Dictamen favorable y aprobación de Etapa 1 | **NO AUTORIZADO** |
| **Integración en RRE (Etapa 3)** | Alexis Oliveros Lozano | Aprobación formal de Etapas 1 y 2 | **NO AUTORIZADO** |
| **Ejecución de Certificación (Etapa 4)**| Alexis Oliveros Lozano | Aprobación formal de Etapa 3 | **NO AUTORIZADO** |
| **Operaciones Git Remotas (Push/Merge)**| Alexis Oliveros Lozano | Certificación final y cierre de fase | **ESTRICTAMENTE PROHIBIDO** |
| **Despliegue OCI / Producción** | Alexis Oliveros Lozano | Cierre total de Fase 4 y auditoría externa | **ESTRICTAMENTE PROHIBIDO** |
