import unicodedata
import re
import string


def normalize_text(text: str | None) -> str | None:
    """
    Normalizes a Greek string for database storage or searching.

    Args:
        text: The input string (potentially containing Greek characters) or None.

    Returns:
        The normalized string, or None if the input was None.
        Returns an empty string if the input is an empty string.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            raise TypeError("Input must be a string or convertible to a string.")

    if not text:
        return ""

    try:
        # 1. Unicode Normalization 
        normalized_text = unicodedata.normalize("NFC", text)

        # 2. Convert to lowercase
        normalized_text = normalized_text.lower()

        # 3. Remove accents/diacritics
        decomposed = unicodedata.normalize("NFD", normalized_text)
        # Filter out characters in the 'Mn' (Mark, Nonspacing) category
        no_accents = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
        # The string is now composed of base characters only
        normalized_text = no_accents

        # 4. Convert final sigma (ς) to medial sigma (σ)
        normalized_text = normalized_text.replace("ς", "σ")

        # 5. Remove common punctuation
        # Includes standard ASCII punctuation + Greek question mark (U+037E) ';'
        # + Greek ano teleia (U+0387) '·'
        # Note: The Greek question mark looks like an English semicolon!
        punctuation_to_remove = string.punctuation + ";·"
        # Create a translation table mapping punctuation chars to None (removal)
        translator = str.maketrans("", "", punctuation_to_remove)
        normalized_text = normalized_text.translate(translator)

        # 6. Whitespace Handling
        normalized_text = normalized_text.strip()
        # Collapse multiple whitespace chars (including spaces, tabs, newlines) to single space
        normalized_text = re.sub(r"\s+", " ", normalized_text)

        return normalized_text

    except Exception as e:
        print(f"Error normalizing text: '{text}'. Error: {e}")
        return text.lower().strip()
