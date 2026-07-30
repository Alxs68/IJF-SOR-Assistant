import json
import os
import sys

# To ensure config can be imported when running mcp_server.py from anywhere
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from core.logger import mcp_logger
from core.registry import registry, ToolContext

class MCPProtocolHandler:
    def __init__(self):
        self.initialized = False
        self.session_id = "SESSION_001"  # Puede ser parametrizado dinámicamente

    def handle_line(self, raw_line: str) -> str:
        """Procesa una línea de texto plano y retorna la respuesta JSON-RPC en string o None"""
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError as e:
            return json.dumps(self._make_error(None, -32700, f"Parse error: {str(e)}"))

        # Validación estructural estricta de JSON-RPC 2.0
        if message.get("jsonrpc") != "2.0":
            return json.dumps(self._make_error(None, -32600, "Invalid Request: Falta campo jsonrpc 2.0"))

        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})

        # Control del ciclo de vida del Handshake
        if not self.initialized and method not in ["initialize", "notifications/initialized"]:
            return json.dumps(self._make_error(msg_id, -32002, "Server Not Initialized"))

        if method == "initialize":
            self.initialized = True
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": config.MCP_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": config.SERVER_NAME, "version": config.SERVER_VERSION}
                }
            })

        elif method == "notifications/initialized":
            mcp_logger.info("Handshake completado. Estado READY.", extra={"session_id": self.session_id, "method": method})
            return None

        elif method == "tools/list":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": registry.list_tools()}
            })

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            tool_instance = registry.find(tool_name)
            if not tool_instance:
                return json.dumps(self._make_error(msg_id, -32601, f"Method not found: Herramienta '{tool_name}' no registrada"))

            # Construcción del contexto de ejecución solicitado
            ctx = ToolContext(
                request_id=str(msg_id),
                session_id=self.session_id,
                logger=mcp_logger,
                config={"server_name": config.SERVER_NAME},
                workspace=os.getcwd()
            )

            # Aislamiento completo de herramientas
            try:
                result_payload = tool_instance.execute(ctx, tool_args)
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result_payload
                })
            except ValueError as val_err:
                return json.dumps(self._make_error(msg_id, -32602, f"Invalid params: {str(val_err)}"))
            except Exception as internal_err:
                mcp_logger.error(f"Fallo crítico en herramienta {tool_name}", extra={"request_id": msg_id, "tool": tool_name, "error": str(internal_err)})
                return json.dumps(self._make_error(msg_id, -32603, f"Internal error: {str(internal_err)}"))

        return json.dumps(self._make_error(msg_id, -32601, f"Method not found: '{method}' desestimado"))

    def _make_error(self, msg_id, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
