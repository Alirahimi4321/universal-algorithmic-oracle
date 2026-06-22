"""NLP Question Analyzer using spaCy and Stanza for deep question understanding."""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import spacy
    _spacy_nlp = spacy.load("en_core_web_sm")
    HAS_SPACY = True
except Exception:
    HAS_SPACY = False
    _spacy_nlp = None

try:
    import stanza
    _stanza_nlp = stanza.Pipeline("en", processors="tokenize,pos,lemma", verbose=False)
    HAS_STANZA = True
except Exception:
    HAS_STANZA = False
    _stanza_nlp = None

_INTENT_KEYWORDS = {
    "career": {"job","work","career","project","promotion","business","success","company","شغل","کار","پروژه","موفقیت"},
    "relationship": {"love","marriage","partner","family","friend","relationship","عشق","ازدواج","رابطه","خانواده"},
    "health": {"health","doctor","illness","healing","medicine","body","سلامت","بیماری","درمان","پزشک"},
    "finance": {"money","wealth","investment","income","profit","financial","پول","ثروت","سرمایه","درآمد"},
    "spiritual": {"god","soul","spirit","pray","faith","destiny","fate","خدا","روح","ایمان","تقدیر","سرنوشت"},
    "dream": {"dream","vision","nightmare","sleep","رؤیا","خواب","کابوس"},
    "decision": {"decide","choose","option","which","whether","choice","تصمیم","انتخاب","گزینه","کدام"},
}

_QUESTION_TYPE_MARKERS = {
    "yes_no": {"is","are","was","were","will","can","do","does","did","آیا","هست","خواهد"},
    "open": {"what","how","why","tell","describe","explain","چی","چگونه","چرا"},
    "choice": {"which","or","better","کدام","یا","بهتر"},
    "time": {"when","time","date","day","month","year","کی","زمان","تاریخ"},
    "person": {"who","whom","whose","چه کسی"},
}


class QuestionAnalyzer:
    """Deep question understanding using spaCy, Stanza, and VADER."""

    def __init__(self) -> None:
        self.spacy_available = HAS_SPACY
        self.stanza_available = HAS_STANZA

    def analyze(self, question: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "raw_question": question,
            "language": self._detect_language(question),
            "intent": self._detect_intent(question),
            "question_type": self._detect_question_type(question),
            "keywords": self._extract_keywords(question),
            "entities": [],
            "pos_tags": [],
            "lemmas": [],
            "complexity": 0.0,
        }
        if self.spacy_available and _spacy_nlp is not None:
            result["entities"] = self._spacy_entities(question)
            result["pos_tags"] = self._spacy_pos(question)
            result["complexity"] = self._compute_complexity(question)
        if self.stanza_available and _stanza_nlp is not None:
            dep = self._stanza_analyze(question)
            result["lemmas"] = dep.get("lemmas", [])
        result["confidence_weight"] = self._compute_confidence_weight(result)
        return result

    def _detect_language(self, text: str) -> str:
        persian = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
        latin = sum(1 for c in text if c.isascii() and c.isalpha())
        if persian / max(len(text), 1) > 0.1:
            return "fa"
        if latin / max(len(text), 1) > 0.1:
            return "en"
        return "unknown"

    def _detect_intent(self, text: str) -> str:
        text_lower = text.lower()
        scores = {}
        for intent, keywords in _INTENT_KEYWORDS.items():
            scores[intent] = sum(1 for kw in keywords if kw in text_lower)
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"

    def _detect_question_type(self, text: str) -> str:
        text_lower = text.lower().strip()
        for qtype, markers in _QUESTION_TYPE_MARKERS.items():
            for marker in markers:
                if text_lower.startswith(marker) or (" " + marker + " ") in text_lower:
                    return qtype
        if text_lower.endswith("?") or text_lower.endswith("؟"):
            return "open"
        return "general"

    def _extract_keywords(self, text: str) -> list[str]:
        if self.spacy_available and _spacy_nlp is not None:
            doc = _spacy_nlp(text)
            return [t.lemma_ for t in doc if not t.is_stop and not t.is_punct and len(t.text) > 2]
        return [w for w in text.split() if len(w) > 2]

    def _spacy_entities(self, text: str) -> list[dict[str, str]]:
        if _spacy_nlp is None:
            return []
        doc = _spacy_nlp(text)
        return [{"text": e.text, "label": e.label_} for e in doc.ents]

    def _spacy_pos(self, text: str) -> list[dict[str, str]]:
        if _spacy_nlp is None:
            return []
        doc = _spacy_nlp(text)
        return [{"text": t.text, "pos": t.pos_} for t in doc]

    def _stanza_analyze(self, text: str) -> dict[str, list]:
        if _stanza_nlp is None:
            return {"lemmas": []}
        doc = _stanza_nlp(text)
        lemmas = []
        for s in doc.sentences:
            for w in s.words:
                lemmas.append(w.lemma)
        return {"lemmas": lemmas}

    def _compute_complexity(self, text: str) -> float:
        if _spacy_nlp is None:
            return min(1.0, len(text.split()) / 20.0)
        doc = _spacy_nlp(text)
        return min(1.0, (len(doc) / 15.0) * 0.5 + (len(doc.ents) / 5.0) * 0.3 + 0.2)

    def _compute_confidence_weight(self, analysis: dict) -> float:
        weight = 1.0
        if analysis.get("question_type") == "yes_no":
            weight *= 1.1
        elif analysis.get("question_type") == "open":
            weight *= 0.9
        if analysis.get("complexity", 0) > 0.7:
            weight *= 0.95
        return round(weight, 4)
