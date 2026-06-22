"""Question Interface Layer - matches document section 8.1."""
import time
from .schemas import QuestionInput, QuestionType
from .normalization import TextNormalizer
from ..entropy.encoder import EntropyEncoder, EntropyPacket


class QuestionInterface:
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.encoder = EntropyEncoder()

    def process(self, question_input: QuestionInput) -> dict:
        normalized_text = self.normalizer.normalize(question_input.question)
        question_type = QuestionType.detect(question_input.question)
        numeric_tokens = self.normalizer.extract_numeric_tokens(question_input.question)
        words = self.normalizer.extract_words(normalized_text)
        language = self.normalizer.detect_language(question_input.question)

        timestamp = time.time()
        if question_input.datetime:
            try:
                from datetime import datetime as dt
                parsed = dt.fromisoformat(question_input.datetime)
                timestamp = parsed.timestamp()
            except (ValueError, TypeError):
                pass

        entropy_packet = self.encoder.encode(
            text=normalized_text,
            timestamp=timestamp,
            location=question_input.location or None,
            extra_numbers=question_input.optional_numbers or None,
        )

        return {
            "normalized_text": normalized_text,
            "question_type": question_type,
            "numeric_tokens": numeric_tokens,
            "words": words,
            "language": language,
            "timestamp": timestamp,
            "entropy_packet": entropy_packet,
            "original": question_input,
        }
