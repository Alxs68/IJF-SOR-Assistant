# Contexto Arquitectónico Central - Framework MCP (ALXOL)

> **Línea Base Oficial:** v1.3.0 (Fase 3 Completada)
> **Última Actualización:** Julio 2026

Este documento sirve como la **Fuente de Verdad (Contexto Unificado)** para sincronizar a cualquier IA o Director Técnico (CTO) sobre el estado actual, reglas y arquitectura del Servidor MCP construido localmente.

---

## 1. Metodología de Desarrollo Institucionalizada
El desarrollo del framework avanza estrictamente mediante el siguiente patrón de 5 pasos:
1. **Arquitectura:** Diseño de propuestas técnicas sin escribir código.
2. **Contratos:** Definición formal de entradas, salidas y reglas de interacción.
3. **Implementación:** Codificación pura basada en los contratos aprobados.
4. **Auditoría:** Pruebas funcionales y de seguridad estrictas obligatorias.
5. **Consolidación:** Subida a GitHub y marcado inmutable de la versión (Git Tag).

---

## 2. Topología del Proyecto y Capas Puras
Todo el código del servidor se encuentra asilado en la ruta `src/mcp/`. No utiliza dependencias externas (FastMCP descartado), ni `asyncio`, sino que implementa JSON-RPC 2.0 síncrono sobre `stdio`.

```text
src/mcp/
├── config.py                 # Constantes globales, límites y allowlists
├── mcp_server.py             # Entrypoint unificado (Inyección de dependencias)
├── core/
│   ├── logger.py             # Logs estructurados hacia stderr
│   ├── transport.py          # Canal síncrono bloqueante (sys.stdin / stdout)
│   ├── protocol.py           # Enrutador JSON-RPC (Capa de Intercambio)
│   └── registry.py           # Gestor en memoria y definición de ToolContext
└── tools/
    ├── filesystem.py         # [Fase 2] Herramientas Read-Only locales
    └── git_ops.py            # [Fase 3] Herramientas Read-Only de historial
```

---

## 3. Contratos Internos (Contract-Version: 1.2.1)
El corazón de la integración exige separación de responsabilidades:
*   **Las herramientas NO serializan a JSON.** Toda herramienta (hija de `BaseTool`) debe retornar en su método `execute()` una estructura de datos nativa (ej. `dict` o `list`).
*   **La Capa de Adaptación:** El archivo `core/protocol.py` es el único responsable de tomar ese diccionario nativo, inyectarlo en el array `content` de MCP (`{"type": "text", "text": ...}`) y ejecutar el `json.dumps()` final para enviar a `stdout`.
*   **Encapsulamiento del Entorno:** Las herramientas no usan variables globales. Reciben un `ToolContext` que provee el `workspace` absoluto que actúa como ancla de seguridad, junto al `logger` y un identificador de trazabilidad.

---

## 4. Capacidades Actuales y Seguridad Blindada

### Fase 1: Core MCP (v1.0)
*   Soporte para los flujos JSON-RPC obligatorios: `initialize`, `notifications/initialized`, `tools/list`, `tools/call`.

### Fase 2: Filesystem Read-Only (v1.2.1)
*   **Herramientas:** `fs_exists`, `fs_list_directory`, `fs_read_file`, `fs_get_metadata`.
*   **Seguridad:** 
    *   **Path Traversal:** Imposible. Se validan prefijos absolutos usando `os.path.commonpath` contrastado contra el `ToolContext.workspace`.
    *   **Allowlist Estricta:** `fs_read_file` solo lee extensiones autorizadas (txt, md, py, json, etc.). Archivos extraños (como `.pdf` o `.exe`) se bloquean.
    *   **Tope de Memoria:** Archivos que superan el límite (1MB) no se procesan, salvaguardando la memoria de transporte.

### Fase 3: Git Ops Read-Only (v1.3.0)
*   **Herramientas:** `git_status`, `git_log`, `git_show`, `git_diff`.
*   **Seguridad:**
    *   **Command Injection:** Imposible. No se usa `shell=True`. Se utilizan arrays estrictos de argumentos en `subprocess.run()`.
    *   **Sanitización:** Argumentos como el Hash del commit en `git_show` se validan con expresiones regulares `r"^[a-fA-F0-9]{4,40}$"` para evitar comandos maliciosos como `HEAD; rm -rf *`.
    *   **Confinamiento:** Subprocesos forzados a ejecutarse usando `cwd=ToolContext.workspace`.

---

## 5. Próximos Pasos en el Mapa de Ruta (Roadmap)
*   **Fase 4 (SQL Ops Read-Only):** Exploración de bases de datos relacionales locales (SQLite/PostgreSQL) para dotar al modelo de contexto sobre datos estructurados.
*   **Fase 5 (Pipeline Orquestador):** Poner a trabajar el servidor MCP en tareas tangibles (ej. proveerle un batch de KUNs JSON al LLM para actualizarlas contra una API).
