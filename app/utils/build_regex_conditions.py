import re
import logging
from typing import List


from .normalize_text import normalize_text

logger = logging.getLogger(__name__)


# Utility function for building regex conditions
def build_regex_conditions(column, terms: List[str]) -> List:
    """Builds case-insensitive regex conditions for a list of terms."""
    if logger.isEnabledFor(logging.DEBUG):
        # Log terms only if DEBUG is enabled and terms are not excessively long or numerous
        terms_log = (
            terms
            if len(terms) < 10 and all(len(str(t)) < 100 for t in terms)
            else f"{len(terms)} terms"
        )
        logger.debug(
            f"Building regex conditions for column: {column} (type: {type(column)}) with terms: {terms_log}"
        )

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
        words = norm_term.split()
        if words:
            # Escape each word individually
            escaped_words = [re.escape(word) for word in words]

            # For PostgreSQL:
            pattern = r"\m" + r"\M.*\m".join(escaped_words) + r"\M"

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Generated regex pattern with word boundaries: '{pattern}' for term: '{norm_term}'"
                )
            conditions.append(column.op("~*")(pattern))
    return conditions
