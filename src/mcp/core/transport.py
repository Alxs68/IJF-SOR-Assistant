import sys

class StdioTransport:
    """Manejo de bajo nivel síncrono para el canal stdio"""
    def read_line(self) -> str:
        line = sys.stdin.readline()
        if not line:
            return None
        return line.strip()

    def write_line(self, json_string: str):
        # Garantiza que el stdout contenga exclusivamente el protocolo MCP
        sys.stdout.write(json_string + "\n")
        sys.stdout.flush()
