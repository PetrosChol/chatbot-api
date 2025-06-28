import re
import unicodedata
from .greek_abbreviations import greek_abbreviations


# Replace potential Greek abbreviations with full forms
def user_query_preprocess(user_query: str) -> str:
    """Replace abbreviations with full forms, preserving unaffected words."""

    def callback(match):
        word = match.group(0)
        word_lower = word.lower()
        word_no_accent = "".join(
            c
            for c in unicodedata.normalize("NFKD", word_lower)
            if not unicodedata.combining(c)
        )
        if word_no_accent in greek_abbreviations:
            return greek_abbreviations[word_no_accent]
        else:
            return word

    return re.sub(r"\b\w+\b", callback, user_query)
