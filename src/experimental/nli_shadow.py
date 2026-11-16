"""Fase 10.2 - Evaluador NLI EXPERIMENTAL en modo SHADOW.

Estima, con un modelo NLI de CPU, si cada afirmacion de una respuesta esta soportada por la
evidencia citada. Es una MEDICION EXPERIMENTAL:
  * no modifica decisiones de ADA, no autoriza SUCCESS, no sustituye citas, no decide autoridad;
  * su resultado no es prueba de entailment normativo (modelos generales, no entrenados en el SOR);
  * ningun modulo productivo lo importa (tests/test_fase10_experimental.py).

Uso:
    ev = NLIShadowEvaluator("MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli")
    ev.load()
    rep = ev.evaluate(question, answer, cited_evidence=[texto, ...], context=None)
Tambien acepta un `scorer` inyectado (callable(premise, hypothesis) -> dict de probabilidades)
para pruebas sin modelo.
"""
import os
import re
import threading
import time

from . import EXPERIMENTAL_LABEL

DISCLAIMER = ("Estimacion de un modelo NLI general en modo SHADOW; no constituye prueba de entailment "
              "normativo, no altera la decision de ADA y no autoriza respuestas.")
RESULTS = ("SOPORTE_PROBABLE", "SOPORTE_NO_ESTABLECIDO", "CONTRADICCION_PROBABLE", "INDETERMINADO")
_CITE = re.compile(r"\[(?:SOR|KUN|CHK|COMPLEMENTO)[^\]]*\]|\((?:SOR|KUN)-[^)]*\)|[*_`#>]+")
_SENT = re.compile(r"(?<=[.!?;])\s+(?=[A-ZÁÉÍÓÚÑ0-9¿¡\"“(])|\n+")


# ---------------------------------------------------------------- memoria del proceso
def rss_mb():
    try:
        import psutil  # opcional
        return psutil.Process().memory_info().rss / 2 ** 20
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            c = PMC()
            c.cb = ctypes.sizeof(PMC)
            ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
            return c.WorkingSetSize / 2 ** 20
        except Exception:
            return None
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except Exception:
        return None


def peak_rss_mb():
    if os.name == "nt":
        try:
            import psutil
            return psutil.Process().memory_info().peak_wset / 2 ** 20
        except Exception:
            pass
        try:
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t)] + \
                           [(n, ctypes.c_size_t) for n in ("a", "b", "c", "d", "e", "f")]
            c = PMC()
            c.cb = ctypes.sizeof(PMC)
            ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
            return c.PeakWorkingSetSize / 2 ** 20
        except Exception:
            return None
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return None


# ---------------------------------------------------------------- utilidades
def split_claims(answer, min_words=4):
    text = _CITE.sub(" ", answer or "")
    out = []
    for s in _SENT.split(text):
        s = re.sub(r"\s+", " ", s).strip(" -•\t")
        if len(re.findall(r"\w+", s)) >= min_words:
            out.append(s)
    return out


def map_labels(id2label):
    """Indices de entailment / neutral / contradiction a partir de id2label del modelo."""
    idx = {"entailment": None, "neutral": None, "contradiction": None}
    for i, lab in id2label.items():
        l = str(lab).lower()
        if "not" in l and "entail" in l:
            idx["neutral"] = int(i)
        elif "entail" in l:
            idx["entailment"] = int(i)
        elif "contrad" in l:
            idx["contradiction"] = int(i)
        elif "neutral" in l:
            idx["neutral"] = int(i)
    if idx["entailment"] is None:
        raise ValueError(f"el modelo no expone una etiqueta de entailment: {id2label}")
    return idx


def lexical_scorer(premise, hypothesis):
    """Linea base NO semantica: fraccion de terminos de contenido de la hipotesis presentes en la premisa."""
    tok = lambda s: set(re.findall(r"[a-záéíóúñüàâçèêëîïôûœ]{4,}|\d+(?:[.,]\d+)?", (s or "").lower()))
    h, p = tok(hypothesis), tok(premise)
    ov = len(h & p) / len(h) if h else 0.0
    return {"entailment": ov, "neutral": 1.0 - ov, "contradiction": 0.0, "truncated": False}


# ---------------------------------------------------------------- evaluador
class NLIShadowEvaluator:
    def __init__(self, model_name=None, scorer=None, device="cpu", max_length=512,
                 entail_threshold=0.5, contradiction_threshold=0.5, hypothesis_mode="answer"):
        if not model_name and scorer is None:
            raise ValueError("indique model_name o scorer")
        self.model_name = model_name or getattr(scorer, "__name__", "scorer")
        self._scorer = scorer
        self.device = device
        self.max_length = max_length
        self.entail_threshold = entail_threshold
        self.contradiction_threshold = contradiction_threshold
        self.hypothesis_mode = hypothesis_mode
        self.load_info = {"loaded": scorer is not None, "load_ms": 0.0, "rss_before_mb": None,
                          "rss_after_mb": None, "n_parameters": None, "error": None}
        self._tok = self._model = self._idx = None
        # los tokenizadores "fast" no admiten uso concurrente ("Already borrowed"): se serializa
        # solo la tokenizacion; la inferencia del modelo puede ejecutarse en paralelo
        self._tok_lock = threading.Lock()

    # -- carga del modelo (perezosa, solo transformers/torch ya instalados)
    def load(self):
        if self.load_info["loaded"]:
            return self.load_info
        self.load_info["rss_before_mb"] = rss_mb()
        t0 = time.perf_counter()
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            self._torch = torch
            self._tok = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name).to(self.device).eval()
            self._idx = map_labels(self._model.config.id2label)
            self.load_info["n_parameters"] = int(sum(p.numel() for p in self._model.parameters()))
            self.load_info["id2label"] = {int(k): v for k, v in self._model.config.id2label.items()}
            self.load_info["loaded"] = True
        except Exception as e:  # dependencia o descarga no disponible: se documenta, no se oculta
            self.load_info["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        self.load_info["load_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        self.load_info["rss_after_mb"] = rss_mb()
        return self.load_info

    def score_batch(self, pairs):
        """pairs: [(premise, hypothesis)] -> [dict(entailment, neutral, contradiction, truncated)]."""
        if self._scorer is not None:
            return [dict(self._scorer(p, h)) for p, h in pairs]
        if not self.load_info["loaded"]:
            raise RuntimeError(f"modelo no cargado: {self.load_info['error']}")
        torch = self._torch
        with self._tok_lock:
            enc = self._tok([p for p, _ in pairs], [h for _, h in pairs], truncation="only_first",
                            max_length=self.max_length, padding=True, return_tensors="pt")
            full = self._tok([p for p, _ in pairs], [h for _, h in pairs], truncation=False)["input_ids"]
        with torch.inference_mode():
            probs = torch.softmax(self._model(**{k: v.to(self.device) for k, v in enc.items()}).logits, dim=-1).cpu().tolist()
        out = []
        for row, ids in zip(probs, full):
            d = {k: (row[i] if i is not None else 0.0) for k, i in self._idx.items()}
            if self._idx["neutral"] is None:
                d["neutral"] = max(0.0, 1.0 - d["entailment"] - d["contradiction"])
            d["truncated"] = len(ids) > self.max_length
            out.append(d)
        return out

    def score_pair(self, premise, hypothesis):
        return self.score_batch([(premise, hypothesis)])[0]

    def _hyp(self, question, claim):
        return f"{question} {claim}" if self.hypothesis_mode == "question_answer" and question else claim

    def evaluate(self, question, answer, cited_evidence, context=None):
        """Informe experimental. Nunca devuelve campos de decision."""
        t0 = time.perf_counter()
        rep = {"experimental_label": EXPERIMENTAL_LABEL, "decision_effect": "NINGUNO", "disclaimer": DISCLAIMER,
               "model": self.model_name, "hypothesis_mode": self.hypothesis_mode,
               "thresholds": {"entailment": self.entail_threshold, "contradiction": self.contradiction_threshold},
               "result": "INDETERMINADO", "claims": [], "scores": {}, "errors": [], "abstention_reason": None,
               "time_ms": None, "memory": {}}
        evidence = [e for e in (cited_evidence or []) if (e or "").strip()]
        claims = split_claims(answer)
        if not evidence:
            rep["abstention_reason"] = "SIN_EVIDENCIA_CITADA"
        elif not claims:
            rep["abstention_reason"] = "SIN_AFIRMACIONES_EVALUABLES"
        elif self._scorer is None and not self.load().get("loaded"):
            rep["abstention_reason"] = "MODELO_NO_DISPONIBLE"
            rep["errors"].append(self.load_info["error"])
        if rep["abstention_reason"]:
            rep["time_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            return rep
        premises = [f"{context} {e}".strip() if context else e for e in evidence]
        try:
            for c in claims:
                sc = self.score_batch([(p, self._hyp(question, c)) for p in premises])
                best = max(range(len(sc)), key=lambda i: sc[i]["entailment"])
                rep["claims"].append({"claim": c, "best_evidence_index": best,
                                      "entailment": round(sc[best]["entailment"], 4),
                                      "max_contradiction": round(max(s["contradiction"] for s in sc), 4),
                                      "truncated": any(s.get("truncated") for s in sc)})
        except Exception as e:
            rep["errors"].append(f"{type(e).__name__}: {str(e)[:300]}")
            rep["abstention_reason"] = "ERROR_DE_INFERENCIA"
            rep["time_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            return rep
        mn = min(c["entailment"] for c in rep["claims"])
        mc = max(c["max_contradiction"] for c in rep["claims"])
        rep["scores"] = {"min_claim_entailment": mn, "max_claim_contradiction": mc,
                         "n_claims": len(claims), "n_evidence": len(evidence)}
        if mc >= self.contradiction_threshold:
            rep["result"] = "CONTRADICCION_PROBABLE"
        elif mn >= self.entail_threshold:
            rep["result"] = "SOPORTE_PROBABLE"
        else:
            rep["result"] = "SOPORTE_NO_ESTABLECIDO"
        if any(c["truncated"] for c in rep["claims"]):
            rep["errors"].append("PREMISA_TRUNCADA: parte de la evidencia excede max_length")
        rep["time_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        rep["memory"] = {"rss_mb": rss_mb(), "peak_rss_mb": peak_rss_mb()}
        return rep
