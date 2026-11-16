"""Fase 8 / Etapa 0 - Benchmark versionado de recuperacion normativa (benchmark_v1).

Politica de anotacion
  * Las consultas y anclas fueron redactadas con asistencia de IA a partir del texto literal
    del corpus SOR 2026-08. NO estan certificadas por arbitros: human_review_status =
    PENDIENTE_REVISION_ARBITRAL en todos los items.
  * Cada ancla (evidencia minima, referencia cruzada, excepcion) es un fragmento LITERAL del
    texto de la pagina; este script lo verifica (comparacion con espacios normalizados).
    Un ancla no localizable, o cuyo articulo no figura en los metadatos de esa pagina, queda
    marcada como PENDIENTE (no se corrige ni se infiere).
  * No se incluyen respuestas normativas: solo localizadores de evidencia.
  * Consultas ambiguas: expected_articles = "PENDIENTE"; candidate_articles son candidatas no verificadas.
  * El conjunto TEST es reservado: no debe usarse para ajustar reglas, umbrales ni prompts.

Uso:  python scripts/build_benchmark_v1.py [--check | --overwrite]
Solo biblioteca estandar. No modifica el corpus.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

VERSION = "benchmark_v1.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_REL = "data/processed/rebuild_2026_08_corrected/passages_candidate.json"
OUT_REL = "data/eval/benchmark_v1"
SPLIT_RATIOS = (("dev", 0.5), ("validation", 0.2), ("test", 0.3))
HUMAN = "PENDIENTE_REVISION_ARBITRAL"
SOURCE = "ASISTIDA_IA_ANCLADA_A_TEXTO_LITERAL"


def A(page, article, snippet):
    return {"page": page, "article": article, "snippet": snippet}


ITEMS = []


def Q(qid, lang, cat, diff, text, anchors=(), xrefs=(), exceptions=(), group=None, answerable=True,
      candidates=(), why=""):
    ITEMS.append({"id": qid, "language": lang, "category": cat, "difficulty": diff, "text": text,
                  "anchors": list(anchors), "xrefs": list(xrefs), "exceptions": list(exceptions),
                  "group": group or qid, "answerable": answerable, "candidates": list(candidates),
                  "justification": why})


ORD_ES, ORD_EN, EXC, OOD, AMB = "ORDINARIA_ES", "ORDINARIA_EN", "EXCEPCION_CONDICION_REFERENCIA", "FUERA_DE_DOMINIO", "AMBIGUA"
W = "Pregunta directa sobre una regla localizable en un unico pasaje."

# ---------------------------------------------------------------- 60 ordinarias ES
Q("B1-ES-001", "es", ORD_ES, "baja", "¿Se tolera la agresión o la violencia en los eventos del IJF World Judo Tour?", [A(14, "1.1.1", "Unacceptable behaviour, violence or aggression will not be tolerated")], why=W)
Q("B1-ES-002", "es", ORD_ES, "media", "¿Quién puede crear un Comité Disciplinario para evaluar violaciones de las reglas de la IJF?", [A(14, "1.2.1", "The IJF Executive Committee has the authority to establish a Disciplinary Committee")], why=W)
Q("B1-ES-003", "es", ORD_ES, "media", "¿Cómo se puede denunciar el amaño de combates o la manipulación de competiciones?", [A(16, "1.2.2", "Match fixing and competition manipulation can be reported, anonymously and confidentially")], why="Texto de continuacion de 1.2.2 en una pagina cuyos metadatos solo citan 1.2.3; mide recuperacion de continuaciones.")
Q("B1-ES-004", "es", ORD_ES, "media", "¿Quién es responsable del seguro de accidentes y de responsabilidad civil de los delegados?", [A(17, "1.3", "Each national federation is directly responsible for all its delegates registered on Judobase")], why=W)
Q("B1-ES-005", "es", ORD_ES, "media", "¿Quién registra el sexo biológico del atleta en Judobase?", [A(17, "1.4", "The national federation shall be responsible for identifying and registering the athlete’s biological sex in Judobase")], why=W)
Q("B1-ES-006", "es", ORD_ES, "media", "¿Quién debe obtener la autorización legal para que compitan atletas menores de edad?", [A(18, "1.5", "The national federations are responsible for obtaining legal approval and permission for minor athletes to compete")], why=W)
Q("B1-ES-007", "es", ORD_ES, "baja", "¿Qué documento acredita la nacionalidad de un atleta?", [A(18, "1.7", "The evidence of nationality shall be the production of a valid passport issued by the represented country")], why=W)
Q("B1-ES-008", "es", ORD_ES, "alta", "¿Puede un atleta representar a una nueva federación nacional antes de que pasen tres años?", [A(20, "1.7.1.1", "The IJF must approve the request to shorten the three-year period")], why=W)
Q("B1-ES-009", "es", ORD_ES, "media", "¿Cómo puede un atleta con estatus de refugiado formar parte del Equipo de Refugiados de la IJF?", [A(22, "1.7.2.2", "An athlete with an official refugee status may apply to become part of the IJF Refugee Team (IRT)")], why=W)
Q("B1-ES-010", "es", ORD_ES, "baja", "¿Qué nacionalidad debe tener un árbitro?", [A(25, "1.8", "The referee must be a national of the country of the national federation they represent")], why=W)
Q("B1-ES-011", "es", ORD_ES, "baja", "¿Cuál es la edad mínima para competir en eventos oficiales de la IJF?", [A(35, "2.3", "Athletes under 15 years of age are not allowed to compete in any official IJF event")], group="G-AGE-MIN", why=W)
Q("B1-ES-012", "es", ORD_ES, "baja", "¿Se permiten combates entre hombres y mujeres?", [A(37, "2.5", "Contests between men and women are not permitted")], group="G-MIXED-SEX", why=W)
Q("B1-ES-013", "es", ORD_ES, "media", "En la hoja de sorteo, ¿qué color de judogi lleva el atleta situado arriba?", [A(38, "2.5", "the athlete/team on top wears a white judogi and the one below wears a blue judogi")], why="Continuacion de 2.5 en pagina cuyos metadatos citan 2.5.1-2.5.4.")
Q("B1-ES-014", "es", ORD_ES, "baja", "¿En qué consiste el sistema de eliminación directa?", [A(38, "2.5.1", "This is a direct elimination format without a repechage")], group="G-DKO", why=W)
Q("B1-ES-015", "es", ORD_ES, "media", "¿Cómo funciona la doble repesca?", [A(38, "2.5.3", "In a double repechage, for each category, the athletes will be divided into two (2) tables")], why=W)
Q("B1-ES-016", "es", ORD_ES, "baja", "¿Qué es el sistema de round robin?", [A(39, "2.5.5", "a system where each athlete or team will compete against the other")], why=W)
Q("B1-ES-017", "es", ORD_ES, "media", "Si solo hay dos atletas en una categoría, ¿qué sistema de competición se aplica?", [A(40, "2.5.6", "if the wins are equal (1-1), a third contest will decide")], why=W)
Q("B1-ES-018", "es", ORD_ES, "baja", "¿Cuántos atletas componen un equipo mixto?", [A(42, "2.7.1", "Each mixed team must consist of six (6) athletes (3 women and 3 men)")], group="G-MIXED-TEAM-SIZE", why=W)
Q("B1-ES-019", "es", ORD_ES, "media", "¿Cuál es el número mínimo de atletas de un equipo femenino o masculino?", [A(45, "2.7.2", "A team must consist of a minimum of three (3) athletes")], why=W)
Q("B1-ES-020", "es", ORD_ES, "baja", "¿Puede la IJF intervenir en la tramitación de visados?", [A(47, "2.8.1", "The IJF is not authorised to intervene in visa application processes")], why=W)
Q("B1-ES-021", "es", ORD_ES, "media", "¿Dónde deben alojarse las delegaciones inscritas en un evento del World Judo Tour?", [A(48, "2.8.3", "must reserve their accommodation in one (1) of the official hotels published in the event outlines")], why=W)
Q("B1-ES-022", "es", ORD_ES, "media", "¿Se obtienen puntos de ranking mundial sin ganar ningún combate?", [A(51, "3.1", "the ranking points are scored only if a minimum of one (1) contest is won")], why=W)
Q("B1-ES-023", "es", ORD_ES, "media", "¿Cómo se calcula el ranking mundial de naciones de la IJF?", [A(57, "3.4", "The IJF Nations WRL consists of the sum of the current WRL points")], why=W)
Q("B1-ES-024", "es", ORD_ES, "media", "¿Qué ocurre en la hoja de sorteo si un atleta no se presenta al tatami para su combate?", [A(58, "3.5", "Any athlete who does not come to the tatami for a contest will have a line put through his name on the draw sheet")], why=W)
Q("B1-ES-025", "es", ORD_ES, "baja", "¿Puede el presidente de una federación nacional actuar como entrenador en un evento de la IJF?", [A(62, "4.2", "The President of a national federation cannot act as a coach or referee during events organised by the IJF")], why=W)
Q("B1-ES-026", "es", ORD_ES, "baja", "¿Cuándo deben realizarse las cancelaciones de atletas?", [A(63, "4.3", "Whenever possible, cancellations should be made before accreditation")], why=W)
Q("B1-ES-027", "es", ORD_ES, "baja", "¿Qué documentos de identidad se aceptan en la acreditación?", [A(68, "4.5", "Accepted documents are a valid passport or a valid national identity card")], why=W)
Q("B1-ES-028", "es", ORD_ES, "baja", "¿A qué hora se realiza el sorteo de los Grand Slam y Grand Prix?", [A(71, "5.1", "the draw will take place at 14:00 local time the day before the competition")], group="G-DRAW-TIME", why=W)
Q("B1-ES-029", "es", ORD_ES, "media", "¿Cuántos atletas son cabezas de serie en los eventos del World Judo Tour?", [A(71, "5.2", "up to a maximum of the top eight (8) athletes")], why=W)
Q("B1-ES-030", "es", ORD_ES, "media", "¿Existe tolerancia de peso en el pesaje oficial de juniors y seniors?", [A(75, "6.1", "there is no additional weight tolerance")], group="G-WEIGHT-TOL-JS", why=W)
Q("B1-ES-031", "es", ORD_ES, "baja", "¿Cuándo abre y cierra el pesaje no oficial?", [A(76, "6.2.2", "It opens 40 minutes before and closes 10 minutes prior to the official weigh-in")], group="G-UNOFFICIAL-WI", why=W)
Q("B1-ES-032", "es", ORD_ES, "baja", "¿Se realiza el pesaje oficial de hombres y mujeres en la misma sala?", [A(77, "6.2.3", "The official weigh-in must be held in separate rooms for men and women")], why=W)
Q("B1-ES-033", "es", ORD_ES, "media", "¿Cómo se registra a un atleta que no se presenta al pesaje oficial?", [A(78, "6.2.5", "this is noted beside his name on the official weigh-in list as DNS (did not show)")], why=W)
Q("B1-ES-034", "es", ORD_ES, "media", "¿Hay pesaje aleatorio en las competiciones por equipos mixtos de la IJF?", [A(79, "6.3", "Random weigh-in is carried out for individual events only")], why=W)
Q("B1-ES-035", "es", ORD_ES, "baja", "¿Cuándo se sortea a los atletas que pasarán el pesaje aleatorio?", [A(79, "6.3.1", "one (1) hour before the start of the competition")], why=W)
Q("B1-ES-036", "es", ORD_ES, "media", "¿Qué sanciones puede recibir un entrenador que infringe el código de conducta?", [A(89, "7.1", "penalties may range from a simple verbal warning to exclusion of competition")], why="La misma frase aparece en E1.5 (medicos); el ancla exige 7.1.")
Q("B1-ES-037", "es", ORD_ES, "baja", "¿Cuál es el código de vestimenta de los entrenadores durante el sorteo?", [A(89, "7.2", "formal suit (jacket, trousers, shirt, and tie for men")], why=W)
Q("B1-ES-038", "es", ORD_ES, "baja", "¿Cuándo puede un entrenador solicitar la revisión de un combate?", [A(90, "7.3", "A coach can request to review a contest at the end of the preliminaries or final block")], why=W)
Q("B1-ES-039", "es", ORD_ES, "baja", "¿Qué aforo mínimo debe tener la sede de los Juegos Olímpicos?", [A(93, "8.1", "For the Olympic Games the seating capacity should be a minimum of 10,000")], why=W)
Q("B1-ES-040", "es", ORD_ES, "media", "¿Se permiten manifestaciones políticas o religiosas en el área de competición?", [A(95, "8.6", "Religious, political, personal, commercial connotation or manifestation is prohibited for everyone on the field of play")], why=W)
Q("B1-ES-041", "es", ORD_ES, "baja", "¿Es obligatorio el sistema de video replay en las competiciones de la IJF?", [A(97, "8.7", "A certified Video Replay System is mandatory for all IJF-sanctioned competitions")], why="Continuacion de 8.7 en pagina con metadatos 8.8/8.9.")
Q("B1-ES-042", "es", ORD_ES, "baja", "¿Debe el medallista recoger personalmente su medalla en la ceremonia?", [A(98, "8.10", "Each athlete who has won a medal must be present at the ceremony to receive their medal personally")], why=W)
Q("B1-ES-043", "es", ORD_ES, "baja", "¿Qué edad mínima se exige para competir en la categoría de veteranos?", [A(103, "A1.4", "a minimum of 30 years of age within the year of the event")], group="G-VET-AGE", why=W)
Q("B1-ES-044", "es", ORD_ES, "baja", "¿Hay cabezas de serie en el campeonato de veteranos?", [A(105, "A1.9", "there is no seeding")], why=W)
Q("B1-ES-045", "es", ORD_ES, "baja", "¿Se realiza pesaje aleatorio a los veteranos?", [A(105, "A1.10", "There is no random weigh-in for veterans")], why=W)
Q("B1-ES-046", "es", ORD_ES, "baja", "¿Cuál es la edad mínima para participar en competiciones de kata?", [A(109, "B1.1", "Participants must be a minimum of 15 years of age in the calendar year")], why=W)
Q("B1-ES-047", "es", ORD_ES, "baja", "¿Qué dimensiones tiene el área de competición de kata?", [A(112, "B1.8", "The competition area dimension is 10 m x 10 m for world championships or 8 m x 8 m for other events")], why=W)
Q("B1-ES-048", "es", ORD_ES, "baja", "¿Pueden los entrenadores dar indicaciones durante las competiciones de kata?", [A(113, "B1.10", "Coaches will be admitted, but coaching is not allowed")], why=W)
Q("B1-ES-049", "es", ORD_ES, "baja", "¿Se permiten los judogis reversibles?", [A(115, "C1.1", "Reversible judogi (white one side and blue on the other) are not allowed")], group="G-REVERSIBLE", why=W)
Q("B1-ES-050", "es", ORD_ES, "media", "¿Qué etiqueta debe llevar la chaqueta del judogi para certificar que cumple las reglas?", [A(118, "C1.2", "unforgeable red or green optical label")], why=W)
Q("B1-ES-051", "es", ORD_ES, "baja", "¿Cuántos logotipos del fabricante se permiten por prenda del judogi?", [A(119, "C1.3", "Only one manufacturer’s logo per clothing item is allowed")], why=W)
Q("B1-ES-052", "es", ORD_ES, "baja", "¿Con qué instrumento se controla la talla del judogi?", [A(124, "C1.10", "The judogi and belt size is controlled by sokuteiki")], group="G-SOKUTEIKI", why=W)
Q("B1-ES-053", "es", ORD_ES, "media", "¿Cómo debe ser la camiseta que se lleva bajo el judogi?", [A(126, "C1.11", "White in colour (not transparent), short-sleeved and round-necked")], why=W)
Q("B1-ES-054", "es", ORD_ES, "baja", "¿Cuántos segundos de osaekomi se necesitan para ippon?", [A(152, "Article 7", "Ippon: 20 seconds")], group="G-OSAE-IPPON", why=W)
Q("B1-ES-055", "es", ORD_ES, "media", "¿En qué situaciones puede el árbitro anunciar Sono-mama?", [A(162, "Article 12", "can only be applied in situations where athletes are working in ne-waza")], why=W)
Q("B1-ES-056", "es", ORD_ES, "baja", "¿Qué sucede cuando un atleta obtiene un segundo waza-ari?", [A(172, "Article 16", "Should one athlete gain a second waza-ari in the contest")], why=W)
Q("B1-ES-057", "es", ORD_ES, "media", "¿Qué ocurre si ambos atletas reciben tres shido?", [A(194, "Article 18.3.1", "if both athletes receive three shido, both athletes will be considered losers")], group="G-DOUBLE-HSK", why=W)
Q("B1-ES-058", "es", ORD_ES, "baja", "¿Cuándo se gana un combate por fusen-gachi?", [A(195, "Article 19.1", "An athlete wins by fusen-gachi (win by default) when the opponent does not appear for the contest according to the 30-second rule")], group="G-FUSEN", why=W)
Q("B1-ES-059", "es", ORD_ES, "baja", "¿Puede un atleta competir mientras sangra?", [A(198, "Article 20.3.1", "The athlete is not allowed to compete while bleeding")], group="G-BLEEDING", why=W)
Q("B1-ES-060", "es", ORD_ES, "media", "¿Cuánto tiempo debe esperar un atleta con sospecha de conmoción cerebral para volver a competir?", [A(202, "E1.2", "are not allowed to compete within the period of seven (7) days starting the day after the date of the injury")], group="G-CONCUSSION", why=W)

# ---------------------------------------------------------------- 30 ordinarias EN
P = "Equivalente EN de una consulta ES (mismo grupo semantico, mismo split) para medir efecto del idioma."
Q("B1-EN-001", "en", ORD_EN, "baja", "What is the minimum age to compete in official IJF events?", [A(35, "2.3", "Athletes under 15 years of age are not allowed to compete in any official IJF event")], group="G-AGE-MIN", why=P)
Q("B1-EN-002", "en", ORD_EN, "baja", "Are contests between men and women permitted?", [A(37, "2.5", "Contests between men and women are not permitted")], group="G-MIXED-SEX", why=P)
Q("B1-EN-003", "en", ORD_EN, "baja", "What is the direct knockout competition system?", [A(38, "2.5.1", "This is a direct elimination format without a repechage")], group="G-DKO", why=P)
Q("B1-EN-004", "en", ORD_EN, "baja", "How many athletes make up a mixed team?", [A(42, "2.7.1", "Each mixed team must consist of six (6) athletes (3 women and 3 men)")], group="G-MIXED-TEAM-SIZE", why=P)
Q("B1-EN-005", "en", ORD_EN, "baja", "At what time does the draw take place for Grand Slam and Grand Prix events?", [A(71, "5.1", "the draw will take place at 14:00 local time the day before the competition")], group="G-DRAW-TIME", why=P)
Q("B1-EN-006", "en", ORD_EN, "media", "Is there any weight tolerance at the official weigh-in for juniors and seniors?", [A(75, "6.1", "there is no additional weight tolerance")], group="G-WEIGHT-TOL-JS", why=P)
Q("B1-EN-007", "en", ORD_EN, "baja", "When does the unofficial weigh-in open and close?", [A(76, "6.2.2", "It opens 40 minutes before and closes 10 minutes prior to the official weigh-in")], group="G-UNOFFICIAL-WI", why=P)
Q("B1-EN-008", "en", ORD_EN, "baja", "What is the minimum age to compete as a veteran?", [A(103, "A1.4", "a minimum of 30 years of age within the year of the event")], group="G-VET-AGE", why=P)
Q("B1-EN-009", "en", ORD_EN, "baja", "Are reversible judogi allowed?", [A(115, "C1.1", "Reversible judogi (white one side and blue on the other) are not allowed")], group="G-REVERSIBLE", why=P)
Q("B1-EN-010", "en", ORD_EN, "baja", "Which instrument is used to control the judogi size?", [A(124, "C1.10", "The judogi and belt size is controlled by sokuteiki")], group="G-SOKUTEIKI", why=P)
Q("B1-EN-011", "en", ORD_EN, "baja", "How many seconds of osaekomi are needed for ippon?", [A(152, "Article 7", "Ippon: 20 seconds")], group="G-OSAE-IPPON", why=P)
Q("B1-EN-012", "en", ORD_EN, "media", "What happens if both athletes receive three shido?", [A(194, "Article 18.3.1", "if both athletes receive three shido, both athletes will be considered losers")], group="G-DOUBLE-HSK", why=P)
Q("B1-EN-013", "en", ORD_EN, "baja", "When is a contest won by fusen-gachi?", [A(195, "Article 19.1", "An athlete wins by fusen-gachi (win by default) when the opponent does not appear for the contest according to the 30-second rule")], group="G-FUSEN", why=P)
Q("B1-EN-014", "en", ORD_EN, "baja", "Can an athlete compete while bleeding?", [A(198, "Article 20.3.1", "The athlete is not allowed to compete while bleeding")], group="G-BLEEDING", why=P)
Q("B1-EN-015", "en", ORD_EN, "media", "How long must an athlete with suspected concussion wait before competing again?", [A(202, "E1.2", "are not allowed to compete within the period of seven (7) days starting the day after the date of the injury")], group="G-CONCUSSION", why=P)
Q("B1-EN-016", "en", ORD_EN, "baja", "What temperature should be maintained in the training areas?", [A(93, "8.2", "a temperature of 18 - 22oC maintained")], why=W)
Q("B1-EN-017", "en", ORD_EN, "baja", "Who is responsible for judogi control at IJF events?", [A(94, "8.3", "Check-in and judogi control are the responsibility of the IJF Education and Coaching Commission")], why=W)
Q("B1-EN-018", "en", ORD_EN, "baja", "Can photographers live stream during the competition?", [A(97, "8.9", "It is expressly forbidden for all media including photographers to live stream")], why=W)
Q("B1-EN-019", "en", ORD_EN, "media", "What happens if a competition is delayed after its scheduled start time?", [A(99, "8.11", "the competition will be restarted if it can be completed within the")], why=W)
Q("B1-EN-020", "en", ORD_EN, "media", "In a veterans round robin that goes into golden score, how long can osaekomi-waza be held?", [A(105, "A1.14", "If a round robin contest goes into golden score, an athlete can hold osaekomi-waza until for ippon")], why=W)
Q("B1-EN-021", "en", ORD_EN, "baja", "How many kata pairs are seeded in the draw?", [A(110, "B1.4", "The top six (6) pairs on the ranking list will be considered seeded")], why=W)
Q("B1-EN-022", "en", ORD_EN, "baja", "How often is the official judogi control carried out on competition days?", [A(116, "C1.1.3", "On each competition day the official judogi control will take place for each contest")], why=W)
Q("B1-EN-023", "en", ORD_EN, "media", "May the national emblem on the judogi mention an institution?", [A(120, "C1.4", "Mention of an institution is not allowed")], why=W)
Q("B1-EN-024", "en", ORD_EN, "media", "In which cases is a reserve judogi provided?", [A(127, "C1.12", "Torn judogi during a contest")], why="Continuacion de C1.12 en pagina cuyos metadatos citan C1.13.")
Q("B1-EN-025", "en", ORD_EN, "baja", "What are the age limits for continental referee examinations?", [A(135, "Article 1", "The ages limits for continental referee examinations are 25-45 years old")], why=W)
Q("B1-EN-026", "en", ORD_EN, "media", "Is a technique started in the last second of the contest time valid?", [A(153, "Article 8", "Any immediate result of a technique started at the very latest in the last second of the valid time shall be valid")], why=W)
Q("B1-EN-027", "en", ORD_EN, "baja", "How can a contest be won in regular time?", [A(163, "Article 13", "In regular time (4 minutes), a contest can be won by")], why=W)
Q("B1-EN-028", "en", ORD_EN, "media", "How long may an athlete hold conventional kumikata without attacking?", [A(177, "Article 18.1.1", "The time between conventional kumikata and making an attack is 45 seconds if there is a positive progression")], why=W)
Q("B1-EN-029", "en", ORD_EN, "baja", "What takes priority when an athlete is injured during a contest?", [A(196, "Article 20", "Athlete safety takes priority over the continuation of a contest")], why=W)
Q("B1-EN-030", "en", ORD_EN, "baja", "Which laboratories may analyse doping control samples?", [A(203, "E1.6.4", "Only WADA accredited approved Laboratories can analyse the samples")], why=W)

# ---------------------------------------------------------------- 30 excepciones / condiciones / referencias
X = "Requiere conservar la regla y su excepcion/condicion (o la referencia cruzada) en la evidencia entregada."
Q("B1-EX-001", "es", EXC, "alta", "En cadetes, ¿cómo se sanciona el head diving y puede el atleta seguir en la competición?",
  [A(190, "Article 18.2.1", "Techniques using head diving are dangerous and will be penalised with hansoku-make")],
  xrefs=[A(188, "Article 18.1.4", "In cadet events athletes are not allowed to use the head to defend as UKE")],
  exceptions=[A(190, "Article 18.2.1", "If this type of hansoku-make is awarded the athlete CAN continue in the competition")],
  why="El texto remite a 'Article 18.1.4 point 34'; la referencia y la condicion de continuidad deben conservarse.")
Q("B1-EX-002", "es", EXC, "alta", "Si uke hace puente al caer pero aterriza sobre el cuerpo de tori, ¿se otorga ippon?",
  [A(166, "Article 14", "voluntarily makes a “bridge”")],
  exceptions=[A(167, "Article 14", "No score or penalty will be given if the landing of uke occurs on the body of tori")], why=X)
Q("B1-EX-003", "en", EXC, "alta", "When the referee penalises an athlete during ne-waza, must he always announce Mate first?",
  [A(175, "Article 18", "he shall temporarily stop the contest by announcing")],
  xrefs=[A(174, "Article 17", "the referee will award directly the penalty pointing uke without interrupting the contest")],
  exceptions=[A(175, "Article 18", "except in the case of")], why=X)
Q("B1-EX-004", "es", EXC, "alta", "Si una proyección coincide con la señal de tiempo pero no es efectiva de inmediato, ¿es válida?",
  [A(153, "Article 8", "Any immediate result of a technique started at the very latest in the last second of the valid time shall be valid")],
  exceptions=[A(153, "Article 8", "Although a throwing technique may be applied simultaneously with the time signal")], why=X)
Q("B1-EX-005", "en", EXC, "media", "Is a technique applied after the time signal valid if the referee has not yet announced Sore-made?",
  [A(153, "Article 8", "Any technique applied after the time signal to indicate the expiry of the time of the contest shall not be valid")], why=X)
Q("B1-EX-006", "es", EXC, "alta", "¿Puede mantenerse una estrangulación iniciada dentro del área si los atletas salen fuera del área de combate?",
  [A(151, "Article 5", "initiated inside the contest area and recognised as being effective to the opponent can be maintained")],
  exceptions=[A(152, "Article 5", "If during ne-waza outside the contest area the athletes go out of the safety area")], why=X)
Q("B1-EX-007", "es", EXC, "alta", "Si una inmovilización sale del área de combate y sobrepasa el área de seguridad, ¿qué debe anunciar el árbitro?",
  [A(174, "Article 17", "goes beyond the limit of the safety area the referee must call")], why=X)
Q("B1-EX-008", "en", EXC, "alta", "If one mixed team athlete becomes ill after weigh-in leaving only three available athletes, can the team still compete?",
  [A(42, "2.7.1", "Each mixed team must consist of six (6) athletes (3 women and 3 men)")],
  exceptions=[A(42, "2.7.1", "However, if four (4) athletes have successfully passed the mixed team weigh-in")], why=X)
Q("B1-EX-009", "es", EXC, "alta", "¿Puede un atleta usar la tolerancia del 5% para competir en una categoría de equipo mixto inferior a la individual?",
  [A(79, "6.3", "cannot be more than 5 % higher than the official maximum weight limit of the category")],
  exceptions=[A(82, "6.4.2", "The +5% weight tolerance cannot be used by an athlete wishing to compete in a lower Mixed Team weight category")], why=X)
Q("B1-EX-010", "en", EXC, "media", "Do cadets receive any weight allowance at the official weigh-in?",
  [A(75, "6.1", "there is no additional weight tolerance")],
  exceptions=[A(75, "6.1", "to compensate an additional 0.2 kg will be allowed")], why=X)
Q("B1-EX-011", "es", EXC, "media", "¿A cuántos atletas por categoría se sortea para el pesaje aleatorio y hay categorías excluidas?",
  [A(79, "6.3.1", "Four athletes per category (except those that are plus categories) will be drawn")], why=X)
Q("B1-EX-012", "en", EXC, "media", "Can national federation Referee Directors referee at Continental Cups?",
  [A(136, "Article 1", "Exception: national federation Referee Director(s) can referee at cadets and juniors Continental Cups")],
  why="Excepcion explicita en texto de continuacion del Article 1.")
Q("B1-EX-013", "es", EXC, "media", "¿Se puede tapar con cinta o parches una parte del judogi?",
  [A(116, "C1.1.3", "It is not permitted to cover up/ patch any part of the judogi or belt with tape")],
  exceptions=[A(116, "C1.1.3", "except under particular circumstances agreed by the IJF Executive Committee")], why=X)
Q("B1-EX-014", "es", EXC, "media", "Si el entrenador no llega al control de judogi porque está dirigiendo a otro atleta, ¿qué ocurre?",
  [A(116, "C1.1.3", "However, if the coach is not present for a valid reason")], why=X)
Q("B1-EX-015", "en", EXC, "media", "Under what circumstances may male athletes wear a t-shirt under the judogi?",
  [A(126, "C1.11", "The wearing of a t-shirt for male athletes is authorised for medical reasons")], why=X)
Q("B1-EX-016", "es", EXC, "media", "¿Pueden las protecciones de las piernas llegar por debajo de la rodilla?",
  [A(128, "C1.13", "These should not go below the knee, except if it is a separate protection made of soft material")], why=X)
Q("B1-EX-017", "en", EXC, "alta", "Should the referee announce Mate to stop athletes going slightly outside the contest area?",
  [A(161, "Article 11", "no more than two metres unless the situation is considered dangerous")], why=X)
Q("B1-EX-018", "es", EXC, "alta", "Si al final del tiempo regular no hay puntuación técnica pero un atleta tiene más shido, ¿quién gana?",
  [A(164, "Article 13", "the contest shall continue in golden score regardless of the number of shido given")],
  xrefs=[A(175, "Article 18", "A contest cannot be decided by single or accumulated shido, until hansoku-make is reached")], why=X)
Q("B1-EX-019", "en", EXC, "alta", "In a kaeshi-waza situation, can the counterattacking athlete use the landing impact to finish the action?",
  [A(165, "Article 13", "CANNOT use the impact of landing on the tatami")], why=X)
Q("B1-EX-020", "es", EXC, "alta", "Si ambos atletas caen tras ataques que parecen simultáneos, ¿se otorga puntuación?",
  [A(167, "Article 14", "the referees cannot decide which technique dominated there should be no score awarded")], why=X)
Q("B1-EX-021", "es", EXC, "alta", "¿Se sanciona siempre salir intencionadamente del área de combate o hay excepciones?",
  [A(177, "Article 18.1.1", "In tachi-waza to intentionally go outside the contest area")],
  xrefs=[A(151, "Article 5", "All actions are valid and may continue (no mate)")],
  exceptions=[A(177, "Article 18.1.1", "Exception: osaekomi-waza, shime-waza and kansetsu-waza where the action starts inside the contest area")],
  why="El texto remite a 'Article 5 - Exceptions'.")
Q("B1-EX-022", "en", EXC, "media", "Is it allowed to grip inside the bottom of the trouser leg?",
  [A(180, "Article 18.1.2", "In tachi-waza it is not allowed to grip inside the bottom of the trouser leg")],
  exceptions=[A(180, "Article 18.1.2", "In ne-waza it is allowed to grip inside the bottom of the trouser leg")], why=X)
Q("B1-EX-023", "es", EXC, "media", "¿Se sanciona romper el agarre del rival con las dos manos?",
  [A(180, "Article 18.1.2", "Breaking the grip with two hands but NOT keeping a grip is shido")],
  exceptions=[A(180, "Article 18.1.2", "Breaking the grips with one or two hands but keeping minimum one grip is allowed")], why=X)
Q("B1-EX-024", "en", EXC, "media", "When is it possible to grip the opponent's leg?",
  [A(183, "Article 18.1.2", "It is possible to grip the leg only when the two opponents are in a clear ne-waza position")], why=X)
Q("B1-EX-025", "es", EXC, "media", "¿Está permitido el abrazo de oso (bear hug) en tachi-waza?",
  [A(185, "Article 18.1.2", "Bear hug in tachi-waza is allowed if tori’s hands are not clasped")], why=X)
Q("B1-EX-026", "en", EXC, "alta", "In cadet events, is reverse seoi-nage scored, and are seoi-nage variations allowed?",
  [A(189, "Article 18.1.4", "In cadet events there will be no score for reverse seoi-nage")],
  exceptions=[A(189, "Article 18.1.4", "The application of seoi-nage techniques when uke can perform ukemi and tori can control is allowed")], why=X)
Q("B1-EX-027", "es", EXC, "alta", "Tras un hansoku-make por actos contra el espíritu del judo, ¿puede el atleta seguir en el torneo?",
  [A(190, "Article 18.2.2", "If this type of hansoku-make is awarded the athlete CANNOT continue in the competition")],
  xrefs=[A(190, "Article 18.2.1", "If this type of hansoku-make is awarded the athlete CAN continue in the competition")], why=X)
Q("B1-EX-028", "en", EXC, "alta", "In cadet events, can an athlete who loses consciousness from a strangulation continue in the competition?",
  [A(199, "Article 20.3.2", "In cadet events, if an athlete loses consciousness during shime-waza he CANNOT continue in the competition")],
  exceptions=[A(199, "Article 20.3.2", "If during shime-waza an athlete gives up")],
  why="Texto de continuacion en pagina cuyos metadatos citan solo Article 21.")
Q("B1-EX-029", "es", EXC, "media", "¿Se considera el vómito como incapacidad para continuar el combate?",
  [A(197, "Article 20.1", "Vomiting by an athlete shall be considered an inability to continue")], why=X)
Q("B1-EX-030", "en", EXC, "alta", "If it is impossible to determine which athlete caused an injury, who loses the contest?",
  [A(196, "Article 20.1", "Where it is impossible to determine which of the athletes was the cause of the injury, the athlete unable to continue shall lose the contest")], why=X)

# ---------------------------------------------------------------- 15 fuera de dominio
O = "Fuera del dominio SOR; respuesta esperada: abstencion. {}"
for qid, lang, diff, text, note in [
    ("B1-OOD-001", "es", "baja", "¿Cuándo se señala fuera de juego en fútbol?", "Deporte distinto."),
    ("B1-OOD-002", "es", "baja", "¿Qué penalización aplica por exceso de velocidad en el pit lane en Fórmula 1?", "Deporte distinto con vocabulario de penalizacion."),
    ("B1-OOD-003", "es", "baja", "¿Cuántos tiros libres se conceden por una falta personal en baloncesto?", "Deporte distinto con vocabulario de falta."),
    ("B1-OOD-004", "es", "baja", "¿Cómo se calcula el interés compuesto anual?", "Dominio no deportivo."),
    ("B1-OOD-005", "en", "baja", "How does a tie-break work in tennis?", "Deporte distinto."),
    ("B1-OOD-006", "en", "media", "What is the penalty for a false start in swimming?", "Deporte distinto con vocabulario de sancion."),
    ("B1-OOD-007", "es", "baja", "Receta tradicional de paella valenciana", "Dominio no deportivo."),
    ("B1-OOD-008", "en", "alta", "How many points is a takedown worth in freestyle wrestling?", "Deporte de combate cercano (lucha)."),
    ("B1-OOD-009", "es", "alta", "¿Cuántos puntos vale una patada a la cabeza en taekwondo?", "Deporte de combate cercano."),
    ("B1-OOD-010", "en", "alta", "What are the dimensions of a sumo dohyo?", "Deporte de combate cercano con vocabulario japones."),
    ("B1-OOD-011", "es", "alta", "¿Qué significa una tarjeta amarilla en el kumite de karate?", "Arte marcial cercano."),
    ("B1-OOD-012", "en", "alta", "How are points scored for a guard pass in Brazilian jiu-jitsu?", "Arte marcial cercano."),
    ("B1-OOD-013", "es", "media", "¿Cuáles son los requisitos para obtener el pasaporte español?", "Vocabulario compartido (pasaporte)."),
    ("B1-OOD-014", "en", "media", "What is the maximum weight for checked baggage on international flights?", "Vocabulario compartido (peso)."),
    ("B1-OOD-015", "es", "baja", "¿Cómo se configura el wifi de un router doméstico?", "Dominio no deportivo."),
]:
    Q(qid, lang, OOD, diff, text, answerable=False, why=O.format(note))

# ---------------------------------------------------------------- 15 ambiguas
M = "Consulta infra-especificada; la interpretacion correcta requiere aclaracion. Candidatas NO verificadas."
for qid, lang, text, cands in [
    ("B1-AMB-001", "es", "¿Cuánto dura?", ["2.4", "Article 6", "A1.6"]),
    ("B1-AMB-002", "es", "¿Cuál es la tolerancia de peso?", ["6.1", "6.3", "6.4.2"]),
    ("B1-AMB-003", "en", "What is the penalty?", []),
    ("B1-AMB-004", "es", "¿Puede continuar en la competición?", ["Article 18.2.1", "Article 18.2.2", "Article 20.1"]),
    ("B1-AMB-005", "es", "¿Cuántos atletas tiene un equipo?", ["2.7.1", "2.7.2"]),
    ("B1-AMB-006", "en", "What colour must it be?", ["C1.9", "C1.11", "B1.12"]),
    ("B1-AMB-007", "es", "¿Qué pasa si no se presenta?", ["6.2.5", "Article 19.1", "3.5"]),
    ("B1-AMB-008", "en", "How many entries are allowed?", ["4.4"]),
    ("B1-AMB-009", "es", "¿Y en cadetes?", []),
    ("B1-AMB-010", "es", "¿Cuándo es el sorteo?", ["5.1", "A1.8", "B1.4"]),
    ("B1-AMB-011", "en", "Is it allowed?", []),
    ("B1-AMB-012", "es", "¿Qué medidas debe tener?", ["8.7", "B1.8", "C1.10"]),
    ("B1-AMB-013", "en", "Who makes the final decision?", []),
    ("B1-AMB-014", "es", "¿Cuántos puntos da?", ["3.2.1", "B1.5", "Article 15"]),
    ("B1-AMB-015", "en", "What happens in golden score?", ["Article 13", "A1.14", "2.7.1"]),
]:
    Q(qid, lang, AMB, "media", text, answerable=False, candidates=cands, why=M)


# ---------------------------------------------------------------- build
def norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def norm_label(s):
    s = re.sub(r"\s*\.\s*", ".", (s or "").strip())
    return re.sub(r"\s+", " ", s).rstrip(".")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def resolve_anchor(a, pages):
    pps = pages.get(a["page"], [])
    out = dict(a)
    if not pps:
        out.update(status="PENDIENTE", reason="PAGINA_INEXISTENTE", passage_ids=[], relation=None)
        return out
    text = norm_ws(pps[0]["text_original"])
    if norm_ws(a["snippet"]) not in text:
        out.update(status="PENDIENTE", reason="FRAGMENTO_NO_LOCALIZADO_LITERALMENTE", passage_ids=[], relation=None)
        return out
    by_art = [p["passage_id"] for p in pps if norm_label(p.get("article_id")) == norm_label(a["article"])]
    if by_art:
        out.update(status="VERIFICADA_TEXTUALMENTE", reason=None, passage_ids=sorted(by_art), relation="ARTICULO_EN_METADATOS")
    else:
        out.update(status="VERIFICADA_TEXTUALMENTE_ARTICULO_PENDIENTE",
                   reason="ARTICULO_NO_FIGURA_EN_METADATOS_DE_LA_PAGINA (continuacion o metadato inexacto)",
                   passage_ids=sorted(p["passage_id"] for p in pps), relation="PAGINA")
    out["snippet_sha256"] = sha(norm_ws(a["snippet"]))
    return out


def tokens(s):
    return set(re.findall(r"\w{3,}", s.lower()))


def build(passages, corpus_raw):
    pages = defaultdict(list)
    for p in passages:
        pages[p["pdf_page_index"]].append(p)
    errors, records = [], []
    ids = Counter(i["id"] for i in ITEMS)
    for k, v in ids.items():
        if v > 1:
            errors.append(f"ID duplicado {k}")
    # union of groups sharing an identical anchor (semantic duplicates)
    parent = {i["group"]: i["group"] for i in ITEMS}

    def find(g):
        while parent[g] != g:
            g = parent[g]
        return g
    seen_anchor = {}
    for it in ITEMS:
        for a in it["anchors"]:
            key = (a["page"], norm_ws(a["snippet"]))
            if key in seen_anchor and find(seen_anchor[key]) != find(it["group"]):
                parent[find(it["group"])] = find(seen_anchor[key])
            seen_anchor.setdefault(key, it["group"])
    for it in ITEMS:
        anchors = [resolve_anchor(a, pages) for a in it["anchors"]]
        xrefs = [resolve_anchor(a, pages) for a in it["xrefs"]]
        excs = [resolve_anchor(a, pages) for a in it["exceptions"]]
        allr = anchors + xrefs + excs
        pend = [r for r in allr if r["status"] != "VERIFICADA_TEXTUALMENTE"]
        if it["category"] == AMB:
            ann = "PENDIENTE"
        elif it["category"] == OOD:
            ann = "VERIFICADA_SIN_EVIDENCIA_ESPERADA"
        else:
            ann = "PENDIENTE" if any(r["status"] == "PENDIENTE" for r in allr) else (
                "VERIFICADA_TEXTUALMENTE_CON_ARTICULO_PENDIENTE" if pend else "VERIFICADA_TEXTUALMENTE")
        for r in allr:
            if r["status"] == "PENDIENTE":
                errors.append(f"{it['id']}: ancla no verificada p{r['page']} '{r['snippet'][:50]}' ({r['reason']})")
        records.append({
            "id": it["id"], "benchmark_version": VERSION, "text": it["text"], "language": it["language"],
            "category": it["category"], "difficulty": it["difficulty"],
            "answerable": ("AMBIGUA_REQUIERE_ACLARACION" if it["category"] == AMB else it["answerable"]),
            "expected_articles": ("PENDIENTE" if it["category"] == AMB else sorted({norm_label(a["article"]) for a in it["anchors"]})),
            "expected_passage_ids": sorted({pid for r in anchors for pid in r["passage_ids"]}),
            "relevant_original_passages": [{"page": r["page"], "article": r["article"], "passage_ids": r["passage_ids"],
                                            "relation": r["relation"], "text_fragment": r["snippet"]} for r in anchors],
            "minimum_evidence": anchors, "mandatory_cross_refs": xrefs, "exceptions_to_preserve": excs,
            "candidate_articles": it["candidates"] if it["category"] == AMB else [],
            "justification": it["justification"], "semantic_group": find(it["group"]),
            "annotation_source": SOURCE, "annotation_status": ann,
            "human_review_status": HUMAN, "certified_by_referees": False,
        })
    # stratified deterministic split by semantic group
    groups = defaultdict(list)
    for r in records:
        groups[r["semantic_group"]].append(r)
    by_cat = defaultdict(list)
    for g, rs in groups.items():
        by_cat[rs[0]["category"]].append(g)
    split_of = {}
    for cat, gs in sorted(by_cat.items()):
        gs.sort(key=lambda g: sha(VERSION + g))
        n = len(gs)
        cut1 = round(n * SPLIT_RATIOS[0][1])
        cut2 = cut1 + round(n * SPLIT_RATIOS[1][1])
        for i, g in enumerate(gs):
            split_of[g] = "dev" if i < cut1 else ("validation" if i < cut2 else "test")
    for r in records:
        r["split"] = split_of[r["semantic_group"]]
    # near-duplicate check across splits (same language)
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            if a["split"] != b["split"] and a["language"] == b["language"]:
                ta, tb = tokens(a["text"]), tokens(b["text"])
                if ta and tb and len(ta & tb) / len(ta | tb) >= 0.8:
                    errors.append(f"posible duplicado semantico entre splits: {a['id']} / {b['id']}")
            if a["split"] != b["split"] and a["semantic_group"] == b["semantic_group"]:
                errors.append(f"grupo semantico repartido entre splits: {a['semantic_group']}")
    records.sort(key=lambda r: r["id"])
    counts = {
        "total": len(records),
        "by_category": dict(sorted(Counter(r["category"] for r in records).items())),
        "by_language": dict(sorted(Counter(r["language"] for r in records).items())),
        "by_split": dict(sorted(Counter(r["split"] for r in records).items())),
        "by_split_category": {s: dict(sorted(Counter(r["category"] for r in records if r["split"] == s).items())) for s in ("dev", "validation", "test")},
        "by_annotation_status": dict(sorted(Counter(r["annotation_status"] for r in records).items())),
        "by_human_review_status": dict(sorted(Counter(r["human_review_status"] for r in records).items())),
        "semantic_groups": len(groups),
        "cross_lingual_pairs": sum(1 for g, rs in groups.items() if len({r["language"] for r in rs}) > 1),
        "anchors_total": sum(len(r["minimum_evidence"]) + len(r["mandatory_cross_refs"]) + len(r["exceptions_to_preserve"]) for r in records),
        "items_with_cross_refs": sum(1 for r in records if r["mandatory_cross_refs"]),
        "items_with_exceptions": sum(1 for r in records if r["exceptions_to_preserve"]),
    }
    manifest = {
        "benchmark_version": VERSION, "corpus": CORPUS_REL,
        "corpus_file_sha256": hashlib.sha256(corpus_raw).hexdigest(),
        "source_pdf_sha256": sorted({p.get("source_sha256") for p in passages}),
        "annotation_policy": {
            "source": SOURCE, "human_review_status": HUMAN, "certified_by_referees": False,
            "anchors": "fragmentos literales verificados automaticamente contra el texto de la pagina (espacios normalizados)",
            "unverifiable": "marcado PENDIENTE; ningun articulo ni respuesta normativa inferido",
            "normative_answers": "no incluidas",
        },
        "split_policy": {"method": "estratificado por categoria, por grupo semantico, orden sha256(version+grupo)",
                         "ratios": dict(SPLIT_RATIOS),
                         "test_restriction": "TEST RESERVADO: no usar para ajustar reglas, umbrales, prompts ni anclas"},
        "counts": counts, "build_errors": errors,
        "build_command": "python scripts/build_benchmark_v1.py",
    }
    files = {"benchmark_v1.jsonl": "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records)}
    for s in ("dev", "validation", "test"):
        files[f"splits/{s}.jsonl"] = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records if r["split"] == s)
    files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    files["hashes.json"] = json.dumps({k: sha(v) for k, v in sorted(files.items())}, indent=2, sort_keys=True) + "\n"
    return files, records, errors, counts


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    with open(os.path.join(ROOT, CORPUS_REL), "rb") as fh:
        raw = fh.read()
    passages = json.loads(raw.decode("utf-8"))
    files, records, errors, counts = build(passages, raw)
    if a.check:
        diffs = [n for n, c in files.items() if not os.path.exists(os.path.join(a.out, n))
                 or open(os.path.join(a.out, n), encoding="utf-8").read().replace("\r\n", "\n") != c]
        print("REPRODUCIBLE" if not diffs else f"NO REPRODUCIBLE: {diffs}")
        return 0 if not diffs else 1
    if os.path.isdir(a.out) and os.listdir(a.out) and not a.overwrite:
        print(f"ERROR: {a.out} ya existe; use --check o --overwrite", file=sys.stderr)
        return 2
    for n, c in files.items():
        fp = os.path.join(a.out, n)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(c)
    print(json.dumps(counts, ensure_ascii=False, indent=1))
    for e in errors:
        print("ERROR:", e)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
