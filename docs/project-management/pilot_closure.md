# Acta de Cierre del Proyecto Piloto (pilot_closure.md)
## Proyecto: IJF SOR Assistant

* **Fase:** 2 – Construcción del Corpus de Conocimiento
* **Subetapa:** 2.2A – Diseño del Protocolo de Extracción y Proyecto Piloto
* **Fecha de Cierre:** 2026-07-19
* **Dictamen:** **APROBADO Y CONGELADO**

---

## 1. Objetivos del Piloto
El proyecto piloto tuvo como propósito principal validar en condiciones reales la viabilidad práctica del **Modelo de Conocimiento v1.0** y el **Protocolo de Extracción** antes de proceder a la fase de captura masiva del corpus. Específicamente, se buscaba verificar:
* El ajuste del esquema JSON de metadatos.
* El nivel de granularidad semántica para RAG.
* La conectividad y gramática del grafo de relaciones.
* El esfuerzo operativo estimado en tiempo y recursos.

---

## 2. Resultados Obtenidos
La extracción de prueba abarcó dos bloques temáticos sobre el recurso matriz **DOC-001 (SOR principal)**, resultando en:
* **8 Unidades de Conocimiento (KUN-0001 a KUN-0008) extraídas y validadas:**
  * 4 KUNs conceptuales complejas sobre **Defensa de Cabeza** (KUN-0001 a KUN-0008, abarcando penalizaciones, definiciones, excepciones y clips de video).
  * 4 KUNs directas sobre **Límites de Edad, Pesos, Dimensiones y Plano Técnico** del Tatami.
* **QA Exitoso:** El 100% de la muestra superó la validación humana de control sintáctico, granularidad y enlaces.

---

## 3. Lecciones Aprendidas
1. **Flexibilidad en KPIs:** El tiempo estimado (~4 minutos/KUN) y la densidad de relaciones (0.5/KUN) se adoptan formalmente como **líneas base informativas**, no como metas de productividad estrictas. La extracción de videos complejos y circulares puede requerir sustancialmente más tiempo que la captura directa de reglas escritas del SOR.
2. **No Homogeneidad del Grafo:** Es normal y esperable que la densidad del grafo no sea uniforme. Ciertas KUNs aisladas (como los límites de edad) operarán con cero relaciones, mientras que temas complejos y disputados (como *Kumikata* o *Diving*) concentrarán una alta densidad de aristas.
3. **Robustez del Campo Interpretación:** La separación entre `contenido_traduccion` e `interpretacion` demostró ser crítica. En el piloto de tatami y defensa de cabeza, la interpretación aportó la lógica de seguridad del atleta que complementa al texto normativo árido.

---

## 4. Decisiones y Acuerdos de Operación
* **Política de Nombres de KUNs:** Las KUNs del piloto se validan formalmente y se declaran como **las primeras 8 KUNs oficiales y productivas del corpus (KUN-0001 a KUN-0008)**, garantizando la continuidad de una numeración única sin namespaces separados.
* **Congelación del Diseño:** Se confirma que el **Modelo de Conocimiento v1.0** y el **Protocolo de Extracción** son plenamente suficientes y aptos, por lo que se congelan sin modificaciones adicionales para la fase masiva.

---

## 5. Autorización de Inicio de la Subetapa 2.2B
Con el dictamen favorable de interventoría y la resolución de las observaciones, se declara formalmente **concluida y aprobada la Subetapa 2.2A**, autorizando de forma inmediata el paso a la **Subetapa 2.2B: Extracción Sistemática** del resto del corpus aprobado.
