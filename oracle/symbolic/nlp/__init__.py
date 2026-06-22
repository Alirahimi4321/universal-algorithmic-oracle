"""NLP processing wrappers."""
from .spacy_wrapper import SpacyWrapper
from .sentence_transformer_wrapper import SentenceTransformerWrapper
from .langdetect_wrapper import LangdetectWrapper

__all__ = ["SpacyWrapper", "SentenceTransformerWrapper", "LangdetectWrapper"]
