# Diccionario de Relaciones Semánticas (relationship_dictionary.md)
## Proyecto: IJF SOR Assistant

Este documento define la **semántica y reglas de uso de los verbos de enlace** en el grafo de conocimiento. Garantiza que las aristas de relaciones entre las KUNs se declaren de forma coherente y uniforme.

---

## 1. Relaciones de Definición y Conceptualización

### A. define_a / definido_por
* **Significado:** A representa un término, concepto, o ilustración que delimita o es la base para comprender la regla B.
* **Dirección (A → B):** `define_a` (DEF → REG / PRO / PEN / PUN)
* **Dirección (B → A):** `definido_por`
* **Criterio de Uso:** Se utiliza cuando un elemento del glosario o una especificación de tatami define los límites activos de una regla.
* *Ejemplo:* `KUN-0002` (Definición de Head Defence) `define_a` `KUN-0001` (Penalización Head Defence).

---

## 2. Relaciones de Complemento e Interconexión

### A. complementa_a / complementado_por
* **Significado:** El nodo A aporta detalles operativos, técnicos o de procedimiento que expanden la regla general B, sin contradecirla ni exceptuarla.
* **Dirección (A → B):** `complementa_a` (PRO / REG → REG)
* **Dirección (B → A):** `complementado_por`
* **Criterio de Uso:** Se usa entre normas de rango similar para enlazar procedimientos prácticos (ej: pesaje aleatorio complementa al pesaje oficial).
* *Ejemplo:* `KUN-0009` (Pesaje Oficial) `complementa_a` `KUN-0010` (Pesaje Aleatorio).

---

## 3. Relaciones de Excepción y Restricción

### A. exceptúa_a / exceptuado_por
* **Significado:** El nodo A describe una atenuante, exclusión o circunstancia especial que exime del cumplimiento o sanción de la regla general B.
* **Dirección (A → B):** `exceptúa_a` (EXC → REG / PEN / PUN)
* **Dirección (B → A):** `exceptuado_por`
* **Criterio de Uso:** Obligatorio para separar la descripción de una infracción de sus salvedades reglamentarias.
* *Ejemplo:* `KUN-0003` (Excepción por impacto involuntario) `exceptúa_a` `KUN-0001` (Sanción Head Defence).

---

## 4. Relaciones de Sanción

### A. penaliza_a / penalizado_por
* **Significado:** El nodo A define el castigo, sanción o amonestación (Shido/Hansoku-make) que se aplica al realizar la acción prohibida B.
* **Dirección (A → B):** `penaliza_a` (PEN → REG / DEF)
* **Dirección (B → A):** `penalizado_por`
* **Criterio de Uso:** Utilizado para conectar la prohibición de una técnica con su castigo correspondiente.

---

## 5. Relaciones de Demostración Visual y Evidencia

### A. ilustrado_por / ilustra_a
* **Significado:** El nodo A contiene material multimedia, planos o videoclips que ejemplifican físicamente la aplicación práctica de la regla B.
* **Dirección (A → B):** `ilustra_a` (CAS / IMG → REG / PEN / PUN)
* **Dirección (B → A):** `ilustrado_por`
* **Criterio de Uso:** Vincula clips de seminarios, esquemas técnicos o planos directamente a la norma que describen.
* *Ejemplo:* `KUN-0008` (Plano de Tatami) `ilustra_a` `KUN-0007` (Dimensiones de Tatami).

### B. confirmado_por / confirma_a
* **Significado:** La noticia, comunicado o circular A valida, ratifica o confirma la vigencia o modificaciones de la regla B.
* **Dirección (A → B):** `confirma_a` (NEW → REG / PEN / PUN)
* **Dirección (B → A):** `confirmado_por`
* **Criterio de Uso:** Vincula boletines informativos de final de ciclo directamente a la regla madre modificada.
