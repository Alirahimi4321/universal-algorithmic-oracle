"""Entropy encoder - converts text to real symbolic/numeric feature representations."""
import hashlib
import random
import time
import math
import secrets
from dataclasses import dataclass, field


@dataclass
class EntropyPacket:
    raw_question: str = ""
    normalized_text: str = ""
    timestamp: float = 0.0
    seed: int = 0
    sha_stream: list = field(default_factory=list)
    hash_stream: list = field(default_factory=list)
    bit_stream: list = field(default_factory=list)
    numeric_vector: list = field(default_factory=list)
    symbolic_tokens: list = field(default_factory=list)
    symbolic_matrix: list = field(default_factory=list)
    calendar_context: dict = field(default_factory=dict)
    calendar_views: dict = field(default_factory=dict)
    question_signature: dict = field(default_factory=dict)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __getitem__(self, key):
        return getattr(self, key)

    def __contains__(self, key):
        return hasattr(self, key) and getattr(self, key) is not None

    def keys(self):
        from dataclasses import fields as dc_fields
        return [f.name for f in dc_fields(self)]

    def values(self):
        from dataclasses import fields as dc_fields
        return [getattr(self, f.name) for f in dc_fields(self)]

    def items(self):
        from dataclasses import fields as dc_fields
        return [(f.name, getattr(self, f.name)) for f in dc_fields(self)]

    def __iter__(self):
        return self.keys().__iter__()


class EntropyEncoder:
    ARABIC_ORDINAL = {
        'ا': 1, 'ب': 2, 'ج': 3, 'د': 4, 'ه': 5, 'و': 6, 'ز': 7,
        'ح': 8, 'ط': 9, 'ی': 10, 'ک': 11, 'ل': 12, 'م': 13, 'ن': 14,
        'س': 15, 'ع': 16, 'ف': 17, 'ص': 18, 'ق': 19, 'ر': 20, 'ش': 21,
        'ت': 22, 'ث': 23, 'خ': 24, 'ذ': 25, 'ض': 26, 'ظ': 27, 'غ': 28,
    }

    HEBREW_ORDINAL = {
        'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7,
        'ח': 8, 'ט': 9, 'י': 10, 'כ': 11, 'ל': 12, 'מ': 13, 'נ': 14,
        'ס': 15, 'ע': 16, 'פ': 17, 'צ': 18, 'ק': 19, 'ר': 20, 'ש': 21,
        'ת': 22,
    }

    def __init__(self):
        self._counter = 0

    def encode(self, text: str, timestamp: float = None, location: dict = None,
               extra_numbers: list = None) -> EntropyPacket:
        self._counter += 1
        if timestamp is None:
            timestamp = time.time()

        combined = f"{text}_{timestamp}_{location}_{extra_numbers}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        seed = int.from_bytes(hash_obj.digest()[:4], byteorder='big')

        normalized = text.lower().strip()
        char_features = self._extract_char_features(normalized)
        word_features = self._extract_word_features(normalized)
        question_type = self._classify_question_type(normalized)
        temporal_features = self._extract_temporal_features(timestamp)
        numeric_tokens = self._extract_numeric_tokens(text)
        gematria_values = self._compute_gematria(normalized)

        bit_stream = self._text_to_bitstream(normalized, seed)
        numeric_vector = self._build_numeric_vector(
            char_features, word_features, temporal_features,
            numeric_tokens, gematria_values, question_type, seed
        )

        sha_stream = []
        for i in range(16):
            h = hashlib.sha256(f"{text}_{i}_{seed}".encode()).digest()
            sha_stream.extend(list(h[:8]))

        symbolic_tokens = normalized.split()
        calendar_context = self._generate_calendar_context(timestamp)

        question_signature = {
            "hash_hex": hash_obj.hexdigest(),
            "seed": seed,
            "length": len(text),
            "word_count": len(symbolic_tokens),
            "char_count": len(text),
            "question_type": question_type,
            "char_features": char_features,
            "word_features": word_features,
            "gematria": gematria_values,
            "temporal": temporal_features,
        }

        symbolic_matrix = [bit_stream[i:i + 8] for i in range(0, min(len(bit_stream), 64), 8)]

        return EntropyPacket(
            raw_question=text,
            normalized_text=normalized,
            timestamp=timestamp,
            seed=seed,
            sha_stream=sha_stream,
            hash_stream=sha_stream,
            bit_stream=bit_stream,
            numeric_vector=numeric_vector,
            symbolic_tokens=symbolic_tokens,
            symbolic_matrix=symbolic_matrix,
            calendar_context=calendar_context,
            calendar_views=calendar_context,
            question_signature=question_signature,
        )

    def _extract_char_features(self, text: str) -> dict:
        if not text:
            return {"length": 0, "unique_chars": 0, "vowel_ratio": 0, "digit_ratio": 0,
                    "consonant_ratio": 0, "avg_char_ord": 0, "char_entropy": 0}

        chars = list(text)
        unique_chars = len(set(chars))
        vowels = sum(1 for c in chars if c in 'aeiouàáâãäåèéêëìíîïòóôõöùúûüýÿآاوت')
        digits = sum(1 for c in chars if c.isdigit())
        consonants = sum(1 for c in chars if c.isalpha() and c not in 'aeiouàáâãäåèéêëìíîïòóôõöùúûüýÿآاوت')

        char_counts = {}
        for c in chars:
            char_counts[c] = char_counts.get(c, 0) + 1
        total = len(chars)
        char_entropy = -sum((count / total) * math.log2(count / total)
                           for count in char_counts.values() if count > 0)

        return {
            "length": total,
            "unique_chars": unique_chars,
            "vowel_ratio": vowels / max(total, 1),
            "digit_ratio": digits / max(total, 1),
            "consonant_ratio": consonants / max(total, 1),
            "avg_char_ord": sum(ord(c) for c in chars) / max(total, 1),
            "char_entropy": char_entropy,
        }

    def _extract_word_features(self, text: str) -> dict:
        words = text.split()
        if not words:
            return {"word_count": 0, "avg_word_length": 0, "max_word_length": 0,
                    "short_word_ratio": 0, "long_word_ratio": 0, "word_length_entropy": 0}

        lengths = [len(w) for w in words]
        avg_len = sum(lengths) / len(lengths)
        short_words = sum(1 for l in lengths if l <= 3)
        long_words = sum(1 for l in lengths if l > 6)

        length_counts = {}
        for l in lengths:
            length_counts[l] = length_counts.get(l, 0) + 1
        total = len(lengths)
        word_length_entropy = -sum((c / total) * math.log2(c / total)
                                   for c in length_counts.values() if c > 0)

        return {
            "word_count": len(words),
            "avg_word_length": avg_len,
            "max_word_length": max(lengths),
            "short_word_ratio": short_words / max(total, 1),
            "long_word_ratio": long_words / max(total, 1),
            "word_length_entropy": word_length_entropy,
        }

    def _classify_question_type(self, text: str) -> int:
        """Classify question type: 0=unknown, 1=yes/no, 2=open, 3=choice, 4=time, 5=person"""
        yes_no_patterns = ['آیا', 'آیا', 'هل', '是否', 'is ', 'are ', 'do ', 'does ', 'will ', 'can ']
        time_patterns = ['کی', 'چه زمانی', 'چند وقت', 'when', 'how long', 'زمان', 'وقت']
        person_patterns = ['چه کسی', 'چه کسی', 'who', 'whom']
        choice_patterns = ['یا', 'or ', 'either']

        for p in yes_no_patterns:
            if p in text:
                return 1
        for p in time_patterns:
            if p in text:
                return 4
        for p in person_patterns:
            if p in text:
                return 5
        for p in choice_patterns:
            if p in text:
                return 3
        return 2

    def _extract_temporal_features(self, timestamp: float) -> dict:
        t = time.gmtime(timestamp)
        hour_sin = math.sin(2 * math.pi * t.tm_hour / 24)
        hour_cos = math.cos(2 * math.pi * t.tm_hour / 24)
        month_sin = math.sin(2 * math.pi * t.tm_mon / 12)
        month_cos = math.cos(2 * math.pi * t.tm_mon / 12)
        day_sin = math.sin(2 * math.pi * t.tm_mday / 31)
        day_cos = math.cos(2 * math.pi * t.tm_mday / 31)
        weekday_sin = math.sin(2 * math.pi * t.tm_wday / 7)
        weekday_cos = math.cos(2 * math.pi * t.tm_wday / 7)
        yearday_sin = math.sin(2 * math.pi * t.tm_yday / 365)
        yearday_cos = math.cos(2 * math.pi * t.tm_yday / 365)

        return {
            "hour_sin": hour_sin, "hour_cos": hour_cos,
            "month_sin": month_sin, "month_cos": month_cos,
            "day_sin": day_sin, "day_cos": day_cos,
            "weekday_sin": weekday_sin, "weekday_cos": weekday_cos,
            "yearday_sin": yearday_sin, "yearday_cos": yearday_cos,
            "unix_timestamp": timestamp,
            "year": t.tm_year,
        }

    def _extract_numeric_tokens(self, text: str) -> list:
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        return [float(n) for n in numbers]

    def _compute_gematria(self, text: str) -> dict:
        abjad_sum = 0
        for c in text:
            if c in self.ARABIC_ORDINAL:
                abjad_sum += self.ARABIC_ORDINAL[c]

        hebrew_sum = 0
        for c in text:
            if c in self.HEBREW_ORDINAL:
                hebrew_sum += self.HEBREW_ORDINAL[c]

        english_sum = 0
        for c in text.lower():
            if 'a' <= c <= 'z':
                english_sum += ord(c) - ord('a') + 1

        digital_root = abjad_sum
        while digital_root > 9 and digital_root not in (11, 22, 33):
            digital_root = sum(int(d) for d in str(digital_root))

        return {
            "abjad": abjad_sum,
            "hebrew": hebrew_sum,
            "english": english_sum,
            "digital_root": digital_root,
            "abjad_mod_7": abjad_sum % 7 if abjad_sum else 0,
            "abjad_mod_9": abjad_sum % 9 if abjad_sum else 0,
            "abjad_mod_12": abjad_sum % 12 if abjad_sum else 0,
            "abjad_mod_22": abjad_sum % 22 if abjad_sum else 0,
        }

    def _text_to_bitstream(self, text: str, seed: int) -> list:
        bits = []
        for c in text:
            code = ord(c)
            for i in range(7):
                bits.append((code >> i) & 1)
        rng = random.Random(seed)
        padding = 256 - len(bits)
        if padding > 0:
            bits.extend([rng.randint(0, 1) for _ in range(padding)])
        return bits[:256]

    def _build_numeric_vector(self, char_features, word_features, temporal_features,
                               numeric_tokens, gematria, question_type, seed) -> list:
        vector = [
            char_features["length"] / 1000,
            char_features["unique_chars"] / 50,
            char_features["vowel_ratio"],
            char_features["consonant_ratio"],
            char_features["digit_ratio"],
            min(char_features["char_entropy"] / 8, 1.0),
            char_features["avg_char_ord"] / 1000,
            word_features["word_count"] / 50,
            word_features["avg_word_length"] / 15,
            word_features["max_word_length"] / 30,
            word_features["short_word_ratio"],
            word_features["long_word_ratio"],
            min(word_features["word_length_entropy"] / 5, 1.0),
            temporal_features["hour_sin"],
            temporal_features["hour_cos"],
            temporal_features["month_sin"],
            temporal_features["month_cos"],
            temporal_features["day_sin"],
            temporal_features["day_cos"],
            temporal_features["weekday_sin"],
            temporal_features["weekday_cos"],
            temporal_features["yearday_sin"],
            temporal_features["yearday_cos"],
            question_type / 5,
            min(gematria["abjad"] / 1000, 1.0),
            min(gematria["hebrew"] / 1000, 1.0),
            min(gematria["english"] / 500, 1.0),
            gematria["digital_root"] / 33,
            gematria["abjad_mod_7"] / 7,
            gematria["abjad_mod_9"] / 9,
            gematria["abjad_mod_12"] / 12,
            gematria["abjad_mod_22"] / 22,
        ]

        if numeric_tokens:
            vector.append(min(max(numeric_tokens) / 1000, 1.0))
            vector.append(len(numeric_tokens) / 10)
            vector.append(sum(numeric_tokens) / (len(numeric_tokens) * 1000))
        else:
            vector.extend([0.0, 0.0, 0.0])

        rng = random.Random(seed)
        while len(vector) < 64:
            vector.append(rng.random() * 0.01)

        return vector[:64]

    def _generate_calendar_context(self, timestamp: float) -> dict:
        t = time.gmtime(timestamp)
        return {
            "year": t.tm_year, "month": t.tm_mon, "day": t.tm_mday,
            "hour": t.tm_hour, "minute": t.tm_min, "second": t.tm_sec,
            "weekday": t.tm_wday, "yearday": t.tm_yday,
            "hour_sin": math.sin(2 * math.pi * t.tm_hour / 24),
            "hour_cos": math.cos(2 * math.pi * t.tm_hour / 24),
            "month_sin": math.sin(2 * math.pi * t.tm_mon / 12),
            "month_cos": math.cos(2 * math.pi * t.tm_mon / 12),
        }
