from typing import List
from sqlalchemy import func
from .normalize_text import normalize_text


# Utility function for building fuzzy matching conditions
def build_fuzzy_conditions(column, terms: List[str], threshold: float = 0.3) -> List:
    """Builds fuzzy matching conditions using pg_trgm similarity."""

    conditions = []
    # Filter out '*' and empty strings, then normalize
    valid_terms_normalized = [
        norm_term
        for term in terms
        if term != "*" and term
        if (norm_term := normalize_text(term))
    ]
    if not valid_terms_normalized:
        return []

    for norm_term in valid_terms_normalized:
        # Calculate similarity directly on the column
        # Assumes the column in the DB is already normalized or comparison handles it
        conditions.append(func.similarity(column, norm_term) > threshold)
    return conditions
