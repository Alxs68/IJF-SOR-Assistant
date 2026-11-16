# Documento de Diseño Arquitectónico Final y Preciso — Fase 4.2.6
## Fusión y Arbitraje Multifuente (`EvidenceBundle` & `NormativeGuard`)

**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.6 — Fusión y Arbitraje Multifuente  
**Supervisor:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría:** ChatGPT  
**Diseño Técnico:** Antigravity  
**Fecha:** 2026-11-05 (Revisión v2.2 — Corrección Arquitectónica Final)  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Branch:** `integration/ijf-sor-2026-08-merge`  
**Estado:** **DISEÑO TÉCNICO EXCLUSIVAMENTE DOCUMENTAL — CÓDIGO NO IMPLEMENTADO**

---

## 1. Fundamentos y Principios Rectores Inmutables

1. **Desacoplamiento Estricto entre Precedencia y Calificación:** La jerarquía formal de autoridad no predetermina la admisibilidad de una fuente. Una fuente de alto rango (Tier 1 o Tier 2) debe superar validaciones independientes de vigencia temporal, alcance material (*scope*) y aplicabilidad contextual antes de ser considerada en el arbitraje.
2. **Prevalencia Canónica de Seguridad (*Safety-First Supremacy*):** Ninguna fuente complementaria Sidecar (Tier 2, Tier 3 o contextual) puede crear, ampliar, flexibilizar ni modificar una excepción de seguridad o una penalización imperativa (Ippon, Hansoku-make directo, acciones prohibidas) sin una validación oficial canónica expresa y verificable criptográficamente.
3. **No-Equivalencia entre Empaquetamiento y Suficiencia:** La inclusión de un fragmento dentro del contenedor `EvidenceBundle` no implica su admisibilidad jurídica automática ni garantiza suficiencia probatoria para alterar la respuesta de ADA.
4. **Tolerancia Cero en Seguridad Normativa:** El criterio de aceptación para casos críticos de seguridad y penalizaciones imperativas es de **cero errores (0.0% margen de fallo)**, independientemente del porcentaje de aprobación global del benchmark.
5. **Abstención Conservadora ante Conflictos Irresolubles:** Ante cualquier contradicción no clasificada o conflicto normativo entre fuentes donde no exista una regla de resolución indubitable, el sistema se abstendrá de incorporar la fuente complementaria, manteniendo exclusivamente la norma canónica SOR 2026 o emitiendo abstención explícita.
6. **Invarianza Absoluta de Doble Capa (RRE y ADA):** Preservación de la respuesta primaria del RRE y de la estructura, citas normativas, mandatos, sanciones y excepciones generados por ADA ante consultas canónicas puras y fuera de dominio.

---

## 2. Contrato de Datos Extendido: `EvidenceBundle`

El contrato `EvidenceBundle` se tipifica minuciosamente incorporando las precisiones de vigencia, alcance, gobernanza y suficiencia:

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class AuthorityTier(Enum):
    TIER_1_CANONICAL = "TIER_1_CANONICAL"              # SOR 2026 Oficial del Comité Ejecutivo IJF
    TIER_2_OFFICIAL_AMENDMENT = "TIER_2_OFFICIAL_AMENDMENT"  # Circulares Oficiales del Comité Ejecutivo
    TIER_3_TECHNICAL_INTERPRETATION = "TIER_3_TECHNICAL_INTERPRETATION"  # Seminarios y presentaciones técnicas de arbitraje
    TIER_4_CONTEXTUAL = "TIER_4_CONTEXTUAL"            # Glosarios, notas pedagógicas y contexto histórico

class NormativeValidity(Enum):
    CONFIRMED_CURRENT = "CONFIRMED_CURRENT"          # Vigente y ratificada formalmente con evidencia externa contrastada
    PENDING_VALIDATION = "PENDING_VALIDATION"        # Declarada vigente en manifiesto pero pendiente de contraste oficial
    UNKNOWN = "UNKNOWN"                              # Estado de vigencia no determinable; inadmisible para arbitraje
    SUPERSEDED = "SUPERSEDED"                        # Reemplazada o derogada formalmente por circular posterior
    EXPIRED = "EXPIRED"                              # Plazo temporal o evento de aplicación concluido

class AgeCategory(Enum):
    ALL_AGES = "ALL_AGES"
    SENIOR_ONLY = "SENIOR_ONLY"
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

class EvidenceLifecycleState(Enum):
    RETRIEVED = "RETRIEVED"            # Fragmento recuperado léxica/semánticamente por el motor
    VALIDATED = "VALIDATED"            # Superó integridad criptográfica, vigencia y elegibilidad
    ADMISSIBLE = "ADMISSIBLE"          # Pertinente, dentro de alcance y apto para deliberación
    CONTEXTUAL = "CONTEXTUAL"          # Válido como trasfondo pedagógico, sin valor dispositivo vinculante
    CONTRADICTORY = "CONTRADICTORY"    # En conflicto directo con una norma de mayor jerarquía
    REJECTED = "REJECTED"              # Descartado activamente por violación de seguridad, expiración o ruido

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

@dataclass(frozen=True)
class ProvenanceInfo:
    document_id: str
    authority_tier: AuthorityTier
    validity: NormativeValidity
    scope: ScopeApplicability
    source_url: str
    staging_sha256: str
    official_gazette_reference: Optional[str] = None  # Evidencia documental externa requerida
    page_or_slide: Optional[int] = None
    verification_timestamp: float = 0.0

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
    rejection_reason: Optional[str] = None

@dataclass
class EvidenceBundle:
    bundle_id: str
    query: str
    primary_items: List[EvidenceItem]
    sidecar_items: List[EvidenceItem]
    arbitration_decision: str  # CANONICAL_EXCLUSIVE, HARMONIZED_SUPPLEMENT, OFFICIAL_MODIFICATION, GUARD_REJECTION, CONSERVATIVE_ABSTENTION
    normative_guard_passed: bool
    audit_trail: List[str]
    is_sufficient_for_synthesis: bool = False  # Explicitamente False por defecto
    requires_context_disambiguation: bool = False  # Si la consulta omite edad cuando la regla difiere
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 3. Especificación Precisa de Gobernanza: Vigencia y Alcance

### 3.1 `NormativeValidity`: Criterios Probatorios de Vigencia
Para impedir que una mera declaración textual en el manifiesto JSON equivalga a una validación jurídica oficial, se establecen los siguientes requerimientos probatorios:

1. **`CONFIRMED_CURRENT`:**
   - Exige correlación biunívoca entre el documento en staging y una circular oficial emitida por el Comité Ejecutivo IJF, verificable mediante URL canónica de la IJF y referencia oficial (`official_gazette_reference` o número de circular).
   - El hash criptográfico SHA-256 del archivo físico debe coincidir exactamente con el valor asentado en el inventario inmutable.
   - Solo los fragmentos con `CONFIRMED_CURRENT` pueden ser considerados para modificar o complementar una norma.
2. **`PENDING_VALIDATION`:**
   - Documentos aprobados para ingesta experimental en Fase 4.2.2 pero cuya vigencia no ha sido cotejada con una publicación normativa del Comité Ejecutivo.
   - **Comportamiento:** Se clasifican automáticamente como `CONTEXTUAL` o se descartan si colisionan con el SOR. No pueden generar modificaciones de reglas.
3. **`UNKNOWN`:**
   - Ausencia de fecha, metadatos incompletos o discrepancia en el repositorio. Provoca el rechazo inmediato (`REJECTED`) del fragmento.
4. **`SUPERSEDED` y `EXPIRED`:**
   - Fragmentos derogados o superados por actualizaciones posteriores. Rechazo inmediato (`REJECTED`) con motivo `INVALID_TEMPORAL_VIGENCY`.

### 3.2 `ScopeApplicability`: Tratamiento Riguroso de Contexto de Edad Desconocido

Queda formalmente rectificada la política ante contexto de edad no especificado:

1. **Prohibición de Asunción Automática:**  
   El sistema **NO asumirá automáticamente la categoría de Cadetes** cuando la consulta omita la edad o categoría del competidor (ej. *"¿Está permitido el reverse seoi-nage?"*). Asumir Cadetes arbitrariamente distorsionaría la consulta de un árbitro o competidor Senior.
2. **Protocolo de Presentación Diferenciada o Desambiguación:**  
   Cuando una técnica o regla presente un régimen normativo divergente según la edad:
   - **En modo interactivo / diálogo:** El sistema marcará `requires_context_disambiguation = True` y solicitará explícitamente aclaración al usuario: *"¿Para qué categoría de edad consulta (Senior o Cadete/Junior)?"*.
   - **En modo de respuesta directa (ADA):** El sistema **presentará mandatoriamente ambas condiciones diferenciadas en la misma respuesta**, estructurando:
     - **Categoría Senior:** Regla aplicable (ej. permitido según enmienda oficial ejecutiva).
     - **Categorías Cadetes y Junior:** Regla aplicable (ej. prohibido taxativamente por seguridad deportiva, sancionable con Shido).
3. **Prohibición Absoluta de Extrapolación:**  
   Queda terminantemente prohibido extrapolar una autorización de Senior hacia Cadetes o viceversa. Ninguna enmienda específica de una categoría podrá aplicarse a otra sin mandato normativo explícito.

---

## 4. Arquitectura del `NormativeGuard`: Evaluación Dispositiva y no Bloqueo por Mención

El `NormativeGuard` se refina para evaluar **la decisión normativa generada, sus mandatos, sanciones y excepciones**, erradicando el bloqueo superficial por mera mención léxica:

```mermaid
flowchart TD
    CandidateEvidence["Evidencia Post-Retrieval"] --> Evaluator["NormativeGuard: Evaluador Dispositivo"]
    
    subgraph Guard_Evaluation ["Evaluación de Mandatos, Sanciones y Excepciones"]
        direction TB
        E1["¿Es una Explicación Doctrinal Legítima del Artículo?"] -->|Sí (Cita / Contexto Armónico)| Allow["ADMISSIBLE / CONCORDANT"]
        E1 -->|No| E2["¿El Fragmento Contradice el Mandato o Sanción Canónica?"]
        E2 -->|Sí (Flexibiliza Sanción o Crea Falsa Excepción)| Reject["REJECTED: GUARD_SAFETY_VIOLATION"]
        E2 -->|Duda o Conflicto No Clasificado| Abstain["CONSERVATIVE_ABSTENTION"]
    end
    
    CandidateEvidence --> Guard_Evaluation
    Reject --> PureSOR["Prevalencia Canónica SOR 2026"]
    Abstain --> PureSOR
    Allow --> Bundle["EvidenceBundle Armonizado"]
```

### 4.1 Principio de No-Bloqueo por Mera Mención
- **Diferenciación Doctrinal:** La mera mención en la consulta o en el fragmento de `Art. 14` (caída de espaldas / puente), `Art. 18.2` (Hansoku-make) o `Apéndice C` (judogi) **NO constituirá causal de bloqueo automático**. Un competidor o árbitro tiene derecho a consultar legítimamente: *"¿Qué establece el Artículo 14 sobre la caída sobre la espalda?"* o *"Explique las tolerancias del judogi según el Apéndice C"*.
- **Criterio de Evaluación Dispositiva:** El `NormativeGuard` intervendrá **únicamente cuando el fragmento complementario o la síntesis propuesta intente alterar la disposición normativa**:
  1. **Mandato Imperativo:** Intentar convertir una obligación o prohibición canónica en una acción optativa.
  2. **Sanción:** Intentar rebajar una descalificación directa (Hansoku-make) a una penalización leve (Shido) sin circular oficial de rango constituyente.
  3. **Excepción No Autorizada:** Crear una causa de justificación o excepción de contacto involuntario sobre una infracción de riesgo grave (ej. pretender que el puente voluntario quede impune).
- **Abstención Conservadora ante Conflictos Irresolubles:** Si surge una colisión entre fragmentos cuya relación jurídica no esté contemplada en las reglas tipificadas de arbitraje, el sistema se abstiene de incorporar la fuente complementaria (`CANONICAL_EXCLUSIVE`) para preservar la seguridad jurídica.

---

## 5. Criterios de Suficiencia Probatoria en `EvidenceBundle`

Para que el flag `is_sufficient_for_synthesis` pase a `True`, el bundle debe satisfacer copulativamente los siguientes criterios objetivos:

$$\text{Suficiencia} = (\text{Autoridad Validada}) \land (\text{Vigencia Confirmada}) \land (\text{Alcance Pertinente}) \land (\text{NormativeGuard OK}) \land (\text{Cero Conflictos})$$

1. **Validación de Autoridad y Vigencia:** Toda evidencia incorporada debe tener `authority_tier` reconocido y vigencia `CONFIRMED_CURRENT`.
2. **Pertinencia de Alcance:** El contexto de la consulta debe corresponder con el `ScopeApplicability` de los fragmentos, o contar con la respuesta diferenciada por categoría.
3. **Ausencia de Conflictos Irresolubles:** No debe existir ningún fragmento complementario en estado `CONTRADICTORY` o colisión con normas imperativas.
4. **Prohibición Expresa:** La suficiencia **bajo ninguna circunstancia** podrá determinarse únicamente por la acumulación de score BM25 o por la cantidad de fragmentos recuperados.

---

## 6. Metodología Reproducible de Invarianza ADA: Mandatos, Sanciones y Excepciones

Para evaluar la invarianza entre la línea base y el modo fusionado en consultas canónicas puras y fuera de dominio, se establece una metodología reproducible y verificable:

### 6.1 Matriz de Comparación y Tolerancias Formales

| Dimensión de Invarianza | Tolerancia Exigida | Método de Verificación Reproducible |
| :--- | :--- | :--- |
| **Identificadores de Evidencia (`passage_ids`)** | **0.0% (Igualdad Exacta)** | Diff string a string de listas de IDs. |
| **Artículos Canónicos Citados (`article_id`)** | **0.0% (Igualdad Exacta)** | Coincidencia de conjuntos canónicos citados. |
| **Ordenamiento y Scores Primarios** | **$< 10^{-4}$ (Flotante exacto)** | Mismo orden secuencial y puntuación numérica. |
| **Estado de Abstención (`status`)** | **0.0% (Igualdad Exacta)** | `status == "ABSTAIN"` idéntico en consultas OOD. |
| **Equivalencia Dispositiva de Mandatos** | **100.0% Concordancia** | Extracción automática de la tupla: `(Acción, Sujeto, Obligación/Prohibición)` mediante parser determinista. |
| **Equivalencia de Sanciones** | **100.0% Concordancia** | Extracción y cotejo exacto de la penalización dictada: `{Ippon, Waza-ari, Yuko, Shido, Hansoku-make directo, No sanción}`. |
| **Equivalencia de Excepciones** | **100.0% Concordancia** | Verificación de que no se agregue ninguna excepción condicional ausente en la respuesta baseline. |

### 6.2 Protocolo de Evaluación Reproducible
Se prohíbe declarar "equivalencia semántica" sin respaldo forense. Toda prueba de invarianza de ADA ejecutará el script reproducible `scratch/verify_ada_dispositive_invariance.py` que parseará las respuestas y verificará la identidad de las tuplas normativas.

---

## 7. Arquitectura del Benchmark Independiente de Certificación

Se formaliza la separación conceptual y metodológica de las baterías de prueba:

### 7.1 Dataset A: Benchmark de Validación Inicial (40 Consultas Calibradas)
- Ubicado en `scratch/run_fase4_2_5_benchmark.py`. Evalúa no-regresión de la calibración de Fase 4.2.5.

### 7.2 Dataset B: Benchmark Ciego de Certificación de Seguridad (20 Consultas Hold-Out)
- **Custodia y Separación:** Mantenido bajo custodia independiente, físicamente separado de los tests de ajuste de umbrales.
- **Alcance Metodológico:** Se declara expresamente que **20 consultas constituyen una validación inicial representativa de seguridad, no una certificación matemática exhaustiva** de todos los escenarios del judo mundial.
- **Distribución de Casos (Hold-Out):**
  - **4 Casos Críticos de Seguridad Normativa (Criterio Cero Fallos Obligatorio).**
  - 4 Enmiendas Oficiales Complejas (Tier 2).
  - 4 Interpretaciones Arbitrales en Ne-waza (Tier 3).
  - 4 Consultas Canónicas Puras SOR (Invarianza estricta).
  - 4 Consultas Fuera de Dominio (OOD Ciego).

### 7.3 Casos Críticos de Seguridad Normativa (Evaluación Individualizada y Excluyente)

| ID Caso | Consulta de Seguridad Crítica | Comportamiento Esperado | Condición de Aceptación |
| :--- | :--- | :--- | :--- |
| `SEC-CRIT-01` | Si tori proyecta y uke cae sobre su puente de cuello voluntario para no marcar punto, ¿aplica excepción de contacto involuntario? | Bloqueo de excepción. SOR Art. 14 / Art. 18.2 imperativo (Ippon en contra). | **CERO ERRORES (PASS)** |
| `SEC-CRIT-02` | ¿Puede un competidor cadete ejecutar reverse seoi-nage si asegura agarre cruzado? | Bloqueo de enmienda Senior. Presentación diferenciada o prohibición en Cadetes. | **CERO ERRORES (PASS)** |
| `SEC-CRIT-03` | En ne-waza, ¿es legal aplicar palanca articular sobre la rodilla si la acción inició en pie? | Bloqueo total de cualquier interpretación permisiva. Hansoku-make directo canónico (Art. 18.2). | **CERO ERRORES (PASS)** |
| `SEC-CRIT-04` | ¿Es legal estrangular al oponente utilizando directamente la pretina o faldón del propio cinturón desatado? | Bloqueo total. Infracción canónica estricta por uso indebido de vestimenta (Art. 18.1). | **CERO ERRORES (PASS)** |

> [!CAUTION]
> **REGLA EXCLUYENTE:** Un solo fallo en cualquiera de los 4 casos críticos de seguridad (`SEC-CRIT-01` a `SEC-CRIT-04`) implicará la **REPROBACIÓN AUTOMÁTICA** de la Fase 4.2.6, independientemente de que el resto del benchmark alcance el 100% de éxito.

---

## 8. Declaración de Cumplimiento de Restricciones

> [!IMPORTANT]
> **DECLARACIÓN DE NO INTERVENCIÓN Y AISLAMIENTO:**  
> - El presente documento representa exclusivamente la especificación técnica precisa y rectificada (v2.2).  
> - **NO se ha modificado ninguna línea de código funcional ni del RRE.**  
> - **NO se han modificado corpus, Sidecars, índices, grafos ni bases de datos.**  
> - **NO se han ejecutado commits, push, merge ni despliegues.**  
> - El repositorio se mantiene en estado de **solo lectura**. La implementación de la Fase 4.2.6 requerirá la aprobación y orden expresa de **Alexis Oliveros Lozano**.
