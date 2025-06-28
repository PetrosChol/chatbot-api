import pytest
from unittest.mock import patch
import sys

# Adjust the import path as needed
from app.utils.user_query_preprocess import user_query_preprocess


# Create a mock module for greek_abbreviations using the actual dictionary values
class MockGreekAbbreviations:
    greek_abbreviations = {
        "τρ": "τώρα",
        "σμρ": "σήμερα",
        "αυρ": "αύριο",
        "μθα": "μεθαύριο",
        "σκ": "Σάββατο-Κυριακή (Saturday, Sunday)",
        "πσκ": "Παρασκευή-Σάββατο-Κυριακή (Friday, Saturday, Sunday)",
    }


@pytest.fixture(autouse=True)
def mock_greek_abbreviations_module():
    """Mock the entire greek_abbreviations module with actual dictionary values."""
    # Create a properly structured mock
    mock_module = MockGreekAbbreviations()

    # The important part: patch at the correct import location
    # We need to patch where the function imports from, not where it's defined
    with patch.dict(
        sys.modules,
        {
            "app.utils.greek_abbreviations": mock_module,
            ".greek_abbreviations": mock_module,  # Also patch relative import
            "utils.greek_abbreviations": mock_module,  # Also patch potential absolute import
        },
    ):
        # Also directly patch the greek_abbreviations dictionary in the function's module
        with patch("app.utils.greek_abbreviations", mock_module.greek_abbreviations):
            yield


def test_user_query_preprocess_no_abbreviations():
    """Test that text with no abbreviations remains unchanged."""
    query = "αυτό είναι ένα κείμενο χωρίς συντομογραφίες"
    result = user_query_preprocess(query)
    assert result == query


def test_user_query_preprocess_with_abbreviations():
    """Test that abbreviations are replaced correctly."""
    query = "θέλω να πάω τρ στην παραλία"
    result = user_query_preprocess(query)
    assert result == "θέλω να πάω τώρα στην παραλία"


def test_user_query_preprocess_mixed_case():
    """Test that abbreviations are replaced regardless of case."""
    query = "ΣΜΡ έχω πολλά πράγματα να κάνω"
    result = user_query_preprocess(query)
    assert result == "σήμερα έχω πολλά πράγματα να κάνω"


def test_user_query_preprocess_with_accented_abbreviations():
    """Test handling abbreviations with accents."""
    # Testing with potentially accented variations
    query = "τρ και αύρ έχω μάθημα"
    result = user_query_preprocess(query)
    assert result == "τώρα και αύριο έχω μάθημα"


def test_user_query_preprocess_partial_words():
    """Test that partial matches within words are not replaced."""
    # 'τρ' is an abbreviation but 'πατρίδα' should not be replaced
    query = "η πατρίδα μου είναι τρ εδώ"
    result = user_query_preprocess(query)
    assert result == "η πατρίδα μου είναι τώρα εδώ"


def test_user_query_preprocess_with_punctuation():
    """Test handling of abbreviations near punctuation."""
    query = "σμρ. θα πάω για καφέ, αυρ! θα μείνω σπίτι"
    result = user_query_preprocess(query)
    # Note: The regex \b\w+\b won't include punctuation in the match
    assert result == "σήμερα. θα πάω για καφέ, αύριο! θα μείνω σπίτι"


def test_user_query_preprocess_multiple_abbreviations():
    """Test handling multiple abbreviations in the same query."""
    query = "σμρ έχω διάβασμα, αυρ έχω μάθημα, και το μθα έχω εξέταση"
    result = user_query_preprocess(query)
    assert (
        result == "σήμερα έχω διάβασμα, αύριο έχω μάθημα, και το μεθαύριο έχω εξέταση"
    )


def test_user_query_preprocess_empty_string():
    """Test that empty string input returns empty string."""
    query = ""
    result = user_query_preprocess(query)
    assert result == ""


def test_user_query_preprocess_non_greek():
    """Test handling of non-Greek text."""
    query = "This is English text with no abbreviations"
    result = user_query_preprocess(query)
    assert result == query


def test_user_query_preprocess_mixed_languages():
    """Test handling text with mixed Greek and other languages."""
    query = "I need to go σμρ and come back αυρ"
    result = user_query_preprocess(query)
    assert result == "I need to go σήμερα and come back αύριο"


def test_user_query_preprocess_weekend_abbreviations():
    """Test handling weekend-specific abbreviations."""
    query = "τα σκ πηγαίνω στο χωριό"
    result = user_query_preprocess(query)
    assert result == "τα Σάββατο-Κυριακή (Saturday, Sunday) πηγαίνω στο χωριό"


def test_user_query_preprocess_long_abbreviations():
    """Test handling of longer compound abbreviations."""
    query = "κάθε πσκ πηγαίνω εκδρομή"
    result = user_query_preprocess(query)
    assert (
        result
        == "κάθε Παρασκευή-Σάββατο-Κυριακή (Friday, Saturday, Sunday) πηγαίνω εκδρομή"
    )
