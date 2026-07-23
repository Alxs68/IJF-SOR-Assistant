import os
import re
import json

# Define the inverse map
INVERSE_RELATIONS = {
    'define_a': 'definido_por',
    'definido_por': 'define_a',
    'complementa_a': 'complementado_por',
    'complementado_por': 'complementa_a',
    'exceptúa_a': 'exceptuado_por',
    'exceptua_a': 'exceptuado_por',
    'exceptuado_por': 'exceptúa_a',
    'es_exceptuado_por': 'exceptúa_a',
    'penaliza_a': 'penalizado_por',
    'penalizado_por': 'penaliza_a',
    'ilustra_a': 'ilustrado_por',
    'ilustrado_por': 'ilustra_a',
    'confirma_a': 'confirmado_por',
    'confirmado_por': 'confirma_a',
    'desarrolla_a': 'es_desarrollado_por',
    'es_desarrollado_por': 'desarrolla_a',
    'requiere_a': 'es_requerido_por',
    'es_requerido_por': 'requiere_a',
    'modifica_a': 'es_modificado_por',
    'es_modificado_por': 'modifica_a'
}

def fix_reciprocity(brain_dir):
    kuns = {}
    file_structures = {}
    
    source_dir = os.path.join(brain_dir, 'data', 'markdown')
    if not os.path.exists(source_dir):
        source_dir = brain_dir
        
    # 1. Read files and parse all JSONs
    for filename in os.listdir(source_dir):
        if filename.startswith('kuns_') and filename.endswith('.md'):
            filepath = os.path.join(source_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all JSON blocks and keep track of their positions
            # We want to replace each ```json ... ``` with its updated version.
            # We can split the file by the regex to keep markdown chunks intact.
            pattern = re.compile(r'(```json\s*.*?\s*```)', re.DOTALL)
            parts = pattern.split(content)
            
            file_structures[filename] = {
                'filepath': filepath,
                'parts': []
            }
            
            for part in parts:
                if part.startswith('```json'):
                    block_content = re.search(r'```json\s*(.*?)\s*```', part, re.DOTALL).group(1)
                    try:
                        data = json.loads(block_content)
                        kun_id = data['id_conocimiento']
                        kuns[kun_id] = {
                            'data': data,
                            'filename': filename,
                            'original_block': part
                        }
                        file_structures[filename]['parts'].append({
                            'is_json': True,
                            'kun_id': kun_id
                        })
                    except Exception as e:
                        # Print error and treat as plain text if it fails
                        print(f"Skipping block in {filename} due to error: {e}")
                        file_structures[filename]['parts'].append({
                            'is_json': False,
                            'text': part
                        })
                else:
                    file_structures[filename]['parts'].append({
                        'is_json': False,
                        'text': part
                    })
                    
    # 2. Build graph and find missing reciprocal edges
    missing_edges = [] # list of (node_to_add_to, target_id, relation_type)
    
    for kun_id, kun_info in kuns.items():
        data = kun_info['data']
        relations = data.get('relaciones', [])
        
        for rel in relations:
            dest_id = rel['id_destino']
            rel_type = rel['tipo_relacion']
            
            if dest_id not in kuns:
                # Broken link, handled by audit
                continue
                
            dest_kun = kuns[dest_id]['data']
            dest_relations = dest_kun.get('relaciones', [])
            
            # The expected inverse type
            expected_inverse = INVERSE_RELATIONS.get(rel_type)
            if not expected_inverse:
                continue
                
            # Check if reciprocal exists
            reciprocal_exists = False
            for d_rel in dest_relations:
                if d_rel['id_destino'] == kun_id:
                    # check if the type is correct
                    d_type = d_rel['tipo_relacion']
                    if d_type == expected_inverse or INVERSE_RELATIONS.get(d_type) == rel_type:
                        reciprocal_exists = True
                        break
            
            if not reciprocal_exists:
                missing_edges.append((dest_id, kun_id, expected_inverse))
                
    # 3. Apply missing edges
    for dest_id, kun_id, rel_type in missing_edges:
        dest_kun = kuns[dest_id]['data']
        if 'relaciones' not in dest_kun:
            dest_kun['relaciones'] = []
            
        # Check if already added in this script run
        already_added = False
        for rel in dest_kun['relaciones']:
            if rel['id_destino'] == kun_id and rel['tipo_relacion'] == rel_type:
                already_added = True
                break
                
        if not already_added:
            dest_kun['relaciones'].append({
                'tipo_relacion': rel_type,
                'id_destino': kun_id
            })
            print(f"Added reciprocal link: {dest_id} --({rel_type})--> {kun_id}")
            
    # 4. Write back files with pretty printed JSON blocks
    for filename, struct in file_structures.items():
        new_parts = []
        for part in struct['parts']:
            if part['is_json']:
                kun_id = part['kun_id']
                kun_data = kuns[kun_id]['data']
                # Sort relationships for consistency
                if 'relaciones' in kun_data:
                    kun_data['relaciones'] = sorted(kun_data['relaciones'], key=lambda x: (x['id_destino'], x['tipo_relacion']))
                
                # Format JSON with 2 space indent
                json_str = json.dumps(kun_data, indent=2, ensure_ascii=False)
                new_parts.append(f"```json\n{json_str}\n```")
            else:
                new_parts.append(part['text'])
                
        new_content = ''.join(new_parts)
        with open(struct['filepath'], 'w', encoding='utf-8') as f:
            f.write(new_content)
            
    print("Reciprocity fix complete!")

if __name__ == '__main__':
    brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fix_reciprocity(brain_path)
