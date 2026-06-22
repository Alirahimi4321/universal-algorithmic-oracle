"""Question schemas - matches document section 8.1."""
from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class QuestionInput:
    question: str = ""
    datetime: str = ""
    timezone: str = "UTC"
    location: dict = field(default_factory=dict)
    optional_numbers: list = field(default_factory=list)
    domain: str = ""
    horizon: str = ""
    user_id: str = ""
    intent: str = ""
    metadata: dict = field(default_factory=dict)


class QuestionType:
    CAREER = "career"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    FINANCE = "finance"
    SPIRITUAL = "spiritual"
    GENERAL = "general"
    DREAM = "dream"
    DECISION = "decision"

    @classmethod
    def detect(cls, text: str) -> str:
        text_lower = text.lower()
        keywords = {
            cls.CAREER: ["شغل", "کار", "حرفه", "شغلی", "شغلم", "کاری", "کارم", "career", "job", "work"],
            cls.RELATIONSHIP: ["رابطه", "عشق", "ازدواج", "عاشق", "love", "marriage", "relationship"],
            cls.HEALTH: ["سلامت", "بیماری", "درمان", "مریض", "health", "disease"],
            cls.FINANCE: ["پول", "مالی", "سرمایه", "درآمد", "money", "finance", "investment"],
            cls.SPIRITUAL: ["معنوی", "روحانی", "meditation", "spiritual"],
            cls.DREAM: ["خواب", "رؤیا", "dream", "vision"],
            cls.DECISION: ["تصمیم", "انتخاب", "decision", "choose"],
        }
        for qtype, words in keywords.items():
            if any(w in text_lower for w in words):
                return qtype
        return cls.GENERAL
