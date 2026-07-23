# Unidades de Conocimiento Extraídas de PAG-002 (kuns_pag_002.md)
## Recurso: rules.ijf.org - Gripping (Kumikata)

Este archivo contiene el corpus extraído de **PAG-002** (Portal de reglas de Agarre) correspondiente a la cuarta entrega productiva de la **Fase 2.2B**.

---

### KUN-0023: Agarre Normal (Normal Kumikata)
```json
{
  "id_conocimiento": "KUN-0023",
  "titulo": "Definición y Requisitos del Agarre Normal",
  "tipo": "DEF",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Normal Kumikata is taking a grip on the opponent's jacket with both hands, sleeve and lapel, sleeve and collar, or pocket grip in traditional collar position.",
  "contenido_traduccion": "El Kumikata Normal consiste en tomar un agarre sobre la chaqueta del oponente con ambas manos: manga y solapa, manga y cuello, o agarre clásico en la solapa.",
  "interpretacion": "Establece la postura y técnica estándar de agarre requerida para iniciar acciones ofensivas antes de que se considere pasividad o combatividad negativa.",
  "fuente_origen": "PAG-002",
  "referencia_especifica": "rules.ijf.org/gripping/normal",
  "tags": [
    "kumikata"
  ],
  "relaciones": [
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0020"
    },
    {
      "tipo_relacion": "penalizado_por",
      "id_destino": "KUN-0024"
    },
    {
      "tipo_relacion": "penalizado_por",
      "id_destino": "KUN-0025"
    },
    {
      "tipo_relacion": "penalizado_por",
      "id_destino": "KUN-0042"
    },
    {
      "tipo_relacion": "complementado_por",
      "id_destino": "KUN-0045"
    }
  ]
}
```

---

### KUN-0025: Penalización por Agarre no Clásico sin Ataque
```json
{
  "id_conocimiento": "KUN-0025",
  "titulo": "Sanción por Agarre no Clásico sin Ataque Inmediato",
  "tipo": "PEN",
  "nivel_autoridad": "Norma",
  "version": "1.0",
  "idioma_original": "en",
  "vigencia_desde": "2026-01-01",
  "vigencia_hasta": "null",
  "contenido_original": "Taking a cross-grip, belt grip, pocket grip, or pistol grip and failing to attack immediately is penalized with Shido.",
  "contenido_traduccion": "Tomar un agarre cruzado, agarre de cinturón, agarre de bolsillo o agarre de pistola y no atacar de forma inmediata se penaliza con Shido.",
  "interpretacion": "Sanciona el uso táctico no clásico de agarres prohibidos a menos que se transicione de inmediato (sin retraso alguno) a una técnica de proyección.",
  "fuente_origen": "PAG-002",
  "referencia_especifica": "rules.ijf.org/gripping/illegal",
  "tags": [
    "shido",
    "kumikata"
  ],
  "relaciones": [
    {
      "tipo_relacion": "exceptuado_por",
      "id_destino": "KUN-0020"
    },
    {
      "tipo_relacion": "penaliza_a",
      "id_destino": "KUN-0023"
    }
  ]
}
```
