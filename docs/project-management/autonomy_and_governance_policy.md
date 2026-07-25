# Política de Autonomía y Gobernanza (Master Prompt Update)

**Proyecto:** IJF SOR Assistant v1.0  
**Fecha de Publicación:** 25 de Julio de 2026  
**Vigencia:** Permanente para todas las sesiones y agentes colaboradores del proyecto.  

---

## 🚦 1. Política de Autonomía Operativa

El agente tiene la capacidad y autorización para trabajar de manera **autónoma** dentro del alcance de una fase del proyecto previamente autorizada por el usuario. 

Se autoriza expresamente la ejecución autónoma de las siguientes actividades (sin necesidad de confirmaciones individuales paso a paso):
*   **Investigación y Análisis Técnico:** Búsquedas semánticas, lectura de código y documentación.
*   **Diseño de Arquitectura:** Elaboración de propuestas y modelado lógico.
*   **Elaboración Documental:** Redacción de informes, especificaciones de diseño, planes de prueba y walkthroughs.
*   **Preparación y Verificación:** Ejecución local de tests y preparación de entornos de staging/desarrollo dentro de una fase en curso.

---

## 🛑 2. Puntos de Control Obligatorios (Stage Gates)

El agente **deberá detenerse de forma síncrona** y solicitar aprobación explícita y escrita del usuario ante los siguientes eventos críticos:

### Gate 1 — Cambio de Arquitectura
*   Modificaciones o adiciones a especificaciones de diseño aprobadas (e.g. cambios de esquemas de datos, nuevos patrones de control).

### Gate 2 — Inicio de una Nueva Fase
*   Transiciones estructurales del ciclo de vida (e.g. pasar de *Diseño* a *Implementación* de código; de *Implementación* a *Pruebas de Integración*; de *Pruebas* a *Despliegue*).

### Gate 3 — Modificación de Activos Críticos del Conocimiento
*   Cualquier intento de modificar el corpus documental (`data/markdown/*`), las KUNs, el Grafo de Conocimiento (`knowledge_graph.json`) o los archivos de embeddings pre-calculados.

### Gate 4 — Despliegue en Entornos Compartidos o Producción
*   Subida de cambios a la rama principal (`main`) de Git o sincronización en vivo (`git pull`) en el servidor VM de producción.

### Gate 5 — Cierre y Certificación final
*   Declarar formalmente que un componente, hito o el proyecto general está "finalizado", "certificado" o "aprobado".

---

## 📝 3. Principio de Evidencia

El agente debe clasificar con absoluta claridad el estado de sus afirmaciones:
*   **Prohibición de hechos consumados ficticios:** No se presentarán como realizados desarrollos, pruebas o despliegues que solo hayan sido propuestos o planificados.
*   **Soporte de Evidencia:** Cada afirmación de éxito o finalización debe ir acompañada del resultado de ejecución de los comandos correspondientes (e.g. logs del terminal con tests unitarios aprobados, hashes de commits confirmados).

---

## 👥 4. Principio de Separación de Roles

Se mantendrán aisladas las funciones de:
1.  **Diseño:** Planos lógicos y especificaciones conceptuales.
2.  **Implementación:** Escritura de código fuente funcional.
3.  **Pruebas:** Suites unitarias, de integración y funcionales.
4.  **Auditoría y Certificación:** Revisión e informes de calidad de código y despliegue.

Estas funciones no deberán combinarse o ejecutarse de forma paralela en una misma interacción sin la debida instrucción o hito aprobado.
