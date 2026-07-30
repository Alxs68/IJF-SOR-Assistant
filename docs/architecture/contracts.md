# Manifiesto de Arquitectura MCP: Contratos de Integración

## Contract-Version: 1.2

Este documento formaliza el contrato interno entre las capas del servidor MCP y las herramientas delegadas.

### 1. Interfaz Base (`BaseTool`)
Todas las herramientas implementadas para el servidor MCP deben heredar de `BaseTool` e implementar:

- `get_schema(self) -> dict`: Define el esquema JSON válido de la herramienta, incluyendo sus parámetros y descripciones de acuerdo a la especificación estándar JSON-RPC de MCP.
- `execute(self, context: ToolContext, arguments: dict) -> dict | list`: Método sincrónico que contiene la lógica core. **Importante:** A partir de la versión 1.2.1, este método debe retornar estructuras de datos puras de Python (`dict` o `list`). La serialización final para el transporte es responsabilidad de la Capa de Protocolo.

### 2. Contexto de Ejecución (`ToolContext`)
Para garantizar un encapsulamiento completo de dependencias, las herramientas no deben acceder a variables globales del servidor. Todo estado y configuración debe inyectarse a través del objeto `ToolContext`:

- `request_id (str)`: Identificador único de la petición (trazabilidad).
- `session_id (str)`: Identificador de la sesión del ciclo de vida del cliente.
- `logger (logging.Logger)`: Instancia del logger configurado (flujo hacia `stderr`).
- `config (dict)`: Diccionario con configuraciones inyectadas.
- `workspace (str)`: Ruta absoluta del directorio raíz que sirve como *sandbox* para herramientas con operaciones de entrada y salida (prevención de Path Traversal).

---
*Aprobado por: Dirección Técnica - 30/07/2026*
