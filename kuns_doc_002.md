# Unidades de Conocimiento Extraídas de DOC-002 (kuns_doc_002.md)
## Recurso: Explanatory Guide of the Judo Refereeing Rules (Version 19)

Este archivo contiene el corpus extraído de **DOC-002** (Guía Explicativa) correspondiente a la segunda entrega productiva de la **Fase 2.2B**.

---

### KUN-0002: Definición de Defensa de Cabeza (Head Defence)
```json
{
  "id_conocimiento": "KUN-0002",
  "titulo": "Definición de Head Defence",
  "tipo": "DEF",
  "nivel_autoridad": "Interpretación oficial",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Head Defence is the action of touching the tatami with the head to support oneself and prevent landing on the back or shoulder.",
  "contenido_traduccion": "La Defensa de Cabeza es la acción de tocar el tatami con la cabeza para apoyarse y evitar caer sobre la espalda o el hombro.",
  "interpretacion": "Define físicamente la acción de apoyo sobre la cabeza; sirve como criterio de referencia para diferenciar el contacto voluntario (permitido en Seniors/Juniors y sancionado con Shido en Cadetes) del buceo de cabeza (sancionado con Hansoku-make).",
  "fuente_origen": "DOC-002",
  "referencia_especifica": "Explanatory Guide - Secc. Penalties, Diapositiva 12",
  "tags": [
    "head-defence",
    "tatami"
  ],
  "relaciones": [
    {
      "tipo_relacion": "define_a",
      "id_destino": "KUN-0001"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0035"
    }
  ]
}
```

---

### KUN-0017: Criterios de Puntuación de Ippon
```json
{
  "id_conocimiento": "KUN-0017",
  "titulo": "Criterios Técnicos para el Otorgamiento de Ippon",
  "tipo": "PUN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Ippon is awarded for a throw with control, force, speed, and landing largely on the back.",
  "contenido_traduccion": "Se otorga Ippon por una proyección ejecutada con control, fuerza, velocidad, y con la caída del oponente ampliamente sobre su espalda.",
  "interpretacion": "Establece los cuatro criterios mecánicos cumulativos necesarios para la puntuación máxima de proyección que finaliza inmediatamente el combate.",
  "fuente_origen": "DOC-002",
  "referencia_especifica": "Explanatory Guide - Secc. Scoring, Diapositiva 1",
  "tags": [
    "scoring",
    "ippon"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0019"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0026"
    }
  ]
}
```

---

### KUN-0018: Criterios de Puntuación de Waza-ari
```json
{
  "id_conocimiento": "KUN-0018",
  "titulo": "Criterios Técnicos para el Otorgamiento de Waza-ari",
  "tipo": "PUN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Waza-ari is awarded when the throw lacks one of the elements of Ippon, or when the opponent lands on the side, shoulder, or elbow.",
  "contenido_traduccion": "Se otorga Waza-ari cuando la proyección carece de uno de los elementos del Ippon, o cuando el oponente cae sobre el costado, el hombro o el codo.",
  "interpretacion": "Define la puntuación intermedia de combate aplicable cuando el impacto no es limpio sobre la espalda o cuando falta fuerza o velocidad.",
  "fuente_origen": "DOC-002",
  "referencia_especifica": "Explanatory Guide - Secc. Scoring, Diapositiva 3",
  "tags": [
    "scoring",
    "waza-ari"
  ],
  "relaciones": [
    {
      "tipo_relacion": "ilustrado_por",
      "id_destino": "KUN-0021"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0026"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0062"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0063"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0064"
    }
  ]
}
```

---

### KUN-0019: Defensa en Puente (Bridge Defense)
```json
{
  "id_conocimiento": "KUN-0019",
  "titulo": "Otorgamiento de Ippon por Defensa en Puente (Bridge)",
  "tipo": "PEN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "If the competitor arches their back (bridges) to avoid landing on their back during a throw, it is counted as Ippon for the attacker.",
  "contenido_traduccion": "Si el competidor arquea su espalda (hace puente) para evitar caer sobre su espalda durante una proyección, se contará como Ippon para el atacante.",
  "interpretacion": "Esta regla castiga de forma severa el puente de cabeza y talones. Debido al alto riesgo de fracturas cervicales, se penaliza otorgándole la victoria inmediata al atacante, desincentivando este tipo de defensa peligrosa.",
  "fuente_origen": "DOC-002",
  "referencia_especifica": "Explanatory Guide - Secc. Penalties, Diapositiva 15",
  "tags": [
    "safety",
    "head-defence",
    "ippon"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementa_a",
      "id_destino": "KUN-0001"
    },
    {
      "tipo_relacion": "complementa_a",
      "id_destino": "KUN-0017"
    }
  ]
}
```

---

### KUN-0020: Permisos de Agarre de Kumikata (Excepción)
```json
{
  "id_conocimiento": "KUN-0020",
  "titulo": "Permisos y Límites Temporales para Agarre no Clásico",
  "tipo": "EXC",
  "nivel_autoridad": "Interpretación oficial",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Cross-gripping, belt-gripping, pocket grip and pistol grip are allowed if the competitor initiates an attack immediately.",
  "contenido_traduccion": "El agarre cruzado, agarre de cinturón, agarre de bolsillo y agarre de pistola están permitidos si el competidor inicia un ataque de forma inmediata.",
  "interpretacion": "Establece la excepción del tiempo de gracia (generalmente entre 3 y 5 segundos) que permite a los competidores usar agarres no tradicionales para proyectar, prohibiendo su uso defensivo estático.",
  "fuente_origen": "DOC-002",
  "referencia_especifica": "Explanatory Guide - Secc. Kumikata, Diapositiva 5",
  "tags": [
    "kumikata",
    "shido",
    "grip-breaking"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementa_a",
      "id_destino": "KUN-0023"
    },
    {
      "tipo_relacion": "exceptua_a",
      "id_destino": "KUN-0024"
    },
    {
      "tipo_relacion": "exceptua_a",
      "id_destino": "KUN-0025"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0075"
    }
  ]
}
```

---

### KUN-0021: Caso Práctico - Waza-ari por Caída sobre Codo o Mano
```json
{
  "id_conocimiento": "KUN-0021",
  "titulo": "Ejemplo Visual - Waza-ari por Aterrizaje sobre Codo",
  "tipo": "CAS",
  "nivel_autoridad": "Caso práctico",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Slide showing sequence of blue athlete thrown and landing on the elbow/hand to absorb impact, scored as Waza-ari.",
  "contenido_traduccion": "Diapositiva que muestra la secuencia del atleta azul siendo proyectado y cayendo sobre el codo/mano para absorber el impacto, puntuado como Waza-ari.",
  "interpretacion": "Caso real de juzgamiento del seminario que ilustra un aterrizaje con codo apoyado en la caída, demostrando la aplicación del criterio de puntuación de Waza-ari.",
  "fuente_origen": "DOC-002",
  "referencia_especifica": "Explanatory Guide - Secc. Scoring, Diapositiva 4 - Clip 2",
  "tags": [
    "scoring",
    "waza-ari",
    "safety"
  ],
  "relaciones": [
    {
      "tipo_relacion": "ilustra_a",
      "id_destino": "KUN-0018"
    },
    {
      "tipo_relacion": "complementa_a",
      "id_destino": "KUN-0027"
    }
  ]
}
```
