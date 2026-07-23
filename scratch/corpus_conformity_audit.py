import os
import re
import json
import csv

# Define constants and allowed vocabularies
ALLOWED_TYPES = {'DEF', 'REG', 'PRO', 'PEN', 'PUN', 'EXC', 'CAS'}
ALLOWED_AUTHORITIES = {
    'Norma', 'Interpretación oficial', 'Caso práctico', 'Comunicado', 'Material complementario'
}

# Mapping of relationship types to their inverses
INVERSE_RELATIONS = {
    'define_a': 'definido_por',
    'definido_por': 'define_a',
    'complementa_a': 'complementado_por',
    'complementado_por': 'complementa_a',
    'exceptúa_a': 'exceptuado_por',
    'exceptua_a': 'exceptuado_por',
    'exceptuado_por': 'exceptua_a',
    'es_exceptuado_por': 'exceptua_a',
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

# Forbidden linguistic patterns in interpretations
ANTIPATTERN_INTENT = [r'\bpara evitar\b', r'\bcon el fin de\b', r'\bcon el propósito de\b', r'\bpara prevenir\b']
ANTIPATTERN_HISTORY = [r'\banteriormente\b', r'\breglamento anterior\b', r'\bciclo pasado\b']

def load_master_tags(filepath):
    """Parses taxonomy_tags.md to extract official allowed tags."""
    tags = set()
    if not os.path.exists(filepath):
        return tags
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find all pattern like #tag-name
    matches = re.findall(r'#([a-zA-Z0-9-]+)', content)
    for m in matches:
        tags.add(m.lower())
    return tags

def jaccard_similarity(str1, str2):
    """Calculates Jaccard similarity between two strings."""
    words1 = set(re.findall(r'\w+', str1.lower()))
    words2 = set(re.findall(r'\w+', str2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

def run_audit(brain_dir):
    """Executes the conformity audit on the corpus."""
    source_dir = os.path.join(brain_dir, 'data', 'markdown')
    if not os.path.exists(source_dir):
        source_dir = brain_dir
        
    master_tags_file = os.path.join(source_dir, 'taxonomy_tags.md')
    allowed_tags = load_master_tags(master_tags_file)
    
    kuns = {}
    errors_critical = []
    warnings = []
    
    # 1. Read files and extract KUN JSONs
    for filename in os.listdir(source_dir):
        if filename.startswith('kuns_') and filename.endswith('.md'):
            filepath = os.path.join(source_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract JSON blocks
            json_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            for block in json_blocks:
                try:
                    data = json.loads(block)
                except Exception as e:
                    errors_critical.append({
                        'type': 'Sintaxis JSON',
                        'file': filename,
                        'detail': f'Error de parseo JSON: {str(e)}'
                    })
                    continue
                
                # Verify JSON structure
                required_fields = [
                    'id_conocimiento', 'titulo', 'tipo', 'nivel_autoridad', 'version',
                    'idioma_original', 'vigencia_desde', 'vigencia_hasta', 'contenido_original',
                    'contenido_traduccion', 'interpretacion', 'fuente_origen', 'referencia_especifica',
                    'tags', 'relaciones'
                ]
                missing = [field for field in required_fields if field not in data]
                if missing:
                    errors_critical.append({
                        'type': 'Estructura JSON',
                        'file': filename,
                        'id': data.get('id_conocimiento', 'DESCONOCIDO'),
                        'detail': f'Campos faltantes: {", ".join(missing)}'
                    })
                    continue
                
                kun_id = data['id_conocimiento']
                if not re.match(r'^KUN-\d{4}$', kun_id):
                    errors_critical.append({
                        'type': 'Formato ID',
                        'file': filename,
                        'id': kun_id,
                        'detail': f'El ID {kun_id} no cumple el formato KUN-XXXX.'
                    })
                    continue
                
                if kun_id in kuns:
                    errors_critical.append({
                        'type': 'Duplicidad ID',
                        'file': filename,
                        'id': kun_id,
                        'detail': f'El ID {kun_id} está duplicado. Aparece en {filename} y {kuns[kun_id]["file"]}.'
                    })
                    continue
                
                # Save KUN record
                kuns[kun_id] = {
                    'data': data,
                    'file': filename,
                    'filepath': filepath
                }
    
    # 2. Run schema and validation checks on parsed KUNs
    for kun_id, record in kuns.items():
        data = record['data']
        filename = record['file']
        
        # Tipo validation
        if data['tipo'] not in ALLOWED_TYPES:
            errors_critical.append({
                'type': 'Tipo Conocimiento Inválido',
                'file': filename,
                'id': kun_id,
                'detail': f'El tipo {data["tipo"]} no está permitido.'
            })
            
        # Nivel de autoridad validation
        if data['nivel_autoridad'] not in ALLOWED_AUTHORITIES:
            errors_critical.append({
                'type': 'Nivel Autoridad Inválido',
                'file': filename,
                'id': kun_id,
                'detail': f'El nivel de autoridad {data["nivel_autoridad"]} no está permitido.'
            })
            
        # Consistencia documental: check source prefix against file name
        source = data['fuente_origen'].upper()
        # file format: kuns_doc_001.md -> doc-001
        expected_prefix = filename.replace('kuns_', '').replace('.md', '').upper().replace('_', '-')
        if source != expected_prefix:
            # Toleration for sub-items or general mappings if needed, but let's check
            # E.g. kuns_doc_001 -> DOC-001
            errors_critical.append({
                'type': 'Consistencia Documental',
                'file': filename,
                'id': kun_id,
                'detail': f'La KUN tiene fuente_origen={source} pero está en el archivo {filename} (esperado {expected_prefix}).'
            })
            
        # Verify tags
        for t in data['tags']:
            clean_t = t.replace('#', '').lower()
            if clean_t not in allowed_tags:
                warnings.append({
                    'type': 'Tag Fuera de Catálogo',
                    'file': filename,
                    'id': kun_id,
                    'detail': f'El tag "#{clean_t}" no está en taxonomy_tags.md.'
                })
                
        # Verify antipatterns in interpretation
        interpretacion = data['interpretacion']
        for p in ANTIPATTERN_INTENT:
            if re.search(p, interpretacion, re.IGNORECASE):
                warnings.append({
                    'type': 'Antipatrón de Intención',
                    'file': filename,
                    'id': kun_id,
                    'detail': f'La interpretación contiene la frase prohibida de intención: "{re.search(p, interpretacion, re.IGNORECASE).group()}".'
                })
        for p in ANTIPATTERN_HISTORY:
            if re.search(p, interpretacion, re.IGNORECASE):
                warnings.append({
                    'type': 'Antipatrón Histórico',
                    'file': filename,
                    'id': kun_id,
                    'detail': f'La interpretación contiene la palabra/frase histórica prohibida: "{re.search(p, interpretacion, re.IGNORECASE).group()}".'
                })

    # 3. Relationship and Graph validation
    edges = []
    orphans = []
    
    for kun_id, record in kuns.items():
        data = record['data']
        filename = record['file']
        relations = data['relaciones']
        
        has_relations = False
        seen_destinations = set()
        
        for rel in relations:
            has_relations = True
            dest_id = rel['id_destino']
            rel_type = rel['tipo_relacion']
            
            # Check if destination exists
            if dest_id not in kuns:
                errors_critical.append({
                    'type': 'Enlace Roto (id_destino inexistente)',
                    'file': filename,
                    'id': kun_id,
                    'detail': f'La relación apunta al destino inexistente {dest_id}.'
                })
                continue
            
            # Check for duplicate relationships
            if dest_id in seen_destinations:
                warnings.append({
                    'type': 'Relación Duplicada',
                    'file': filename,
                    'id': kun_id,
                    'detail': f'Existe más de una relación hacia el destino {dest_id}.'
                })
            seen_destinations.add(dest_id)
            
            # Check if relation type is allowed
            if rel_type not in INVERSE_RELATIONS:
                errors_critical.append({
                    'type': 'Tipo Relación Inválido',
                    'file': filename,
                    'id': kun_id,
                    'detail': f'El tipo de relación "{rel_type}" no está en el diccionario de relaciones.'
                })
                continue
            
            # Record edge for metrics
            edges.append((kun_id, dest_id, rel_type))
            
            # Check reciprocity
            # Check if destination KUN has a relation pointing back to this KUN with the inverse type
            dest_kun = kuns[dest_id]['data']
            dest_relations = dest_kun.get('relaciones', [])
            expected_inverse = INVERSE_RELATIONS[rel_type]
            
            reciprocity_found = False
            for d_rel in dest_relations:
                if d_rel['id_destino'] == kun_id and d_rel['tipo_relacion'] in (expected_inverse, rel_type): # allow unaccented/accented variations
                    # wait, let's make sure it is exactly the inverse or a valid synonym
                    # check if the relationship type maps to expected inverse
                    if INVERSE_RELATIONS.get(d_rel['tipo_relacion']) == rel_type or d_rel['tipo_relacion'] == expected_inverse:
                        reciprocity_found = True
                        break
            
            if not reciprocity_found:
                warnings.append({
                    'type': 'Falta de Reciprocidad de Grafo',
                    'file': filename,
                    'id': kun_id,
                    'detail': f'La relación {kun_id} --({rel_type})--> {dest_id} no tiene una relación recíproca en {dest_id} (esperado "{expected_inverse}").'
                })
        
        # Check if node is orphan
        if not has_relations:
            # Check if orphan status is justified (e.g. definitions or page indices)
            is_justified = (data['tipo'] == 'DEF') or ('PAG' in data['fuente_origen']) or (data['tipo'] == 'REG' and 'age' in [t.replace('#','').lower() for t in data['tags']])
            orphans.append({
                'id': kun_id,
                'file': filename,
                'tipo': data['tipo'],
                'justified': is_justified
            })

    # 4. Check for Semantic Similarity (Duplicate Ingest Candidates)
    duplicate_candidates = []
    kun_ids_list = list(kuns.keys())
    for i in range(len(kun_ids_list)):
        for j in range(i + 1, len(kun_ids_list)):
            id1 = kun_ids_list[i]
            id2 = kun_ids_list[j]
            str1 = kuns[id1]['data']['interpretacion']
            str2 = kuns[id2]['data']['interpretacion']
            sim = jaccard_similarity(str1, str2)
            if sim > 0.80:
                duplicate_candidates.append({
                    'id1': id1,
                    'id2': id2,
                    'similarity': sim,
                    'detail': f'Similitud léxica Jaccard de {sim*100:.1f}% entre interpretaciones.'
                })

    # 5. Graph metrics calculation
    unique_edges = set()
    degree_map = {k: 0 for k in kuns}
    for u, v, t in edges:
        # Undirected edge set
        unique_edges.add(tuple(sorted([u, v])))
        degree_map[u] += 1
        degree_map[v] += 1
        
    num_nodes = len(kuns)
    num_aristas = len(unique_edges)
    avg_degree = sum(degree_map.values()) / num_nodes if num_nodes > 0 else 0.0
    
    most_connected = sorted(degree_map.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # 6. Type counters
    type_counts = {}
    for kun_id, record in kuns.items():
        t = record['data']['tipo']
        type_counts[t] = type_counts.get(t, 0) + 1
        
    # 7. Dictamen determination
    if errors_critical:
        dictamen = '🔴 NO CONFORME'
    elif warnings:
        dictamen = '🟡 CONFORME CON OBSERVACIONES'
    else:
        dictamen = '🟢 CONFORME'
        
    audit_results = {
        'dictamen': dictamen,
        'metrics': {
            'num_nodes': num_nodes,
            'num_edges': num_aristas,
            'avg_degree': avg_degree,
            'orphans_count': len(orphans),
            'type_counts': type_counts
        },
        'errors_critical': errors_critical,
        'warnings': warnings,
        'duplicate_candidates': duplicate_candidates,
        'most_connected': most_connected,
        'orphans': orphans
    }
    
    return audit_results

def write_reports(results, brain_dir):
    """Writes report artifacts."""
    source_dir = os.path.join(brain_dir, 'data', 'markdown')
    if not os.path.exists(source_dir):
        source_dir = brain_dir
        
    # Write to docs/reports if directory exists, otherwise fallback to base
    reports_dir = os.path.join(brain_dir, 'docs', 'reports')
    if os.path.exists(reports_dir):
        report_path = os.path.join(reports_dir, 'AUD-001_Corpus_Conformity_Report.md')
    else:
        report_path = os.path.join(brain_dir, 'AUD-001_Corpus_Conformity_Report.md')
    
    markdown_content = []
    markdown_content.append("# Informe de Auditoría de Conformidad del Corpus (AUD-001)")
    markdown_content.append(f"## Dictamen Automatizado: {results['dictamen']}\n")
    markdown_content.append("---")
    markdown_content.append("## 1. Resumen Ejecutivo de Métricas del Grafo")
    markdown_content.append(f"* **Número de Nodos (KUNs):** {results['metrics']['num_nodes']}")
    markdown_content.append(f"* **Número de Aristas (Relaciones Únicas):** {results['metrics']['num_edges']}")
    markdown_content.append(f"* **Grado Promedio de Conexión:** {results['metrics']['avg_degree']:.2f}")
    markdown_content.append(f"* **Nodos Aislados (Huérfanos):** {results['metrics']['orphans_count']}")
    
    markdown_content.append("\n### Distribución por Tipo de Conocimiento:")
    for k, v in sorted(results['metrics']['type_counts'].items()):
        markdown_content.append(f"* **{k} ({k}):** {v}")
        
    markdown_content.append("\n---")
    markdown_content.append("## 2. No Conformidades Críticas (Errores)")
    if not results['errors_critical']:
        markdown_content.append("🟢 **No se encontraron No Conformidades Críticas en el corpus.**")
    else:
        markdown_content.append(f"⚠️ Se detectaron **{len(results['errors_critical'])} no conformidades críticas** que impiden la certificación:")
        for idx, err in enumerate(results['errors_critical'], 1):
            file_path_url = os.path.join(source_dir, err['file']).replace('\\', '/')
            markdown_content.append(f"\n{idx}. **[{err['type']}]** en file: [{err['file']}](file:///{file_path_url}) (KUN: {err.get('id', 'N/A')})")
            markdown_content.append(f"   * *Detalle:* {err['detail']}")
            
    markdown_content.append("\n---")
    markdown_content.append("## 3. Observaciones y Advertencias Menores")
    if not results['warnings']:
        markdown_content.append("🟢 **No se detectaron advertencias ni observaciones menores.**")
    else:
        markdown_content.append(f"⚠️ Se identificaron **{len(results['warnings'])} observaciones** que requieren revisión metodológica:")
        for idx, warn in enumerate(results['warnings'], 1):
            file_path_url = os.path.join(source_dir, warn['file']).replace('\\', '/')
            markdown_content.append(f"\n{idx}. **[{warn['type']}]** en file: [{warn['file']}](file:///{file_path_url}) (KUN: {warn['id']})")
            markdown_content.append(f"   * *Detalle:* {warn['detail']}")
            
    markdown_content.append("\n---")
    markdown_content.append("## 4. Candidatos a Duplicidad Semántica")
    if not results['duplicate_candidates']:
        markdown_content.append("🟢 **No se encontraron candidatos a duplicidad semántica (>80% similitud).**")
    else:
        markdown_content.append(f"ℹ️ Se identificaron **{len(results['duplicate_candidates'])} casos potenciales** para revisión manual:")
        for idx, cand in enumerate(results['duplicate_candidates'], 1):
            markdown_content.append(f"\n{idx}. **{cand['id1']}** y **{cand['id2']}** (Similitud: {cand['similarity']*100:.1f}%)")
            markdown_content.append(f"   * *Detalle:* {cand['detail']}")
            
    markdown_content.append("\n---")
    markdown_content.append("## 5. Análisis Técnico del Grafo")
    markdown_content.append("### Nodos más conectados (Hubs):")
    for node, deg in results['most_connected']:
        markdown_content.append(f"* **{node}:** {deg} conexiones.")
        
    markdown_content.append("\n### Nodos Huérfanos y Justificación:")
    for o in results['orphans']:
        just = "✓ Justificado (tipo DEF/Portal/Edad)" if o['justified'] else "⚠️ No Justificado (Revisar por qué está aislado)"
        file_path_url = os.path.join(source_dir, o['file']).replace('\\', '/')
        markdown_content.append(f"* **{o['id']}** ({o['tipo']}) en [{o['file']}](file:///{file_path_url}) - {just}")
        
    markdown_content.append("\n---")
    markdown_content.append("## 6. Dictamen de Certificación Final del Auditor")
    if results['dictamen'] == '🟢 CONFORME':
        markdown_content.append("### **DICTAMEN: CONFORME 🟢**\n")
        markdown_content.append("El corpus oficial en su versión 1.0 cumple íntegramente con todos los requisitos metodológicos, taxonomía de etiquetas, relaciones semánticas y principios de neutralidad documental del proyecto.")
        markdown_content.append("Se certifica formalmente el **Corpus Oficial v1.0** y se autoriza el paso a la **Fase 3: Explotación del Conocimiento (Grafo, Embeddings y RAG)**.")
    elif results['dictamen'] == '🟡 CONFORME CON OBSERVACIONES':
        markdown_content.append("### **DICTAMEN: CONFORME CON OBSERVACIONES 🟡**\n")
        markdown_content.append("El corpus oficial no contiene no conformidades críticas que afecten la integridad del sistema. Sin embargo, contiene advertencias de reciprocidad o tags fuera de catálogo.")
        markdown_content.append("Se autoriza el paso condicionado a la **Fase 3**, recomendando corregir las advertencias reportadas en la próxima versión menor (v1.1) del corpus.")
    else:
        markdown_content.append("### **DICTAMEN: NO CONFORME 🔴**\n")
        markdown_content.append("Se han detectado no conformidades críticas (errores JSON, inconsistencia documental, enlaces rotos) que impiden la certificación del corpus.")
        markdown_content.append("**No se autoriza el paso a la Fase 3.** Se debe corregir cada no conformidad y re-ejecutar esta auditoría.")
        
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))
        
    # 2. qa_results.json
    json_path = os.path.join(brain_dir, 'scratch', 'qa_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # 3. audit_metrics.csv
    csv_path = os.path.join(brain_dir, 'scratch', 'audit_metrics.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Metrica', 'Valor'])
        writer.writerow(['Num_Nodos', results['metrics']['num_nodes']])
        writer.writerow(['Num_Aristas', results['metrics']['num_edges']])
        writer.writerow(['Grado_Promedio', round(results['metrics']['avg_degree'], 3)])
        writer.writerow(['Num_Huerfanos', results['metrics']['orphans_count']])
        writer.writerow(['Dictamen', results['dictamen']])
        for k, v in results['metrics']['type_counts'].items():
            writer.writerow([f'Tipo_{k}', v])

if __name__ == '__main__':
    # Determine the project root path dynamically
    brain_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res = run_audit(brain_path)
    write_reports(res, brain_path)
    print(f"Auditoria ejecutada. Dictamen: {res['dictamen'].replace('🔴','[NO CONFORME]').replace('🟡','[CONFORME CON OBSERVACIONES]').replace('🟢','[CONFORME]')}. Errores: {len(res['errors_critical'])}, Advertencias: {len(res['warnings'])}")
