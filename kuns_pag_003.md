# Unidades de Conocimiento Extraídas de PAG-003 (kuns_pag_003.md)
## Recurso: rules.ijf.org - Scoring

Este archivo contiene el corpus extraído de **PAG-003** (Portal de reglas de Puntuación) correspondiente a la quinta entrega productiva de la **Fase 2.2B**.

---

### KUN-0026: Puntuación de Osaekomi-waza (Inmovilizaciones)
```json
{
  "id_conocimiento": "KUN-0026",
  "titulo": "Tiempos Oficiales de Puntuación para Osaekomi-waza",
  "tipo": "PUN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Osaekomi-waza is scored as Waza-ari for 10 to 19 seconds, and Ippon for 20 seconds.",
  "contenido_traduccion": "Osaekomi-waza se puntúa como Waza-ari de 10 a 19 segundos, e Ippon a los 20 segundos.",
  "interpretacion": "Define los tiempos oficiales de control continuo sobre la espalda del oponente en el suelo (ne-waza) necesarios para que el árbitro conceda puntuaciones técnicas acumulativas o de fin de combate.",
  "fuente_origen": "PAG-003",
  "referencia_especifica": "rules.ijf.org/scoring/osaekomi",
  "tags": [
    "scoring",
    "ippon",
    "waza-ari"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementa_a",
      "id_destino": "KUN-0017"
    },
    {
      "tipo_relacion": "complementa_a",
      "id_destino": "KUN-0018"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0037"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0038"
    },
    {
      "tipo_relacion": "penalizado_por",
      "id_destino": "KUN-0039"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0053"
    }
  ]
}
```

---

### KUN-0027: Puntuación por Caída sobre Codos o Manos
```json
{
  "id_conocimiento": "KUN-0027",
  "titulo": "Puntuación de Waza-ari por Aterrizaje sobre Ambos Codos",
  "tipo": "PUN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Landing on two elbows or two hands to absorb the impact is scored as Waza-ari.",
  "contenido_traduccion": "Caer sobre ambos codos o ambas manos para absorber el impacto se puntúa como Waza-ari.",
  "interpretacion": "Regula una situación específica de aterrizaje en la que apoyar ambos codos o ambas manos para absorber el impacto del derribo se evalúa como Waza-ari de forma automática para el rival.",
  "fuente_origen": "PAG-003",
  "referencia_especifica": "rules.ijf.org/scoring/landing",
  "tags": [
    "scoring",
    "waza-ari",
    "safety"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0021"
    }
  ]
}
```
