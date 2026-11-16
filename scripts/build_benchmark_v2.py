#!/usr/bin/env python3
"""Fase 10.1 - benchmark_v2: benchmark independiente para evaluacion semantica.

Principios (ver docs/audits/FASE_10_EVALUACION_SEMANTICA.md, seccion 2):
  * Consultas redactadas de nuevo (no derivadas de benchmark_v1); se verifica el
    solapamiento lexico con v1 y se registra en el manifiesto.
  * Toda evidencia esperada (minimum_evidence, wrong_scope_distractors,
    mandatory_cross_refs, exceptions_to_preserve) es un fragmento LITERAL del
    corpus SOR verificado automaticamente contra el texto de su pagina.
  * Las etiquetas automaticas (auto_labels) se separan de las humanas
    (human_labels = null). Ningun item esta certificado: review_status =
    PENDING_EXPERT_REVIEW hasta que un arbitro lo revise (ver review/).
  * No contiene respuestas normativas redactadas: solo comportamiento esperado
    y evidencia literal.
  * Particion 'test_sealed' por grupo semantico: no debe usarse para ajustar
    reglas, umbrales, prompts, modelos ni anclas. Su hash queda en el manifiesto.
  * Para los items INSUFICIENTE se registra una sonda de ausencia (regex sobre el
    corpus) con su numero de coincidencias, para que la etiqueta sea auditable.

Solo stdlib. Lectura del corpus; no lo modifica.
Uso:  python scripts/build_benchmark_v2.py [--overwrite | --check]
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

VERSION = "benchmark_v2.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_REL = "data/processed/rebuild_2026_08_corrected/passages_candidate.json"
V1_REL = "data/eval/benchmark_v1/benchmark_v1.jsonl"
OUT_REL = "data/eval/benchmark_v2"
SPLIT_RATIOS = (("dev", 0.4), ("test_sealed", 0.6))
REVIEW = "PENDING_EXPERT_REVIEW"
LABELER = "AUTOMATICA_ASISTIDA_IA_ANCLADA_A_TEXTO_LITERAL"
V1_MAX_JACCARD = 0.7  # por encima: se considera reutilizacion de una consulta v1

# comportamiento esperado
RESP, ABS_INS, ABS_OOD, ACL = "RESPONDER", "ABSTENER_INSUFICIENCIA", "ABSTENER_FUERA_DE_DOMINIO", "SOLICITAR_ACLARACION"
CATS = {
    "DIRECTA": RESP, "AMBITO_DISTRACTOR": RESP, "DISTINCION_CATEGORIA": RESP, "EXCEPCION": RESP,
    "REFERENCIA_CRUZADA": RESP, "MULTI_ARTICULO": RESP, "MULTILINGUE": RESP,
    "INSUFICIENTE": ABS_INS, "OOD": ABS_OOD, "AMBIGUA": ACL, "INCOMPLETA": ACL,
}
JUST = {
    "DIRECTA": "Regla localizable en un pasaje; la evidencia minima es el fragmento literal indicado.",
    "AMBITO_DISTRACTOR": ("Existe una regla literal parecida en OTRO ambito (otra modalidad, grupo de edad o tipo de "
                          "evento). Responder con el distractor es un error de ambito aunque la cita sea literal."),
    "DISTINCION_CATEGORIA": "La respuesta depende de distinguir la categoria (peso, edad, grupo) correcta dentro de la misma regla.",
    "EXCEPCION": "La regla incluye una excepcion o condicion que debe conservarse en la evidencia y en la respuesta.",
    "REFERENCIA_CRUZADA": "La regla remite literalmente a otra seccion cuya evidencia tambien es necesaria.",
    "MULTI_ARTICULO": "Requiere evidencia de dos o mas articulos; uno solo es insuficiente.",
    "MULTILINGUE": "Consulta en idioma distinto de ES/EN sobre una regla localizable; mide robustez de idioma.",
    "INSUFICIENTE": ("Consulta del dominio judo/IJF cuya respuesta no esta en el SOR (sonda de ausencia registrada). "
                     "Lo correcto es abstenerse por insuficiencia, no responder con texto proximo."),
    "OOD": "Fuera del dominio del SOR; lo correcto es abstenerse.",
    "AMBIGUA": ("Varias reglas del SOR responden segun una dimension no especificada (ambito, grupo, evento). "
                "Lo correcto es pedir aclaracion sobre esa dimension."),
    "INCOMPLETA": ("La consulta carece del objeto o depende de un contexto previo inexistente; no hay candidatas "
                   "identificables. Lo correcto es pedir que se complete la consulta."),
}


def A(page, article, snippet, note=None):
    d = {"page": page, "article": article, "snippet": snippet}
    if note:
        d["scope_note"] = note
    return d


ITEMS = []


def Q(qid, lang, cat, text, ev=(), distract=(), xrefs=(), exc=(), scope=None, group=None,
      dimension=None, candidates=(), clarification=None, absence=None, difficulty="media"):
    ITEMS.append(dict(id=qid, language=lang, category=cat, text=text, ev=list(ev), distract=list(distract),
                      xrefs=list(xrefs), exc=list(exc), scope=scope, group=group or qid, dimension=dimension,
                      candidates=list(candidates), clarification=clarification, absence=absence,
                      difficulty=difficulty))


# ---------------------------------------------------------------- evidencia comun
DUR_SEN = A(152, "Article 6", "Senior men and women/mixed teams: 4 minutes real contest time", "competicion general seniors")
DUR_CAD = A(152, "Article 6", "Cadet under 18 men and women/mixed teams: 4 minutes real contest time", "competicion general cadetes")
DUR_V16 = A(103, "A1.6", "M1/F1 to M6/F6: three (3) minutes", "veteranos M1-M6")
DUR_V7 = A(103, "A1.6", "M7/F7 and over: two and a half (2.5) minutes", "veteranos M7+")
DRAW_WJT = A(71, "5.1", "the draw will take place at 14:00 local time the day before the competition", "WC/Masters/GS/GP")
DRAW_VET = A(105, "A1.8", "will take place at 19.00 hours on the day before the competition", "veteranos")
SEED_WJT = A(71, "5.2", "up to a maximum of the top eight (8) athletes among the entered athletes in each weight category will be seeded based on their IJF WRL position", "eventos WJT")
SEED_OG = A(72, "5.3", "based on their IJF Senior WRL of the Olympic qualification period", "Juegos Olimpicos")
SEED_VET = A(105, "A1.9", "In the veterans’ event, there is no seeding.", "veteranos")
SEED_KATA = A(110, "B1.4", "The top six (6) pairs on the ranking list will be considered seeded", "kata")
RW_INDIV = A(79, "6.3", "For IJF World Judo Tour (WJT) events the random weigh-in will open one hour before the start of the competition each day.", "eventos individuales WJT")
RW_MIX = A(79, "6.3", "there will be no random weigh-in for IJF Mixed Team events", "equipos mixtos")
RW_VET = A(105, "A1.10", "There is no random weigh-in for veterans.", "veteranos")
JG_VET = A(105, "A1.11", "All athletes MUST compete wearing a white or blue IJF approved judogi and belt", "veteranos")
JG_KATA = A(113, "B1.12", "Participants must wear a white judogi, a black belt and a backnumber", "kata")
JG_KATA_U18 = A(113, "B1.12", "A green, blue or brown belt without an IJF label is authorised for the U18 age group.", "kata U18")
AREA_KATA_WC = A(112, "B1.8", "The competition area dimension is 10 m x 10 m for world championships", "kata campeonatos del mundo")
AREA_KATA_OTH = A(112, "B1.8", "or 8 m x 8 m for other events", "kata otros eventos")
AREA_SHIAI = A(96, "8.7", "for IJF events shall be a minimum of 8 m x 8 m and a maximum of 10 m x 10 m", "area de combate (shiai)")
MED_VET1 = A(106, "A1.15", "One athlete - no medal will be awarded", "veteranos")
MED_KATA = A(113, "B1.9", "Medals will be awarded following a performance by a pair according to standings regardless the number of pairs.", "kata")
AGE_VET = A(103, "A1.4", "Meeting the entrance criteria of a minimum of 30 years of age", "veteranos")
AGE_ATH = A(35, "2.3", "The lower age limit for all IJF competitions is 15 years (calendar year).", "atletas competicion IJF")
AGE_KATA = A(109, "B1.1", "Participants must be a minimum of 15 years of age in the calendar year of the competition.", "kata")
AGE_REF_INT = A(135, "Article 1", "The ages limits for IJF international referee examination are 30-50 years old", "examen arbitro internacional")
AGE_REF_CONT = A(135, "Article 1", "The ages limits for continental referee examinations are 25-45 years old", "examen arbitro continental")
TOL_CAD = A(75, "6.1", "to compensate an additional 0.2 kg will be allowed", "cadetes")
TOL_JS = A(75, "6.1", "there is no additional weight tolerance", "juniors y seniors individual")
TOL_MIX = A(81, "6.4.2", "A +5% tolerance applies only to the minus weight categories.", "equipo mixto tras individual")
TOL_MIX_PLUS = A(81, "6.4.2", "No tolerance applies to the plus weight categories because they do not have an upper weight limit", "equipo mixto categorias +")
TEAM_MIX = A(42, "2.7.1", "Each mixed team must consist of six (6) athletes (3 women and 3 men)", "equipo mixto")
TEAM_MIX_RES = A(42, "2.7.1", "has the possibility to have up to six (6) reserves (3 women and 3 men)", "equipo mixto")
TEAM_FM = A(45, "2.7.2", "Each team will consist of up to five (5) athletes", "equipos femeninos/masculinos")
TEAM_FM_RES = A(45, "2.7.2", "has the possibility to have up to five (5) reserves", "equipos femeninos/masculinos")
WRL_SEN = A(52, "3.2.1", "Athletes can earn points for the IJF Seniors WRL by competing in IJF World Judo Tour (WJT) events for senior, World Championships Juniors", "WRL seniors")
WRL_JUN = A(53, "3.2.2", "Athletes can earn points for the IJF Juniors WRL by competing in Continental Cups Juniors", "WRL juniors")
WRL_CAD = A(54, "3.2.3", "Athletes can earn points for the IJF Cadets WRL by competing in Continental Cups Cadets", "WRL cadetes")
WRL_KATA = A(110, "B1.5", "A pair can earn points in the following events: Continental Open, Continental Championships, Kata World Series (KWS) and World Kata Championships.", "ranking kata")
INJ_KATA = A(113, "B1.11", "the kata performance will be stopped", "kata")
INJ_SHIAI = A(198, "Article 20.3.2", "A minor injury may be treated by the athlete himself.", "combate (shiai)")

# ---------------------------------------------------------------- AMBITO_DISTRACTOR
G = "AMBITO_DISTRACTOR"
Q("B2-SCO-001", "en", G, "How long does a contest last for a veteran in the M7 age division?", [DUR_V7], [DUR_SEN, DUR_V16], scope="veteranos M7", group="g-dur")
Q("B2-SCO-002", "es", G, "¿Cuánto dura un combate de cadetes en una competición de la IJF?", [DUR_CAD], [DUR_V16], scope="cadetes competicion IJF", group="g-dur")
Q("B2-SCO-003", "en", G, "The day before a Masters event, at what hour is the draw scheduled?", [DRAW_WJT], [DRAW_VET], scope="Grand Slam", group="g-draw")
Q("B2-SCO-004", "es", G, "¿A qué hora se hace el sorteo en un campeonato de veteranos?", [DRAW_VET], [DRAW_WJT], scope="veteranos", group="g-draw")
Q("B2-SCO-005", "en", G, "How many athletes per weight category are seeded at a Grand Prix?", [SEED_WJT], [SEED_VET, SEED_KATA], scope="Grand Prix", group="g-seed")
Q("B2-SCO-006", "es", G, "¿Hay cabezas de serie en los campeonatos de veteranos?", [SEED_VET], [SEED_WJT], scope="veteranos", group="g-seed")
Q("B2-SCO-007", "en", G, "In kata competitions, which pairs are treated as seeds?", [SEED_KATA], [SEED_WJT], scope="kata", group="g-seed")
Q("B2-SCO-008", "es", G, "¿En qué ranking se basa el sembrado de los Juegos Olímpicos?", [SEED_OG], [SEED_WJT], scope="Juegos Olimpicos", group="g-seed")
Q("B2-SCO-009", "en", G, "Is there a random weigh-in at IJF mixed team events?", [RW_MIX], [RW_INDIV], scope="equipos mixtos", group="g-rw")
Q("B2-SCO-010", "es", G, "¿Se hace pesaje aleatorio a los veteranos?", [RW_VET], [RW_INDIV], scope="veteranos", group="g-rw")
Q("B2-SCO-011", "en", G, "What colour of judogi must veteran athletes wear?", [JG_VET], [JG_KATA], scope="veteranos", group="g-jg")
Q("B2-SCO-012", "es", G, "¿De qué color tiene que ser el judogi en una competición de kata?", [JG_KATA], [JG_VET], scope="kata", group="g-jg")
Q("B2-SCO-013", "en", G, "What are the dimensions of the competition area at a World Kata Championships?", [AREA_KATA_WC], [AREA_KATA_OTH, AREA_SHIAI], scope="kata mundial", group="g-area")
Q("B2-SCO-014", "es", G, "¿Qué medidas tiene el área de competición de kata en un evento que no es campeonato del mundo?", [AREA_KATA_OTH], [AREA_KATA_WC, AREA_SHIAI], scope="kata otros eventos", group="g-area")
Q("B2-SCO-015", "en", G, "Is a medal awarded when only one athlete competes in a veterans category?", [MED_VET1], [MED_KATA], scope="veteranos", group="g-med")
Q("B2-SCO-016", "es", G, "En kata, ¿se entregan medallas aunque participen pocas parejas?", [MED_KATA], [MED_VET1], scope="kata", group="g-med")
Q("B2-SCO-017", "en", G, "What is the minimum age to take part in veterans competitions?", [AGE_VET], [AGE_ATH, AGE_KATA], scope="veteranos", group="g-age")
Q("B2-SCO-018", "es", G, "¿Qué límites de edad hay para presentarse al examen de árbitro internacional de la IJF?", [AGE_REF_INT], [AGE_REF_CONT, AGE_ATH], scope="examen arbitro internacional", group="g-age")
Q("B2-SCO-019", "es", G, "¿Qué tolerancia de peso tienen los cadetes en el pesaje oficial?", [TOL_CAD], [TOL_MIX, TOL_JS], scope="cadetes", group="g-tol")
Q("B2-SCO-020", "en", G, "Do senior athletes get any weight tolerance at the official weigh-in of an individual event?", [TOL_JS], [TOL_MIX, TOL_CAD], scope="seniors individual", group="g-tol")
Q("B2-SCO-021", "en", G, "How many athletes can a female team have in a team event?", [TEAM_FM], [TEAM_MIX], scope="equipos femeninos", group="g-team")
Q("B2-SCO-022", "es", G, "¿Cuántos reservas puede tener un equipo mixto?", [TEAM_MIX_RES], [TEAM_FM_RES], scope="equipo mixto", group="g-team")
Q("B2-SCO-023", "en", G, "Which events give points for the IJF Juniors World Ranking List?", [WRL_JUN], [WRL_SEN, WRL_CAD], scope="WRL juniors", group="g-wrl")
Q("B2-SCO-024", "es", G, "¿En qué eventos puede sumar puntos de ranking una pareja de kata?", [WRL_KATA], [WRL_SEN], scope="ranking kata", group="g-wrl")
Q("B2-SCO-025", "en", G, "What happens if an athlete suffers a minor injury during a kata performance?", [INJ_KATA], [INJ_SHIAI], scope="kata", group="g-inj")
Q("B2-SCO-026", "es", G, "¿Puede un atleta tratarse a sí mismo una lesión leve durante un combate?", [INJ_SHIAI], [INJ_KATA], scope="combate", group="g-inj")
Q("B2-SCO-027", "en", G, "In a veterans category with four entries, which competition system is used?",
  [A(105, "A1.13", "3, 4, 5 entries: round robin", "veteranos")],
  [A(105, "A1.13", "6 and more entries: double repechage", "veteranos >=6"), A(42, "2.6.2", "the organiser can choose the competition system used", "otros eventos")],
  scope="veteranos 4 inscritos", group="g-sys")
Q("B2-SCO-028", "es", G, "Si solo hay dos participantes en una categoría de veteranos, ¿cómo se decide el ganador?",
  [A(105, "A1.13", "2 entries: best of 2 contests, if 1-1 the third contest will decide", "veteranos")],
  [A(104, "A1.7", "The best of three contests between the two (2) athletes, if the result is 2-0 then the third contest will not be fought.", "pool de dos tras fallo de combinacion")],
  scope="veteranos 2 inscritos", group="g-sys")
Q("B2-SCO-029", "en", G, "By what time must the mixed team composition be confirmed when the event follows an individual competition?",
  [A(43, "2.7.1", "by 13:00 local time on the day prior to the mixed team competition", "equipo mixto")], [DRAW_WJT], scope="equipo mixto", group="g-mixconf")
Q("B2-SCO-030", "en", G, "Which kata can a U21 pair perform?",
  [A(109, "B1.2", "U21 group: A pair can do the following kata: nage-no-kata, katame-no-kata and ju-no-kata.", "kata U21")],
  [A(109, "B1.2", "Seniors group: A pair can do the following kata: nage-no-kata, katame-no-kata, ju-no-kata, Kodokan goshin-jutsu", "kata seniors")],
  scope="kata U21", group="g-kata")

# ---------------------------------------------------------------- DISTINCION_CATEGORIA
G = "DISTINCION_CATEGORIA"
Q("B2-CAT-001", "es", G, "¿Qué longitud mínima debe tener la falda de la chaqueta para un atleta de -66 kg?",
  [A(124, "C1.10", "All athletes -73 kg*: a minimum of 20 cm")], [A(124, "C1.10", "All athletes +73 kg*: a minimum of 25 cm", "+73 kg")], scope="-66 kg")
Q("B2-CAT-002", "en", G, "What is the maximum size of the manufacturer's logo on the belt?",
  [A(119, "C1.3", "9 cm2 on the belt")], [A(119, "C1.3", "It must be a maximum of 30 cm2 on the jacket and trousers", "chaqueta y pantalon")], scope="cinturon")
Q("B2-CAT-003", "es", G, "¿Puede una pareja U18 de kata usar un cinturón verde?", [JG_KATA_U18], [JG_KATA], scope="kata U18")
Q("B2-CAT-004", "en", G, "What minimum grade must senior kata participants hold?",
  [A(109, "B1.1", "They shall have a minimum of 1st dan for seniors age group.")], [A(109, "B1.1", "shall have a minimum of 1st kyu", "U21")], scope="kata seniors")
Q("B2-CAT-005", "en", G, "Which individual categories make up the men's -73 kg category of the Olympic mixed team?",
  [A(34, "2.2.2", "-73 kg Men (60 kg, 66 kg, 73 kg*)")], [A(34, "2.2.2", "-73 kg Men Up to and including 73.0 kg", "equipo mixto general")], scope="mixto olimpico")
Q("B2-CAT-006", "es", G, "En el equipo mixto, ¿se aplica la tolerancia del 5% a las categorías de más (+)?", [TOL_MIX_PLUS], [TOL_CAD], scope="mixto categorias +")
Q("B2-CAT-007", "en", G, "At a Grand Prix Cadets, how many athletes per country and weight category can obtain Cadets WRL points?",
  [A(55, "3.2.3", "At Grand Prix Cadets events only the two (2) best domestic athletes per weight category can obtain points")],
  [A(55, "3.2.3", "At World Championships Cadets only the ten (10) best domestic male and ten (10) best domestic female athletes", "Campeonato del Mundo cadetes")],
  scope="GP cadetes")

# ---------------------------------------------------------------- EXCEPCION
G = "EXCEPCION"
Q("B2-EXC-001", "en", G, "Can the mixed team list be updated after it has been confirmed?",
  [A(43, "2.7.1", "the list can be updated up to one (1) hour after the end of the final block only for the athletes competing on the last day")])
Q("B2-EXC-002", "es", G, "¿Se da kiken-gachi si el rival no puede seguir por haber perdido una lentilla?",
  [A(195, "Article 19.2", "inability to continue after losing a contact lens")])
Q("B2-EXC-003", "en", G, "Can the IJF enter an athlete who is not entered by a national federation?",
  [A(61, "4.2", "Only entries from member national judo federations will be accepted.")],
  exc=[A(61, "4.2", "the IJF can, to protect an athlete’s career, inscribe an athlete into an IJF event")])
Q("B2-EXC-004", "es", G, "Si los médicos discrepan en el área de competición, ¿quién tiene la última palabra?",
  [A(201, "E1.1.1", "In case of a dispute between them, the delegation doctor will take the decision")],
  exc=[A(201, "E1.1.1", "the International Judo Federation (IJF) Medical Commissioner has the final say")])
Q("B2-EXC-005", "en", G, "May an athlete compete with the head covered?",
  [A(202, "E1.3", "The head may not be covered except for bandaging of a medical nature")])
Q("B2-EXC-006", "es", G, "Quien compite en individual y en mixto, ¿puede dar el peso siempre con el margen del 5%?",
  [A(82, "6.4.2", "must be within the weight limit of their mixed team category (without the +5% tolerance) at least once during the two competitions")], [TOL_MIX])
Q("B2-EXC-007", "en", G, "Can category combining be used in a veterans category with four entrants?",
  [A(104, "A1.7", "Category combining may only be applied to categories where there are less than three entrants.")])
Q("B2-EXC-008", "es", G, "¿Se pueden poner logotipos del evento en el área de combate del tatami?",
  [A(97, "8.7", "can only be placed on the safety area, never on the contest area")])
Q("B2-EXC-009", "en", G, "Does an athlete who skips the medal ceremony keep the medal?",
  [A(98, "8.10", "Any athlete who is absent from the awards ceremony without a good reason may forfeit the medal and prize money.")])
Q("B2-EXC-010", "es", G, "¿Hasta qué edad puede arbitrar un árbitro en el World Judo Tour?",
  [A(135, "Article 1", "must be a maximum of 55 years old during that Olympic cycle")], [AGE_REF_INT])

# ---------------------------------------------------------------- REFERENCIA_CRUZADA
G = "REFERENCIA_CRUZADA"
Q("B2-REF-001", "en", G, "Which rules must the judogi of veterans conform to?",
  [A(105, "A1.11", "The judogi and belt must conform to the rules in Appendix C.")],
  xrefs=[A(115, "C1.1", "Athletes participating in International Judo Federation (IJF) official events should comply with the IJF Judogi regulations.")])
Q("B2-REF-002", "es", G, "¿Qué reglas de nacionalidad se aplican a las parejas de kata?",
  [A(109, "B1.1", "National federations must follow IJF nationality rules")],
  xrefs=[A(19, "1.7.1", "An athlete who has represented one country in")])
Q("B2-REF-003", "en", G, "Where are the weigh-in rules for female and male team events?",
  [A(45, "2.7.2", "Weigh-in rules can be found in Section 6.")],
  xrefs=[A(75, "6.1", "Athletes competing in junior and senior events must be within the weight limits of a category in which they are inscribed")])
Q("B2-REF-004", "es", G, "¿Qué límites de peso deben cumplir juniors y seniors en el pesaje individual?",
  [A(75, "6.1", "must be within the weight limits of a category in which they are inscribed")],
  xrefs=[A(33, "2.2.1", "Weight Categories for Individual Competitions")])
Q("B2-REF-005", "en", G, "Which weight categories are used in veterans competitions?",
  [A(103, "A1.5", "The weight categories are the same as those for senior men and women.")],
  xrefs=[A(33, "2.2.1", "Weight Categories for Individual Competitions")])

# ---------------------------------------------------------------- MULTI_ARTICULO
G = "MULTI_ARTICULO"
Q("B2-MUL-001", "en", G, "Compare the contest duration for a senior contest and for an M8 veteran contest.", [DUR_SEN, DUR_V7], difficulty="alta")
Q("B2-MUL-002", "es", G, "¿En qué se diferencia la hora del sorteo de un Grand Slam y la de un campeonato de veteranos?", [DRAW_WJT, DRAW_VET], difficulty="alta")
Q("B2-MUL-003", "en", G, "How do seeding rules differ between Grand Prix events and veterans events?", [SEED_WJT, SEED_VET], difficulty="alta")
Q("B2-MUL-004", "es", G, "Compara cuántos atletas forman un equipo mixto y un equipo femenino.", [TEAM_MIX, TEAM_FM], difficulty="alta")

# ---------------------------------------------------------------- DIRECTA
G = "DIRECTA"
Q("B2-DIR-001", "en", G, "How far back from the athletes' starting line does the referee stand at the start?",
  [A(153, "Article 9", "2 m back from the line from which the athletes start")])
Q("B2-DIR-002", "es", G, "¿Qué ocurre cuando un atleta consigue un segundo waza-ari?",
  [A(172, "Article 16", "Should one athlete gain a second waza-ari in the contest")])
Q("B2-DIR-003", "en", G, "How many entrances to the field of play are required?",
  [A(96, "8.7", "A minimum of three entrances to the field of play are needed")])
Q("B2-DIR-004", "es", G, "¿Es obligatorio un sistema de videoarbitraje en las competiciones sancionadas por la IJF?",
  [A(97, "8.7", "A certified Video Replay System is mandatory for all IJF-sanctioned competitions.")])
Q("B2-DIR-005", "en", G, "What spacing is required between the world champion stars on the judogi?",
  [A(129, "C1.14.1", "There should be a space of 0.5 cm - 2 cm between each star.")])
Q("B2-DIR-006", "es", G, "¿Cuánto descanso tiene un atleta entre combates?",
  [A(152, "Article 6", "Any athlete is entitled to 10 minutes rest between contests.")])
Q("B2-DIR-007", "en", G, "Must athletes wear shoes at the medal ceremony?",
  [A(98, "8.10", "Athletes must attend the medal ceremony barefoot")])
Q("B2-DIR-008", "es", G, "¿Puede el árbitro llevar objetos religiosos mientras arbitra?",
  [A(136, "Article 2", "without any head coverings, religious objects, or garish jewellery")])
Q("B2-DIR-009", "en", G, "How must long hair be tied during competition?",
  [A(202, "E1.3", "Hair shall be tied by means of a hair band made of rubber or similar material")])
Q("B2-DIR-010", "es", G, "¿Cómo se solicita autorización para llevar un dispositivo médico durante la competición?",
  [A(202, "E1.4", "must be submitted in writing for the approval of the IJF")])
Q("B2-DIR-011", "en", G, "How long before the first contest must an athlete arrive at the random weigh-in?",
  [A(79, "6.3", "30 minutes or 6 contests before the athlete’s first contest at the latest")])
Q("B2-DIR-012", "es", G, "¿Cuántos atletas como máximo se pueden inscribir en un equipo mixto?",
  [A(42, "2.7.1", "A maximum of 12 athletes can be entered")])
Q("B2-DIR-013", "en", G, "In a kata event with twelve pairs, into how many groups are the pairs divided?",
  [A(111, "B1.6", "Kata will be divided into two (2) groups for kata with 17 pairs or less")])
Q("B2-DIR-014", "es", G, "Si dos juniors empatan a puntos en el ranking mundial, ¿cuál es el primer criterio de desempate?",
  [A(54, "3.2.2", "The highest sum of the current points from all World Championships Juniors.")])
Q("B2-DIR-015", "en", G, "On which side of the field of play is the awarding ceremony area set up?",
  [A(98, "8.10", "should be set up on the same side of the field of play as the athlete entry")])
Q("B2-DIR-016", "es", G, "¿Qué temperatura debe mantenerse en el pabellón de competición?",
  [A(93, None, "constant temperature of between 18 – 22°C")])
Q("B2-DIR-017", "en", G, "What percentage of prize money must athletes give to their coach?",
  [A(98, "8.10", "responsible to give 20% to their coach")])
Q("B2-DIR-018", "es", G, "¿Qué debe hacer el árbitro si un atleta recibe un fuerte impacto en la cabeza?",
  [A(197, "Article 20.2", "The referee shall call the doctor inside the contest area, to attend to an athlete who has received a severe impact to the head")])

# ---------------------------------------------------------------- MULTILINGUE (fr / pt)
G = "MULTILINGUE"
Q("B2-MLG-001", "fr", G, "Combien de temps dure un combat chez les cadets lors d'une compétition de l'IJF ?", [DUR_CAD], [DUR_V16])
Q("B2-MLG-002", "pt", G, "Quantos atletas compõem uma equipa mista?", [TEAM_MIX], [TEAM_FM])
Q("B2-MLG-003", "fr", G, "Les vétérans sont-ils soumis à une pesée aléatoire ?", [RW_VET], [RW_INDIV])
Q("B2-MLG-004", "pt", G, "A que horas é o sorteio no campeonato de veteranos?", [DRAW_VET], [DRAW_WJT])

# ---------------------------------------------------------------- INSUFICIENTE (en dominio, sin respuesta en el SOR)
G = "INSUFICIENTE"
Q("B2-INS-001", "en", G, "How many contests may a referee officiate per day at a Grand Slam?", absence=r"contests? per day|per day.{0,40}referee")
Q("B2-INS-002", "es", G, "¿Cuántos puntos del ranking mundial otorga un campeonato de veteranos?", absence=r"veteran.{0,40}(WRL|ranking list)|(WRL|ranking list).{0,40}veteran")
Q("B2-INS-003", "en", G, "What is the daily allowance paid to international referees?", absence=r"salary|per diem|daily allowance")
Q("B2-INS-004", "es", G, "¿Cuántos videoárbitros se requieren por cada tatami?", absence=r"video.{0,60}(per|each) (mat|tatami|contest area)")
Q("B2-INS-005", "en", G, "What doping control procedure applies to kata competitions?", absence=r"kata.{0,80}doping|doping.{0,80}kata")
Q("B2-INS-006", "es", G, "¿Cuál es el importe de la cuota de inscripción por atleta en un Grand Prix?",
  distract=[A(101, None, "Pay the appropriate entry fees in full before the deadline set in the event outlines.", "obligacion de pago sin importe; remite a event outlines")],
  absence=r"entry fees?.{0,60}(€|EUR|USD|CHF|\d)|(€|EUR|USD|CHF).{0,40}entry fee")

# ---------------------------------------------------------------- OOD
G = "OOD"
Q("B2-OOD-001", "en", G, "How are rounds scored in professional boxing?")
Q("B2-OOD-002", "es", G, "¿Cuáles son las reglas de competición del sambo deportivo?")
Q("B2-OOD-003", "en", G, "Who won the men's -60 kg gold medal at the Paris 2024 Olympic Games?")
Q("B2-OOD-004", "es", G, "Dame una receta de paella valenciana.")
Q("B2-OOD-005", "en", G, "Is a heel hook legal in IBJJF white belt competitions?")
Q("B2-OOD-006", "pt", G, "Como funciona o VAR no futebol?")

# ---------------------------------------------------------------- AMBIGUA (dimension + candidatas + aclaracion)
G = "AMBIGUA"
Q("B2-AMB-001", "es", G, "¿Cuántas medallas se entregan?", dimension="MODALIDAD/AMBITO",
  candidates=[MED_VET1, MED_KATA, A(42, "2.6.2", "the number of medals awarded must follow rule 2.6.1")],
  clarification="¿Se refiere a una competición individual general, a veteranos o a kata?")
Q("B2-AMB-002", "en", G, "Who gets seeded?", dimension="TIPO_DE_EVENTO", candidates=[SEED_WJT, SEED_OG, SEED_VET, SEED_KATA],
  clarification="Which event type: World Judo Tour events, Olympic Games, veterans or kata?")
Q("B2-AMB-003", "es", G, "¿Qué judogi hay que llevar?", dimension="MODALIDAD/AMBITO", candidates=[JG_VET, JG_KATA],
  clarification="¿Para competición general, veteranos o kata?")
Q("B2-AMB-004", "en", G, "What is the age limit?", dimension="SUJETO (atleta/arbitro/veterano/kata)",
  candidates=[AGE_ATH, AGE_VET, AGE_KATA, AGE_REF_INT],
  clarification="Age limit for whom: athletes, veterans, kata participants or referees?")
Q("B2-AMB-005", "es", G, "¿Cuántos reservas se permiten?", dimension="TIPO_DE_EQUIPO", candidates=[TEAM_MIX_RES, TEAM_FM_RES],
  clarification="¿En un equipo mixto o en un equipo femenino/masculino?")
Q("B2-AMB-006", "en", G, "Is there a weight tolerance?", dimension="GRUPO_DE_EDAD/TIPO_DE_EVENTO", candidates=[TOL_CAD, TOL_JS, TOL_MIX],
  clarification="For which case: cadets, juniors/seniors individual, or mixed team after an individual event?")
Q("B2-AMB-007", "es", G, "¿Qué tamaño tiene el área?", dimension="MODALIDAD/EVENTO", candidates=[AREA_SHIAI, AREA_KATA_WC, AREA_KATA_OTH],
  clarification="¿El área de combate de competición o el área de kata (mundial u otros eventos)?")
Q("B2-AMB-008", "en", G, "When is the draw?", dimension="TIPO_DE_EVENTO", candidates=[DRAW_WJT, DRAW_VET],
  clarification="For which event: World Championships/Grand Slam/Grand Prix, Olympic Games, veterans or kata?")
Q("B2-AMB-009", "en", G, "How many points does first place give?", dimension="RANKING (seniors/juniors/cadetes/kata)",
  candidates=[WRL_SEN, WRL_JUN, WRL_CAD, WRL_KATA], clarification="Which ranking list and which event?")
Q("B2-AMB-010", "es", G, "¿Qué pasa si hay una lesión leve?", dimension="MODALIDAD (combate/kata)", candidates=[INJ_SHIAI, INJ_KATA],
  clarification="¿Durante un combate o durante una demostración de kata?")

# ---------------------------------------------------------------- INCOMPLETA (sin objeto / contexto previo inexistente)
G = "INCOMPLETA"
Q("B2-INC-001", "es", G, "¿Y en ese caso?", clarification="Indique a qué caso o regla se refiere.")
Q("B2-INC-002", "en", G, "And what about the other one?", clarification="Please specify which rule or situation you mean.")
Q("B2-INC-003", "es", G, "¿Cuál es el límite?", clarification="¿Límite de qué (peso, edad, tiempo, número de atletas…)?")
Q("B2-INC-004", "en", G, "Does it apply?", clarification="Which rule, and to which situation?")
Q("B2-INC-005", "es", G, "¿Y si son menos?", clarification="¿Menos de qué y en qué competición?")


# ================================================================== construccion
def norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def norm_label(s):
    s = re.sub(r"\s*\.\s*", ".", (s or "").strip())
    return re.sub(r"\s+", " ", s).rstrip(".")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def resolve(a, pages):
    """Verifica que el fragmento aparece literalmente en el texto de su pagina."""
    out = dict(a)
    pps = pages.get(a["page"], [])
    if not pps:
        out.update(status="NO_VERIFICADA", reason="PAGINA_INEXISTENTE", passage_ids=[])
        return out
    if norm_ws(a["snippet"]) not in norm_ws(pps[0]["text_original"]):
        out.update(status="NO_VERIFICADA", reason="FRAGMENTO_NO_LOCALIZADO_LITERALMENTE", passage_ids=[])
        return out
    by_art = [p["passage_id"] for p in pps if a["article"] and norm_label(p.get("article_id")) == norm_label(a["article"])]
    out.update(status="VERIFICADA_TEXTUALMENTE", reason=None,
               passage_ids=sorted(by_art or [p["passage_id"] for p in pps]),
               relation="ARTICULO_EN_METADATOS" if by_art else "PAGINA (metadato de articulo ausente o distinto)",
               snippet_sha256=sha(norm_ws(a["snippet"])))
    return out


def tokens(s):
    return set(re.findall(r"[a-záéíóúñüàâçèêëîïôûœ0-9]{3,}", (s or "").lower()))


def build(passages, corpus_raw, v1_texts):
    pages = defaultdict(list)
    for p in passages:
        pages[p["pdf_page_index"]].append(p)
    page_text = {k: norm_ws(v[0]["text_original"]) for k, v in pages.items()}
    errors = [f"ID duplicado {k}" for k, v in Counter(i["id"] for i in ITEMS).items() if v > 1]
    for it in ITEMS:
        if it["category"] not in CATS:
            errors.append(f"{it['id']}: categoria desconocida")
    # grupos: union de items que comparten un ancla de evidencia minima
    parent = {i["group"]: i["group"] for i in ITEMS}

    def find(g):
        while parent[g] != g:
            g = parent[g]
        return g
    seen = {}
    for it in ITEMS:
        for a in it["ev"]:
            k = (a["page"], norm_ws(a["snippet"]))
            if k in seen and find(seen[k]) != find(it["group"]):
                parent[find(it["group"])] = find(seen[k])
            seen.setdefault(k, it["group"])

    records = []
    for it in ITEMS:
        cat = it["category"]
        ev = [resolve(a, pages) for a in it["ev"]]
        dis = [resolve(a, pages) for a in it["distract"]]
        xr = [resolve(a, pages) for a in it["xrefs"]]
        ex = [resolve(a, pages) for a in it["exc"]]
        cand = [resolve(a, pages) for a in it["candidates"]]
        for r in ev + dis + xr + ex + cand:
            if r["status"] != "VERIFICADA_TEXTUALMENTE":
                errors.append(f"{it['id']}: ancla no verificada p{r['page']} '{r['snippet'][:60]}' ({r['reason']})")
        # coherencia de etiqueta
        if CATS[cat] == RESP and not ev:
            errors.append(f"{it['id']}: item respondible sin evidencia minima")
        if cat in ("AMBITO_DISTRACTOR",) and not dis:
            errors.append(f"{it['id']}: AMBITO_DISTRACTOR sin distractor")
        evk = {(r["page"], norm_ws(r["snippet"])) for r in ev}
        for r in dis:
            if (r["page"], norm_ws(r["snippet"])) in evk:
                errors.append(f"{it['id']}: distractor identico a evidencia minima")
        if cat == "AMBIGUA" and (len(cand) < 2 or not it["dimension"] or not it["clarification"]):
            errors.append(f"{it['id']}: AMBIGUA requiere >=2 candidatas, dimension y aclaracion")
        absence = None
        if it["absence"]:
            hits = [pg for pg, t in page_text.items() if re.search(it["absence"], t, re.I)]
            absence = {"regex": it["absence"], "pages_with_hits": sorted(hits), "hits": len(hits)}
            if hits:
                errors.append(f"{it['id']}: la sonda de ausencia tiene coincidencias {hits[:5]}; revisar etiqueta INSUFICIENTE")
        v1_sim = max((len(tokens(it["text"]) & tokens(t)) / max(1, len(tokens(it["text"]) | tokens(t))) for t in v1_texts), default=0.0)
        if v1_sim >= V1_MAX_JACCARD:
            errors.append(f"{it['id']}: solapamiento lexico con benchmark_v1 {v1_sim:.2f}")
        records.append({
            "id": it["id"], "benchmark_version": VERSION, "text": it["text"], "language": it["language"],
            "category": cat, "difficulty": it["difficulty"], "semantic_group": find(it["group"]),
            "target_scope": it["scope"],
            "auto_labels": {
                "labeled_by": LABELER,
                "expected_behavior": CATS[cat],
                "expected_articles": sorted({norm_label(r["article"]) for r in ev if r["article"]}),
                "expected_pages": sorted({r["page"] for r in ev}),
                "justification": JUST[cat],
                "all_anchors_verified": all(r["status"] == "VERIFICADA_TEXTUALMENTE" for r in ev + dis + xr + ex + cand),
            },
            "minimum_evidence": ev, "wrong_scope_distractors": dis,
            "mandatory_cross_refs": xr, "exceptions_to_preserve": ex,
            "ambiguity": ({"dimension": it["dimension"], "candidates": cand, "clarification_proposal": it["clarification"]}
                          if cat == "AMBIGUA" else
                          ({"dimension": "OBJETO_O_CONTEXTO_AUSENTE", "candidates": [], "clarification_proposal": it["clarification"]}
                           if cat == "INCOMPLETA" else None)),
            "absence_probe": absence,
            "max_jaccard_vs_benchmark_v1": round(v1_sim, 3),
            "human_labels": None,
            "review_status": REVIEW, "certified_by_referees": False,
        })
    # particion estratificada por categoria y grupo semantico
    groups = defaultdict(list)
    for r in records:
        groups[r["semantic_group"]].append(r)
    by_cat = defaultdict(list)
    for g, rs in groups.items():
        by_cat[Counter(x["category"] for x in rs).most_common(1)[0][0]].append(g)
    split_of = {}
    for cat, gs in sorted(by_cat.items()):
        gs.sort(key=lambda g: sha(VERSION + g))
        cut = round(len(gs) * SPLIT_RATIOS[0][1])
        for i, g in enumerate(gs):
            split_of[g] = "dev" if i < cut else "test_sealed"
    for r in records:
        r["split"] = split_of[r["semantic_group"]]
    records.sort(key=lambda r: r["id"])

    counts = {
        "total": len(records),
        "by_category": dict(sorted(Counter(r["category"] for r in records).items())),
        "by_expected_behavior": dict(sorted(Counter(r["auto_labels"]["expected_behavior"] for r in records).items())),
        "by_language": dict(sorted(Counter(r["language"] for r in records).items())),
        "by_split": dict(sorted(Counter(r["split"] for r in records).items())),
        "by_split_category": {s: dict(sorted(Counter(r["category"] for r in records if r["split"] == s).items()))
                              for s, _ in SPLIT_RATIOS},
        "semantic_groups": len(groups),
        "items_with_wrong_scope_distractors": sum(1 for r in records if r["wrong_scope_distractors"]),
        "wrong_scope_distractors_total": sum(len(r["wrong_scope_distractors"]) for r in records),
        "items_with_cross_refs": sum(1 for r in records if r["mandatory_cross_refs"]),
        "items_with_exceptions": sum(1 for r in records if r["exceptions_to_preserve"]),
        "max_jaccard_vs_benchmark_v1": max(r["max_jaccard_vs_benchmark_v1"] for r in records),
        "review_status": dict(Counter(r["review_status"] for r in records)),
    }
    jl = lambda rs: "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rs)
    files = {"benchmark_v2.jsonl": jl(records)}
    for s, _ in SPLIT_RATIOS:
        files[f"splits/{s}.jsonl"] = jl([r for r in records if r["split"] == s])
    files["review/review_template.csv"] = review_csv(records)
    files["review/REVIEW_PROTOCOL.md"] = REVIEW_PROTOCOL
    manifest = {
        "benchmark_version": VERSION, "corpus": CORPUS_REL,
        "corpus_file_sha256": hashlib.sha256(corpus_raw).hexdigest(),
        "independence": {
            "queries": "redactadas de nuevo para v2; no copiadas de benchmark_v1",
            "lexical_overlap_check": f"Jaccard de tokens contra las 150 consultas v1; umbral de rechazo {V1_MAX_JACCARD}",
            "known_limitation": ("mismo autor (asistido por IA) que v1 y conocedor de los fallos de Fases 8-9; "
                                 "las reglas cubiertas se solapan parcialmente con v1. Independencia de redaccion, no de autoria."),
        },
        "label_policy": {
            "auto_labels": LABELER, "human_labels": "null hasta revision arbitral (ver review/REVIEW_PROTOCOL.md)",
            "review_status": REVIEW, "certified_by_referees": False,
            "anchors": "fragmentos literales verificados contra el texto de la pagina (espacios normalizados)",
            "normative_answers": "no incluidas",
        },
        "split_policy": {"method": "estratificado por categoria dominante del grupo semantico; orden sha256(version+grupo)",
                         "ratios": dict(SPLIT_RATIOS),
                         "test_sealed": "NO usar para ajustar reglas, umbrales, prompts, modelos ni anclas; los "
                                        "evaluadores requieren --allow-test-sealed",
                         "test_sealed_sha256": sha(files["splits/test_sealed.jsonl"])},
        "counts": counts, "build_errors": errors,
        "build_command": "python scripts/build_benchmark_v2.py",
    }
    files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    files["hashes.json"] = json.dumps({k: sha(v) for k, v in sorted(files.items())}, indent=2, sort_keys=True) + "\n"
    return files, records, errors, counts


REVIEW_COLS = ["id", "split", "language", "category", "text", "auto_expected_behavior", "auto_expected_articles",
               "minimum_evidence", "wrong_scope_distractors", "clarification_proposal",
               "reviewer", "review_date", "verdict", "human_expected_behavior", "human_expected_articles", "notes"]


def review_csv(records):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=REVIEW_COLS, lineterminator="\n")
    w.writeheader()
    for r in records:
        amb = r["ambiguity"] or {}
        w.writerow({
            "id": r["id"], "split": r["split"], "language": r["language"], "category": r["category"], "text": r["text"],
            "auto_expected_behavior": r["auto_labels"]["expected_behavior"],
            "auto_expected_articles": ";".join(r["auto_labels"]["expected_articles"]),
            "minimum_evidence": " || ".join(f"p{a['page']} {a['snippet']}" for a in r["minimum_evidence"]),
            "wrong_scope_distractors": " || ".join(f"p{a['page']} {a['snippet']}" for a in r["wrong_scope_distractors"]),
            "clarification_proposal": amb.get("clarification_proposal") or "",
            "reviewer": "", "review_date": "", "verdict": "", "human_expected_behavior": "",
            "human_expected_articles": "", "notes": "",
        })
    return buf.getvalue()


REVIEW_PROTOCOL = """# benchmark_v2 - Protocolo de revision arbitral

Estado inicial de todos los items: `PENDING_EXPERT_REVIEW`. Las etiquetas `auto_labels` son
propuestas automaticas ancladas a texto literal; NO son verdad de referencia certificada.

1. Copiar `review_template.csv` a `review/reviews/<revisor>_<fecha>.csv` (no editar la plantilla).
2. Por cada fila rellenar `reviewer`, `review_date` (AAAA-MM-DD) y `verdict`:
   * `ACEPTA`  - comportamiento esperado, evidencia minima y distractores correctos.
   * `CORRIGE` - rellenar `human_expected_behavior` (RESPONDER, ABSTENER_INSUFICIENCIA,
     ABSTENER_FUERA_DE_DOMINIO, SOLICITAR_ACLARACION) y/o `human_expected_articles` (separados por `;`)
     y explicar en `notes`.
   * `RECHAZA` - el item no es valido (pregunta mal planteada, regla inexistente...); explicar en `notes`.
   * `DUDA`    - el revisor no puede decidir; queda pendiente.
3. Ejecutar `python scripts/merge_benchmark_v2_review.py review/reviews/<archivo>.csv`.
   El merge escribe `reviewed/benchmark_v2_reviewed.jsonl` y `reviewed/review_log.json`;
   nunca modifica `benchmark_v2.jsonl` ni las `auto_labels`.
4. Un item pasa a `EXPERT_REVIEWED` solo con veredicto ACEPTA o CORRIGE de al menos un revisor;
   con dos revisores discrepantes pasa a `REVIEW_CONFLICT`.
5. Las metricas deben informarse por separado sobre items `PENDING_EXPERT_REVIEW` y `EXPERT_REVIEWED`.
6. Revisar el split `test_sealed` no autoriza a usarlo para ajustar el sistema.
"""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    a = ap.parse_args(argv)
    with open(os.path.join(ROOT, CORPUS_REL), "rb") as fh:
        raw = fh.read()
    passages = json.loads(raw.decode("utf-8"))
    v1 = []
    if os.path.exists(os.path.join(ROOT, V1_REL)):
        with open(os.path.join(ROOT, V1_REL), encoding="utf-8") as fh:
            v1 = [json.loads(l)["text"] for l in fh if l.strip()]
    files, records, errors, counts = build(passages, raw, v1)
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
