"""Input sanitization for user-provided data."""
import re
import html
import logging

logger = logging.getLogger("oracle.sanitizer")

MAX_QUESTION_LENGTH = 10000
SAFE_PATTERN = re.compile(r'^[\w\s\d.,!?;:\-\'\"()\[\]{}@#$%^&*+=/\\|~`<>]+$')

def sanitize_question(question: str) -> str:
    """Sanitize user question input."""
    if not isinstance(question, str):
        question = str(question)
    
    question = question.strip()
    
    if len(question) > MAX_QUESTION_LENGTH:
        logger.warning("Question truncated from %d to %d chars", len(question), MAX_QUESTION_LENGTH)
        question = question[:MAX_QUESTION_LENGTH]
    
    question = html.escape(question)
    
    return question

def sanitize_seed(seed) -> int:
    """Sanitize random seed to a valid integer."""
    try:
        seed = int(seed)
        return seed & 0xFFFFFFFF
    except (ValueError, TypeError):
        logger.warning("Invalid seed %s, using default 42", seed)
        return 42

def sanitize_config_value(value, default=None, min_val=None, max_val=None):
    """Sanitize a numeric config value."""
    try:
        value = float(value)
        if min_val is not None and value < min_val:
            value = min_val
        if max_val is not None and value > max_val:
            value = max_val
        return value
    except (ValueError, TypeError):
        return default
