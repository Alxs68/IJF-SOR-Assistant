import os
import sys
import json

# Ajustar PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "mcp")))
import config
from core.protocol import MCPProtocolHandler
from core.registry import registry
from tools.filesystem import FsExistsTool, ListDirectoryTool, ReadFileTool, GetMetadataTool

def run_tests():
    print("=== INICIANDO SUITE DE PRUEBAS LOCAL V1.2.1-OFICIAL ===")
    
    # 1. Registrar herramientas manualmente para la prueba (simulando mcp_server.py)
    registry.register("fs_exists", FsExistsTool())
    registry.register("fs_list_directory", ListDirectoryTool())
    registry.register("fs_read_file", ReadFileTool())
    registry.register("fs_get_metadata", GetMetadataTool())
    print("[OK] Herramientas registradas en registry.")
    
    protocol = MCPProtocolHandler()
    
    # 2. Flujo de inicialización
    req_init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    resp_init = protocol.handle_line(json.dumps(req_init))
    assert "2024-11-05" in resp_init, "Protocol version no coincide"
    assert "1.2.1" in resp_init, "Server version no coincide"
    print("[OK] Handshake 'initialize' procesado.")
    
    req_initialized = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    resp_initialized = protocol.handle_line(json.dumps(req_initialized))
    assert resp_initialized is None, "Notificación initialized debe retornar None"
    print("[OK] Handshake 'initialized' procesado.")
    
    # 3. tools/list
    req_list = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    resp_list = json.loads(protocol.handle_line(json.dumps(req_list)))
    tools = resp_list["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "fs_exists" in tool_names
    assert "fs_list_directory" in tool_names
    assert "fs_read_file" in tool_names
    assert "fs_get_metadata" in tool_names
    print("[OK] tools/list validado.")
    
    # 4. tools/call - fs_exists
    req_call1 = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "fs_exists", "arguments": {"path": "."}}}
    resp_call1 = json.loads(protocol.handle_line(json.dumps(req_call1)))
    content_raw = resp_call1["result"]["content"][0]["text"]
    assert "true" in content_raw.lower(), "fs_exists debe retornar true para '.'"
    print("[OK] fs_exists ejecutada exitosamente.")
    
    # 5. Path Traversal Protection
    req_traversal = {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "fs_exists", "arguments": {"path": "../../../../../etc/passwd"}}}
    resp_traversal = json.loads(protocol.handle_line(json.dumps(req_traversal)))
    # MCP Protocol returns isError=False but the text has the error if we catch it inside the adapter? 
    # Wait, the protocol adapter sets isError=False for internal dict payload. BUT if the tool raises ValueError, the protocol catches it and returns JSON-RPC error.
    assert "error" in resp_traversal, "El ataque de path traversal no fue bloqueado como error JSON-RPC."
    assert "Acceso denegado" in resp_traversal["error"]["message"] or "Invalid params" in resp_traversal["error"]["message"]
    print("[OK] Path Traversal estrictamente bloqueado.")
    
    # 6. Extension Validation Protection
    req_ext = {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "fs_read_file", "arguments": {"path": "C:/PROYECTOS/IJF-SOR-Assistant/data/raw/ijf_sor_2026.pdf"}}}
    # Because workspace is current working directory (os.getcwd()), we need to ensure the test path is relative or absolute inside it.
    # We will just write a dummy PDF file locally in the workspace to test extension validation.
    with open("dummy.pdf", "w") as f: f.write("dummy")
    req_ext = {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "fs_read_file", "arguments": {"path": "dummy.pdf"}}}
    resp_ext = json.loads(protocol.handle_line(json.dumps(req_ext)))
    assert "error" in resp_ext, "La validación de extensión no bloqueó el archivo."
    print("[OK] Violación de Extensión (.pdf) estrictamente bloqueada.")
    os.remove("dummy.pdf")
    
    # 7. tools/call - fs_list_directory (Determinismo)
    req_call2 = {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "fs_list_directory", "arguments": {"path": "."}}}
    resp_call2 = json.loads(protocol.handle_line(json.dumps(req_call2)))
    # just checking it runs
    assert "result" in resp_call2
    print("[OK] fs_list_directory ejecutada.")
    
    print("=== TODOS LOS TESTS PASADOS CON ÉXITO ===")

if __name__ == "__main__":
    run_tests()
