# Mapa de Ruta del Ecosistema Tecnológico — ALXOL

## 1. Niveles de Abstracción del Ecosistema
El desarrollo de este laboratorio se rige bajo un modelo jerárquico que separa la visión, la metodología, la infraestructura y el producto:

ALXOL (Visión Empresarial)
   └── Laboratorio de IA (Espacio metodológico, estándares y gobernanza)
          └── Framework MCP (Activo tecnológico e infraestructura reutilizable)
                 └── Asistente IJF SOR (Primer producto concreto construido sobre el framework)

## 2. Próximas Capacidades del Framework MCP
Para mantener el Framework MCP como una pieza genérica, modular y desacoplada del dominio específico de cualquier asistente, se planifica la incorporación progresiva de las siguientes capacidades:

- **Fase 3 — Git Ops (Read-Only):** Capacidad del Framework para interactuar con sistemas de control de versiones locales (historial, estados de ramas y diffs) mediante `src/mcp/tools/git_ops.py`. El Asistente IJF SOR será simplemente su primer consumidor.
- **Fase 4 — SQL Ops (Read-Only):** Conector genérico parametrizado para explotación segura de bases de datos relacionales.
- **Fase 5 — OCI Integration:** Capacidad de infraestructura para interactuar de forma segura con los servicios en la nube de Oracle Cloud Infrastructure.
