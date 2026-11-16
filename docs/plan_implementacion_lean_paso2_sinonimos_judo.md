# Plan de Implementación: Expansión de Vocabulario Coloquial de Judo (Fase Lean-2)
## Enriquecimiento del Tokenizador BM25 y Proyección Cruzada RRE

**Proyecto:** SOR-IJF — IJF Sport and Organisation Rules Assistant  
**Autorización Soberana:** Alexis Oliveros Lozano (2026-11-06T03:29:04-05:00)  
**Objetivo:** Elevar drásticamente la tasa de recuperación de pasajes normativos relevantes ante consultas redactadas en lenguaje coloquial o expresiones informales de combate en español e inglés.

---

### 1. Diagnóstico del Problema en Consultas Coloquiales
Actualmente, el diccionario `SPANISH_TO_ENGLISH_SYNONYMS` en `src/rre_engine.py` cuenta con ~140 términos mayoritariamente literales (ej. `"cabeza": "head"`, `"proyeccion": "throw"`).
Sin embargo, cuando un competidor, árbitro o entrenador formula preguntas coloquiales frecuentes como:
1. *"rodilla palanca en ne-waza"* $\rightarrow$ No asocia *"rodilla"* con *"joint other than elbow"* o *"ashi-garami"*, recuperando artículos genéricos de pág. 159 en lugar del **Art. 18.2.2 (pág. 191)**.
2. *"estrangular con la pretina o faldon desatado"* $\rightarrow$ No asocia *"pretina"* con *"belt / bottom of jacket"*, recuperando reglas de judogi C1.9 en lugar del **Art. 18.1.2 (pág. 184-185)**.
3. *"meter el pie en la solapa o cinturon"* $\rightarrow$ Recupera medidas de fabricación C1.10 en lugar de la prohibición de infracción ilegal **Art. 18.1.2 (pág. 184)**.
4. *"tirarse de cabeza"* $\rightarrow$ Aunque recupera pág. 190, la expansión puede fortalecerse con términos como *"zambullirse"*, *"diving"*, *"cervical"*, *"peligro"*.

---

### 2. Especificación del Diccionario Ampliado de Sinónimos y Colocaciones
Se enriquecerá `SPANISH_TO_ENGLISH_SYNONYMS` incorporando términos clave del arbitraje y coloquialismos frecuentes:

```python
COLLOQUIAL_JUDO_SYNONYMS = {
    # Acciones con la cabeza y cervicales
    "tirarse": "diving head",
    "tirar": "throw diving",
    "tirando": "diving",
    "zambullirse": "diving dive head",
    "zambullida": "diving dive head",
    "cervical": "cervical spine neck",
    "cervicales": "cervical spine neck",
    "nuca": "neck cervical",
    
    # Articulaciones y Luxaciones prohibidas (Art. 18.2.2 p.191)
    "rodilla": "joint knee ashi-garami kansetsu-waza elbow",
    "rodillas": "joint knee ashi-garami kansetsu-waza elbow",
    "tobillo": "joint ankle ashi-garami kansetsu-waza elbow",
    "tobillos": "joint ankle ashi-garami kansetsu-waza elbow",
    "muneca": "joint wrist kansetsu-waza elbow",
    "articulacion": "joint elbow",
    "articulaciones": "joints elbow",
    "palanca": "kansetsu-waza joint lock armlock",
    "palancas": "kansetsu-waza joint lock armlocks",
    "hiperextension": "overstretching leg leg-stretching",

    # Vestimenta, Faldón y Pretina (Art. 18.1.2 p.184-185)
    "pretina": "belt bottom jacket encircle",
    "pretinas": "belt bottom jacket encircle",
    "desatado": "unfastened untied belt jacket",
    "desatada": "unfastened untied belt jacket",
    "suelto": "unfastened untied",
    "suelta": "unfastened untied",
    "enrollar": "encircle encircling",
    "enrollado": "encircle encircling",
    "meter": "insert put foot leg",
    "boca": "mouth",

    # Comandos y Agarre
    "cruzado": "cross grip kumikata",
    "cruzada": "cross grip kumikata",
    "pistola": "pistol grip kumikata",
    "bolsillo": "pocket grip kumikata",
    "abrazo": "bearhug bear hug",
    "abrazar": "bearhug bear hug",
    "soltar": "break release grip",
    "romper": "break release grip",

    # Puntuaciones y Transiciones
    "costado": "lateral side waza-ari 90",
    "perpendicular": "lateral side waza-ari 90",
    "plano": "flat back ippon",
    "inercia": "continuation momentum",
    "falso": "false attack",
    "falsa": "false attack",
    "tiempo": "time wasting",
    "pasividad": "non-combativity shido",
    "empujar": "push pushing outside",
    "bloquear": "blocking defensive posture"
}
```

---

### 3. Protocolo de Verificación sin Regresiones
1. **Prueba Comparativa:** Ejecutar script antes y después para contrastar los scores y pasajes recuperados en las 6 consultas coloquiales.
2. **Prueba de No Regresión:** Ejecutar la suite completa de 267 tests base para garantizar 100% PASS sin alteraciones en las consultas canónicas existentes.
3. **Validación de Invarianza:** Confirmar que las consultas formales en inglés y con terminología oficial mantengan identidad exacta de pasajes.

---

*Documento preparatorio para revisión de Alexis Oliveros Lozano antes de la edición del código.*
