# Unidades de Conocimiento Extraídas de PAG-004 (kuns_pag_004.md)
## Recurso: rules.ijf.org - Penalties

Este archivo contiene el corpus extraído de **PAG-004** (Portal de reglas de Penalizaciones) correspondiente a la sexta entrega productiva de la **Fase 2.2B**.

---

### KUN-0028: Sanción por Ataque Falso (False Attack)
```json
{
  "id_conocimiento": "KUN-0028",
  "titulo": "Penalización de Shido por Ataque Falso",
  "tipo": "PEN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "An attack that has no intent or preparation to throw the opponent, made solely to avoid passivity warnings, is penalized with Shido.",
  "contenido_traduccion": "Un ataque que no tiene la intención o preparación para proyectar al oponente, realizado únicamente para evitar amonestaciones de pasividad, se penaliza con Shido.",
  "interpretacion": "Sanciona los ataques tácticos sin intención ni preparación real de proyección, realizados con el propósito exclusivo de simular combatividad y eludir las amonestaciones de pasividad del árbitro.",
  "fuente_origen": "PAG-004",
  "referencia_especifica": "rules.ijf.org/penalties/false-attack",
  "tags": [
    "shido",
    "referee"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0036"
    }
  ]
}
```

---

### KUN-0029: Sanción por Salir del Área de Combate (Stepping Out)
```json
{
  "id_conocimiento": "KUN-0029",
  "titulo": "Penalización de Shido por Salir del Tatami",
  "tipo": "PEN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Stepping out of the contest area with one foot without an immediate attack or transition is penalized with Shido.",
  "contenido_traduccion": "Salir del área de combate con un pie sin realizar un ataque o transición inmediata se penaliza con Shido.",
  "interpretacion": "Regula el posicionamiento en el tatami. El atleta que traspase la zona exterior con un pie sin ejecutar un ataque o transición inmediata es sancionado, asegurando que el combate se mantenga dentro del área activa de la plataforma.",
  "fuente_origen": "PAG-004",
  "referencia_especifica": "rules.ijf.org/penalties/stepping-out",
  "tags": [
    "shido",
    "safety-area",
    "tatami"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementa_a",
      "id_destino": "KUN-0007"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0041"
    }
  ]
}
```

---

### KUN-0030: Penalización por Buceo de Cabeza (Diving)
```json
{
  "id_conocimiento": "KUN-0030",
  "titulo": "Penalización de Hansoku-make Directo por Buceo de Cabeza (Diving)",
  "tipo": "PEN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Diving head-first onto the tatami during a throw attempt is penalized with direct Hansoku-make.",
  "contenido_traduccion": "Bucear de cabeza (hacer clavado) sobre el tatami durante un intento de proyección se penaliza con Hansoku-make directo.",
  "interpretacion": "Prohíbe de forma absoluta la acción de clavado o buceo de cabeza durante un intento de proyección, debido al grave riesgo de lesiones cervicales y espinales para el competidor que la ejecuta.",
  "fuente_origen": "PAG-004",
  "referencia_especifica": "rules.ijf.org/penalties/diving",
  "tags": [
    "hansoku-make",
    "safety"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementa_a",
      "id_destino": "KUN-0001"
    }
  ]
}
```
