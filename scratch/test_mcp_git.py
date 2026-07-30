import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "mcp")))
from core.protocol import MCPProtocolHandler
from core.registry import registry
from tools.git_ops import GitStatusTool, GitLogTool, GitShowTool, GitDiffTool

def run_tests():
    print("=== INICIANDO SUITE DE PRUEBAS LOCAL FASE 3 GIT OPS ===")
    
    # 1. Registrar
    registry.register("git_status", GitStatusTool())
    registry.register("git_log", GitLogTool())
    registry.register("git_show", GitShowTool())
    registry.register("git_diff", GitDiffTool())
    print("[OK] Herramientas Git registradas.")
    
    protocol = MCPProtocolHandler()
    protocol.initialized = True
    protocol.session_id = "TEST"
    
    # 2. git_status
    req_status = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "git_status", "arguments": {}}}
    resp_status = json.loads(protocol.handle_line(json.dumps(req_status)))
    assert "error" not in resp_status, f"git_status falló: {resp_status.get('error')}"
    # Validar contrato nativo
    status_content = json.loads(resp_status["result"]["content"][0]["text"])
    assert isinstance(status_content, list), "El contenido debe ser una lista"
    print("[OK] git_status validado exitosamente.")
    
    # 3. git_log
    req_log = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "git_log", "arguments": {"count": 3}}}
    resp_log = json.loads(protocol.handle_line(json.dumps(req_log)))
    assert "error" not in resp_log
    log_content = json.loads(resp_log["result"]["content"][0]["text"])
    assert len(log_content) > 0 and "hash" in log_content[0]
    last_commit_hash = log_content[0]["hash"]
    print(f"[OK] git_log validado. Último commit detectado: {last_commit_hash}")
    
    # 4. git_show (con hash válido)
    req_show = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "git_show", "arguments": {"commit_hash": last_commit_hash}}}
    resp_show = json.loads(protocol.handle_line(json.dumps(req_show)))
    assert "error" not in resp_show
    show_content = json.loads(resp_show["result"]["content"][0]["text"])
    assert show_content["commit_hash"] == last_commit_hash
    print("[OK] git_show validado con hash real.")
    
    # 5. git_show (Inyección maliciosa bloqueada por RegEx)
    req_hack = {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "git_show", "arguments": {"commit_hash": "HEAD; rm -rf *"}}}
    resp_hack = json.loads(protocol.handle_line(json.dumps(req_hack)))
    assert "error" in resp_hack, "La inyección de comandos no fue bloqueada"
    assert "formato válido" in resp_hack["error"]["message"].lower() or "inseguros" in resp_hack["error"]["message"].lower()
    print("[OK] Ataque de Inyección de Comandos (;) estrictamente bloqueado por RegEx.")
    
    print("=== TODOS LOS TESTS DE GIT PASADOS CON ÉXITO ===")

if __name__ == "__main__":
    run_tests()
