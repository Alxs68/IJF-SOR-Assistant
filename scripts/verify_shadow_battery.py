import os
import sys
sys.path.insert(0, os.path.abspath("."))

from src.multisource_retriever import MultisourceRetriever
from src.rre_engine import ReasoningRetrievalEngine

retriever = MultisourceRetriever()
rre = ReasoningRetrievalEngine(allow_degraded=True, enable_shadow_mode_multisource=True)

test_cases = [
    {
        "category": "Normativa Disciplinaria (Sanciones y Prescripcion)",
        "query": "cuales son las sanciones disciplinarias en judo y plazo de prescripcion de 5 anos",
        "expected_doc": "KUN-DIS-001",
        "expected_chunks": ["CHK-KUN-DIS-001-002", "CHK-KUN-DIS-001-003"]
    },
    {
        "category": "Etica y Conducta (Apuestas y Manipulacion)",
        "query": "que prohibe el codigo de etica sobre apuestas deportivas y manipulacion de competiciones",
        "expected_doc": "KUN-ETH-001",
        "expected_chunks": ["CHK-KUN-ETH-001-002"]
    },
    {
        "category": "Salvaguardia y Proteccion (Tolerancia Cero)",
        "query": "tolerancia cero contra acoso abuso negligencia discriminacion en judo",
        "expected_doc": "KUN-ETH-001",
        "expected_chunks": ["CHK-KUN-ETH-001-003"]
    },
    {
        "category": "Clasificacion Olimpica LA28 (Cuota 342 y Top 17)",
        "query": "cuantos judocas clasifican directamente por el ranking mundial a los Juegos Olimpicos LA28 y cuantas plazas hay en total",
        "expected_doc": "KUN-QSY-001",
        "expected_chunks": ["CHK-KUN-QSY-001-001", "CHK-KUN-QSY-001-002"]
    },
    {
        "category": "Clasificacion Olimpica LA28 (Fechas y 5% Tolerancia)",
        "query": "periodo calificacion olimpica tolerancia peso equipos mixtos 15 de junio de 2026",
        "expected_doc": "KUN-QSY-001",
        "expected_chunks": ["CHK-KUN-QSY-001-004"]
    },
    {
        "category": "Arbitraje LA28 (Reverse Seoi-nage Senior)",
        "query": "esta permitido el reverse seoi-nage en senior comunicados oficiales",
        "expected_doc": "KUN-NEW-001",
        "expected_chunks": ["CHK-KUN-NEW-001-002"]
    },
    {
        "category": "Arbitraje (Limite de Agarre 30s Kumikata)",
        "query": "limite de tiempo 30 segundos kumi-kata agarre sin ataque",
        "expected_doc": "KUN-NEW-001",
        "expected_chunks": ["CHK-KUN-NEW-001-003"]
    },
    {
        "category": "Puntuacion (Yuko 5 a 9s Osaekomi)",
        "query": "puntuacion yuko inmovilizacion 5 a 9 segundos osaekomi",
        "expected_doc": "KUN-NEW-003",
        "expected_chunks": ["CHK-KUN-NEW-003-001"]
    },
    {
        "category": "Arbitraje Operativo (Continuidad a Suelo Ne-waza)",
        "query": "continuidad en la transicion a suelo ne-waza arbitro seminario",
        "expected_doc": "KUN-PPT-002",
        "expected_chunks": ["CHK-KUN-PPT-002-001"]
    },
    {
        "category": "Arbitraje Operativo (Arrastre Directo Shido)",
        "query": "penalizacion Shido por arrastre directo al suelo sin tecnica",
        "expected_doc": "KUN-PPT-002",
        "expected_chunks": ["CHK-KUN-PPT-002-002"]
    }
]

print("=== EJECUCION DE PRUEBAS DE RECUPERACION FUNCIONAL SHADOW ===\n")
passed = 0
for tc in test_cases:
    res = retriever.search(tc["query"], top_k=2, min_score=2.0)
    matches = res.get("matches", [])
    top_doc = matches[0].get("document_id") if matches else None
    top_chunk = matches[0].get("chunk_id") if matches else None
    
    doc_match = (top_doc == tc["expected_doc"])
    chunk_match = any(m.get("chunk_id") in tc["expected_chunks"] for m in matches)
    ok = doc_match and chunk_match
    if ok:
        passed += 1
        verdict = "PASSED"
    else:
        verdict = "FAILED"
    print(f"[{verdict}] {tc['category']}")
    print(f"  Query: {tc['query']}")
    print(f"  Esperado: {tc['expected_doc']} en {tc['expected_chunks']}")
    print(f"  Recuperado: Doc={top_doc}, TopChunk={top_chunk}, Score={matches[0].get('confidence_score') if matches else 'None'}")
    print()

print(f"Total Pruebas: {len(test_cases)} | Aprobadas: {passed} | Fallidas: {len(test_cases) - passed}")
