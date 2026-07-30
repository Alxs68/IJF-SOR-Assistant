# Manifiesto de Arquitectura MCP: Contratos de Integración

## Contract-Version: 1.2

Este documento formaliza el contrato interno estricto entre las capas del servidor MCP y las herramientas delegadas.

### 1. Interfaz Base (`BaseTool`)
Todas las herramientas implementadas para el servidor MCP deben heredar de `BaseTool` e implementar obligatoriamente:

- `get_schema(self) -> dict`: Define el esquema JSON válido de la herramienta, incluyendo sus parámetros y descripciones (según la especificación JSON-RPC de MCP).
- `execute(self, context: ToolContext, arguments: dict) -> dict | list`: Método sincrónico con la lógica central. **Regla de Oro (v1.2.1):** Este método debe retornar estrictamente estructuras de datos nativas puras de Python (`dict` o `list`). Bajo ninguna circunstancia la herramienta debe invocar `json.dumps()`. La serialización y encapsulamiento es responsabilidad exclusiva de la Capa de Protocolo.

### 2. Contexto de Ejecución (`ToolContext`)
Todo estado, configuración externa y entorno de confinamiento se inyecta estrictamente mediante el objeto `ToolContext`:

- `request_id (str)`: Identificador único de la petición.
- `session_id (str)`: Identificador de la sesión del ciclo de vida.
- `logger (logging.Logger)`: Instancia del logger configurado (flujo hacia `stderr`).
- `config (dict)`: Diccionario con configuraciones globales inyectadas.
- `workspace (str)`: Ruta absoluta del directorio raíz confinado (*sandbox*). Todo acceso I/O debe resolverse y limitarse dentro de este perímetro para prevención de Path Traversal.

---
*Aprobado por: Dirección Técnica - Línea Base Oficial v1.2.1*
