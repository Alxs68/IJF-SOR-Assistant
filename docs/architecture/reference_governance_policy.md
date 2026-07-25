# Política de Gobernanza de Referencias (Reference Governance Policy)

**Proyecto:** IJF SOR Assistant v1.0  
**Foco:** Normas de Gobernanza del Conocimiento y Mantenimiento de Fuentes Externas  
**Fecha:** 25 de Julio de 2026  

---

## 👥 1. Roles y Responsabilidades

Para asegurar la integridad del conocimiento y prevenir la degradación de los enlaces a lo largo del tiempo, se establecen los siguientes roles específicos de gobernanza:

### A. Data-Steward (Custodio de Datos)
*   **Responsabilidad:** Mantener y validar la base de datos de referencias operativas (`data/references/reference_registry.json`).
*   **Acciones:** Modificar URLs resueltas, corregir estados operativos de las referencias, analizar reportes de enlaces rotos y dar de alta nuevos recursos.

### B. Product Owner (PO - Alexis)
*   **Responsabilidad:** Aprobación definitiva de cambios en la base de conocimiento y reclasificaciones manuales.
*   **Acciones:** Autorizar la adición de nuevos documentos maestros, aprobar la migración definitiva de fuentes históricas y decidir políticas de UX ante recursos eliminados por la IJF.

### C. Auditor Técnico (Developer/QA)
*   **Responsabilidad:** Mantenimiento y optimización de los resolvedores y herramientas automáticas de chequeo.
*   **Acciones:** Mantener el script del Checker de background, optimizar el resolvedor de URLs y auditar la compatibilidad técnica del RRM.

---

## ⏱️ 2. Periodicidad y Flujo de Verificación

Para garantizar que el catálogo maestro se mantenga actualizado frente a las modificaciones que realiza la IJF en su web oficial:

1.  **Chequeo Automático Semanal:**
    El script verificador (`Reference Checker`) se ejecutará de forma programada una vez por semana. Analizará la disponibilidad HTTP de los servidores de la IJF y de YouTube, y marcará el `verification_status` como `AUTO_VERIFIED` si responde con 200 OK, o levantará una alerta si encuentra fallos.
2.  **Auditoría Manual Trimestral:**
    El Data-Steward realizará una revisión visual manual de los enlaces marcados como `MANUAL_REVIEW` o `DELETED` cada tres meses, o ante el inicio de un nuevo ciclo competitivo/reglamentario de la IJF (como la transición pre-olímpica o pre-congreso).

---

## 🚨 3. Criterios para Declarar Estados de Referencias

*   **Paso a `DELETED`:**
    Un recurso se clasificará técnicamente como `DELETED` si y solo si:
    *   El servidor responde de forma definitiva con un código de estado `404 Not Found`.
    *   El HTML del video de YouTube contiene de forma consistente indicadores de playability nula (privado, borrado, cancelado) durante **3 chequeos semanales consecutivos** (para evitar falsos positivos por caídas temporales de red).
*   **Paso a `MIGRATED`:**
    Se declarará un recurso como `MIGRATED` cuando la IJF modifique la ruta o el dominio de hospedaje del archivo original (ej. traspaso de Rackcdn a un servidor propio de la IJF), pero el contenido de la regla siga siendo idéntico. Se actualizará el campo `url_resolved` manteniendo la `url_original` para la trazabilidad histórica.

---

## 📥 4. Procedimiento para Registrar Nuevas Referencias

Cuando se incorporen nuevas KUNs al corpus que requieran referencias externas:

1.  **Ingreso en el Registro:** El Data-Steward añadirá la entrada correspondiente en `reference_registry.json` con `version: "1.0"` y el estado inicial `verification_status: "NOT_VERIFIED"`.
2.  **Verificación Inicial:** Se ejecutará el script checker localmente para validar que la URL sea accesible y responder con éxito.
3.  **Confirmación y Commit:** Una vez validado (paso a `VERIFIED`), se guardará el cambio en el repositorio mediante un commit semántico del tipo:
    `chore: register new reference resource for DOC-005`

---

## 💾 5. Preservación de la Evidencia Histórica

Para proteger la integridad de las auditorías de RAG y el entrenamiento de los modelos:
*   **Inmutabilidad del Corpus:** Las KUNs almacenadas en la base de conocimiento original (`data/markdown/`) y el Grafo de Conocimiento (`knowledge_graph.json`) son **evidencia histórica inmutable**. Bajo ninguna circunstancia se modificarán sus metadatos internos de `fuente_origen` o `referencia_especifica` para corregir enlaces caídos en producción.
*   **Desacoplamiento Operativo:** Todas las redirecciones, actualizaciones de URLs activas y reportes de disponibilidad se realizarán **exclusivamente dentro de la base de datos de referencias operativas (`reference_registry.json`)** mediante el RRM. Esto permite auditar la procedencia histórica de cualquier regla tal como fue redactada originalmente, al mismo tiempo que se le ofrece al usuario un enlace funcional en tiempo real.
