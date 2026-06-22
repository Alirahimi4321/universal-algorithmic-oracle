"""Text normalization - matches document section 8.1."""
import re
import unicodedata


class TextNormalizer:
    PERSIAN_CHARS = set("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")
    ARABIC_CHARS = set("أإآءؤئبتثجحخدذرزسشصضطظعغفقكلمنهوي")
    NUMBERS_MAP = {
        "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
        "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
    }

    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = self._normalize_persian(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _normalize_persian(self, text: str) -> str:
        for arabic, persian in zip("يىكؤهة", "ییکوئه"):
            text = text.replace(arabic, persian)
        for num_fa, num_en in self.NUMBERS_MAP.items():
            text = text.replace(num_fa, num_en)
        return text

    def extract_numeric_tokens(self, text: str) -> list[float]:
        numbers = re.findall(r"\d+\.?\d*", text)
        return [float(n) for n in numbers]

    def extract_words(self, text: str) -> list[str]:
        return text.split()

    def detect_language(self, text: str) -> str:
        persian_count = sum(1 for c in text if c in self.PERSIAN_CHARS)
        arabic_count = sum(1 for c in text if c in self.ARABIC_CHARS)
        latin_count = sum(1 for c in text if c.isascii() and c.isalpha())
        total = persian_count + arabic_count + latin_count
        if total == 0:
            return "unknown"
        if persian_count / total > 0.3:
            return "persian"
        if arabic_count / total > 0.3:
            return "arabic"
        return "english"
