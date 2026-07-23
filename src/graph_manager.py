import os
import re
import json

class KnowledgeGraph:
    """Manages the nodes and semantically typed edges of the KUN Knowledge Graph."""
    
    def __init__(self):
        self.nodes = {}  # id_conocimiento -> dict (KUN data)
        self.edges = {}  # id_conocimiento -> list of dict ({'id_destino': str, 'tipo_relacion': str})
        self.in_edges = {}  # id_conocimiento -> list of dict ({'id_origen': str, 'tipo_relacion': str})
        
    def add_node(self, kun_id, kun_data):
        """Adds a KUN node to the graph."""
        self.nodes[kun_id] = kun_data
        if kun_id not in self.edges:
            self.edges[kun_id] = []
        if kun_id not in self.in_edges:
            self.in_edges[kun_id] = []
            
    def add_edge(self, src_id, dest_id, rel_type):
        """Adds a directed, semantically typed edge between two nodes."""
        if src_id not in self.edges:
            self.edges[src_id] = []
        # Avoid duplicate edges
        if not any(e['id_destino'] == dest_id and e['tipo_relacion'] == rel_type for e in self.edges[src_id]):
            self.edges[src_id].append({
                'id_destino': dest_id,
                'tipo_relacion': rel_type
            })
            
        if dest_id not in self.in_edges:
            self.in_edges[dest_id] = []
        if not any(e['id_origen'] == src_id and e['tipo_relacion'] == rel_type for e in self.in_edges[dest_id]):
            self.in_edges[dest_id].append({
                'id_origen': src_id,
                'tipo_relacion': rel_type
            })

    def get_kun(self, kun_id):
        """Retrieves a KUN node by its ID."""
        return self.nodes.get(kun_id)

    def get_neighbors(self, kun_id, rel_types=None):
        """Returns the neighbors of a KUN, optionally filtered by relationship types."""
        neighbors = []
        if kun_id not in self.edges:
            return neighbors
            
        for edge in self.edges[kun_id]:
            if rel_types is None or edge['tipo_relacion'] in rel_types:
                neighbors.append({
                    'id_destino': edge['id_destino'],
                    'tipo_relacion': edge['tipo_relacion'],
                    'direction': 'out'
                })
                
        if kun_id in self.in_edges:
            for edge in self.in_edges[kun_id]:
                if rel_types is None or edge['tipo_relacion'] in rel_types:
                    neighbors.append({
                        'id_destino': edge['id_origen'],
                        'tipo_relacion': edge['tipo_relacion'],
                        'direction': 'in'
                    })
        return neighbors

    def get_metrics(self):
        """Computes topological metrics of the graph."""
        num_nodes = len(self.nodes)
        
        # Count unique undirected edges
        undirected_edges = set()
        degree_map = {node_id: 0 for node_id in self.nodes}
        
        for u in self.edges:
            for edge in self.edges[u]:
                v = edge['id_destino']
                undirected_edges.add(tuple(sorted([u, v])))
                degree_map[u] += 1
                degree_map[v] += 1
                
        num_edges = len(undirected_edges)
        avg_degree = sum(degree_map.values()) / num_nodes if num_nodes > 0 else 0.0
        
        hubs = sorted(degree_map.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate connected components using BFS
        visited = set()
        components = []
        
        for node in self.nodes:
            if node not in visited:
                comp = []
                queue = [node]
                visited.add(node)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    # Get all direct undirected neighbors
                    curr_neighbors = []
                    if curr in self.edges:
                        curr_neighbors.extend([e['id_destino'] for e in self.edges[curr]])
                    if curr in self.in_edges:
                        curr_neighbors.extend([e['id_origen'] for e in self.in_edges[curr]])
                        
                    for n in curr_neighbors:
                        if n not in visited and n in self.nodes:
                            visited.add(n)
                            queue.append(n)
                components.append(comp)
                
        orphans = [node for node, deg in degree_map.items() if deg == 0]
        
        return {
            'nodes_count': num_nodes,
            'edges_count': num_edges,
            'avg_degree': avg_degree,
            'components_count': len(components),
            'orphans_count': len(orphans),
            'orphans': orphans,
            'hubs': hubs
        }

    def save_to_json(self, filepath):
        """Serializes the graph structure into a JSON file."""
        data = {
            'nodes': self.nodes,
            'edges': self.edges
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_json(self, filepath):
        """Deserializes the graph structure from a JSON file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Graph file not found: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.nodes = data.get('nodes', {})
        self.edges = data.get('edges', {})
        
        # Reconstruct in_edges
        self.in_edges = {kun_id: [] for kun_id in self.nodes}
        for src_id, src_edges in self.edges.items():
            for edge in src_edges:
                dest_id = edge['id_destino']
                rel_type = edge['tipo_relacion']
                if dest_id not in self.in_edges:
                    self.in_edges[dest_id] = []
                self.in_edges[dest_id].append({
                    'id_origen': src_id,
                    'tipo_relacion': rel_type
                })

def compile_graph_from_markdown(brain_dir):
    """Scans md files in brain_dir (or brain_dir/data/markdown), extracts JSON KUN blocks, and builds a KnowledgeGraph."""
    graph = KnowledgeGraph()
    source_dir = os.path.join(brain_dir, 'data', 'markdown')
    if not os.path.exists(source_dir):
        source_dir = brain_dir
        
    for filename in os.listdir(source_dir):
        if filename.startswith('kuns_') and filename.endswith('.md'):
            filepath = os.path.join(source_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            json_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    kun_id = data['id_conocimiento']
                    graph.add_node(kun_id, data)
                except Exception as e:
                    print(f"Error parsing KUN in {filename}: {e}")
                    
    for kun_id, kun_data in graph.nodes.items():
        relations = kun_data.get('relaciones', [])
        for rel in relations:
            dest_id = rel['id_destino']
            rel_type = rel['tipo_relacion']
            if dest_id in graph.nodes:
                graph.add_edge(kun_id, dest_id, rel_type)
                
    return graph

if __name__ == '__main__':
    brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Compiling graph from: {brain_path}")
    kg = compile_graph_from_markdown(brain_path)
    metrics = kg.get_metrics()
    print("Graph Compiled Successfully!")
    print(f"Nodes: {metrics['nodes_count']}, Edges: {metrics['edges_count']}")
    print(f"Average Degree: {metrics['avg_degree']:.2f}")
    
    out_file = os.path.join(brain_path, 'scratch', 'knowledge_graph.json')
    kg.save_to_json(out_file)
    print(f"Graph serialized to: {out_file}")
