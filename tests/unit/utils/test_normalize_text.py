from app.utils.normalize_text import normalize_text


def test_normalize_text_none():
    """Test that normalize_text returns None when input is None."""
    result = normalize_text(None)
    assert result is None


def test_normalize_text_empty_string():
    """Test that normalize_text handles empty strings correctly."""
    result = normalize_text("")
    assert result == ""


def test_normalize_text_plain_ascii():
    """Test that normalize_text works with plain ASCII text."""
    result = normalize_text("Hello World")
    assert result == "hello world"


def test_normalize_text_mixed_case():
    """Test that normalize_text converts to lowercase."""
    result = normalize_text("UPPER lower MiXeD")
    assert result == "upper lower mixed"


def test_normalize_text_accented_chars():
    """Test that normalize_text removes accents from characters."""
    result = normalize_text("café résumé naïve")
    assert result == "cafe resume naive"


def test_normalize_text_complex_diacritics():
    """Test that normalize_text handles complex diacritics."""
    result = normalize_text("Příliš žluťoučký kůň úpěl ďábelské ódy")
    assert result == "prilis zlutoucky kun upel dabelske ody"


def test_normalize_text_multiple_combining_marks():
    """Test handling of characters with multiple combining marks."""
    # Vietnamese example with multiple diacritics
    result = normalize_text("Tiếng Việt với các dấu phức tạp")
    assert result == "tieng viet voi cac dau phuc tap"


def test_normalize_text_non_latin_scripts():
    """Test behavior with non-Latin scripts."""
    # Greek (accents removed, lowercase, final sigma 'ς' to 'σ')
    result = normalize_text("Ελληνικά κείμενο με τόνους και τελικό σίγμας.")
    # Corrected: Period is removed by punctuation stripper
    assert result == "ελληνικα κειμενο με τονουσ και τελικο σιγμασ"

    # Cyrillic (note: 'й' becomes 'и' since the function removes the breve mark, 'ё' becomes 'е')
    result = normalize_text("Русский ТЕКСТ с буквой Ё ё")
    assert result == "русскии текст с буквои е е"  # This was already correct


def test_normalize_text_special_chars_and_punctuation():
    """Test that normalize_text removes punctuation and handles special chars."""
    # string.punctuation + ';·' are removed.
    # Input: "Special characters: !@#$%^&*()_+-=[]{}|;:,./<>? Greek Q:; Ano Teleia:·"
    # Expected after normalization (lowercase, no accents, punctuation removed):
    # "special characters @ ^ & _ + - = [ ] { } |"
    # Note: # $ % * ( ) ; : , . / < > ? are in string.punctuation and will be removed.
    # Greek question mark (;) and ano teleia (·) are also removed.
    result = normalize_text(
        "Special characters: !@#$%^&*()_+-=[]{}|;:,./<>? Greek Q:; Ano Teleia:· Extra."
    )
    assert result == "special characters greek q ano teleia extra"
