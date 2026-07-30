import logging
import os

class ToolContext:
    """Contexto de ejecución unificado que reciben las herramientas"""
    def __init__(self, request_id: str, session_id: str, logger: logging.Logger, config: dict, workspace: str):
        self.request_id = request_id
        self.session_id = session_id
        self.logger = logger
        self.config = config
        self.workspace = workspace

class BaseTool:
    """Clase abstracta base para todas las herramientas del laboratorio"""
    def get_schema(self) -> dict:
        raise NotImplementedError
    def execute(self, context: ToolContext, arguments: dict) -> dict:
        raise NotImplementedError

class ToolRegistry:
    """Gestor dinámico de herramientas aislado del protocolo"""
    def __init__(self):
        self._tools = {}

    def register(self, name: str, tool_instance: BaseTool):
        self._tools[name] = tool_instance

    def find(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def list_tools(self) -> list:
        return [tool.get_schema() for tool in self._tools.values()]

# --- IMPLEMENTACIÓN DE LA FASE 1: ECHO TOOL ---
class EchoTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "echo",
            "description": "Herramienta de diagnóstico que devuelve el texto enviado.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> dict:
        # Validación básica del esquema requerida
        if "text" not in arguments:
            raise ValueError("Parámetro requerido 'text' ausente.")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": arguments["text"]
                }
            ]
        }

# Instancia global del registro listada para el servidor
registry = ToolRegistry()
registry.register("echo", EchoTool())
