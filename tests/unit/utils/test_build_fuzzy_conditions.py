from unittest.mock import patch, MagicMock
from sqlalchemy import Column

# Assuming normalize_text exists in app.utils.normalize_text
# Assuming build_fuzzy_conditions exists in app.utils.build_fuzzy_conditions
from app.utils.build_fuzzy_conditions import build_fuzzy_conditions


# Mock for the result of func.similarity(column, term) > threshold
class MockSimilarityComparison:
    def __init__(self, column, term, threshold):
        self.column = column
        self.term = term
        self.threshold = threshold

    def __eq__(self, other):
        return (
            isinstance(other, MockSimilarityComparison)
            and self.column == other.column
            and self.term == other.term
            and self.threshold == other.threshold
        )

    def __repr__(self):
        return f"MockSimilarityComparison(column={self.column!r}, term={self.term!r}, threshold={self.threshold!r})"


# Mock for sqlalchemy.func.similarity
class MockSimilarityFunction:
    def __init__(self, column, term):
        self.column = column
        self.term = term

    def __gt__(self, threshold):
        # Return our custom comparison mock when '>' is used
        return MockSimilarityComparison(self.column, self.term, threshold)

    def __repr__(self):
        return f"MockSimilarityFunction(column={self.column!r}, term={self.term!r})"


# --- Test Cases ---


@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_empty_list(mock_sql_func, mock_norm):
    """Test with an empty list of terms."""
    mock_column = MagicMock(spec=Column)
    mock_column.__str__ = MagicMock(return_value="mock_column")  # For repr if needed
    conditions = build_fuzzy_conditions(mock_column, [])
    assert conditions == []
    mock_norm.assert_not_called()
    mock_sql_func.similarity.assert_not_called()


@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_asterisk_only(mock_sql_func, mock_norm):
    """Test with only the '*' wildcard."""
    mock_column = MagicMock(spec=Column)
    mock_column.__str__ = MagicMock(return_value="mock_column")
    conditions = build_fuzzy_conditions(mock_column, ["*"])
    assert conditions == []
    mock_norm.assert_not_called()  # '*' is filtered out before normalization
    mock_sql_func.similarity.assert_not_called()


@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: x.strip().lower() if x and x.strip() else None,
)
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_empty_strings(mock_sql_func, mock_norm):
    """Test with empty strings or strings containing only whitespace."""
    mock_column = MagicMock(spec=Column)
    mock_column.__str__ = MagicMock(return_value="mock_column")
    conditions = build_fuzzy_conditions(mock_column, ["", "   ", "\t"])
    assert conditions == []
    # Assert normalize was called for non-empty strings ("   ", "\t")
    assert mock_norm.call_count == 2
    mock_sql_func.similarity.assert_not_called()


@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: None if x == "invalid" else x.lower(),
)
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_none_values_from_normalize(mock_sql_func, mock_norm):
    """Test when normalize_text returns None for some inputs."""
    mock_sql_func.similarity.side_effect = MockSimilarityFunction
    mock_column = MagicMock(spec=Column, name="test_col")
    mock_column.__str__ = MagicMock(return_value="test_col")

    terms = ["valid", "invalid", "another_valid"]
    expected_conditions = [
        MockSimilarityComparison(mock_column, "valid", 0.3),
        MockSimilarityComparison(mock_column, "another_valid", 0.3),
    ]
    conditions = build_fuzzy_conditions(mock_column, terms)

    assert conditions == expected_conditions
    assert mock_norm.call_count == len(terms)
    assert mock_sql_func.similarity.call_count == 2  # Only for valid terms


@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_single_term(mock_sql_func, mock_norm):
    """Test with a single valid term."""
    mock_sql_func.similarity.side_effect = MockSimilarityFunction
    mock_column = MagicMock(spec=Column, name="test_col")
    mock_column.__str__ = MagicMock(return_value="test_col")

    expected_conditions = [MockSimilarityComparison(mock_column, "term1", 0.3)]
    conditions = build_fuzzy_conditions(mock_column, ["Term1"])

    assert conditions == expected_conditions
    mock_norm.assert_called_once_with("Term1")
    mock_sql_func.similarity.assert_called_once_with(mock_column, "term1")


@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_multiple_terms(mock_sql_func, mock_norm):
    """Test with multiple valid terms."""
    mock_sql_func.similarity.side_effect = MockSimilarityFunction
    mock_column = MagicMock(spec=Column, name="test_col")
    mock_column.__str__ = MagicMock(return_value="test_col")

    terms = ["Term1", "Term2"]
    expected_conditions = [
        MockSimilarityComparison(mock_column, "term1", 0.3),
        MockSimilarityComparison(mock_column, "term2", 0.3),
    ]
    conditions = build_fuzzy_conditions(mock_column, terms)

    assert conditions == expected_conditions
    assert mock_norm.call_count == len(terms)
    assert mock_sql_func.similarity.call_count == len(terms)


# More realistic mock for normalize_text that handles whitespace stripping
@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: x.strip().lower() if x and x.strip() and x != "*" else None,
)
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_mixed_terms(mock_sql_func, mock_norm):
    """Test with a mix of valid terms, '*', and empty strings."""
    mock_sql_func.similarity.side_effect = MockSimilarityFunction
    mock_column = MagicMock(spec=Column, name="test_col")
    mock_column.__str__ = MagicMock(return_value="test_col")

    terms = [
        "Term1",
        "*",
        "",
        "Term2",
        "   ",
    ]  # Assuming normalize handles "   " -> None
    expected_conditions = [
        MockSimilarityComparison(mock_column, "term1", 0.3),
        MockSimilarityComparison(mock_column, "term2", 0.3),
    ]
    conditions = build_fuzzy_conditions(mock_column, terms)

    assert conditions == expected_conditions
    # Normalize called for "Term1", "Term2", "   " but returns None for "   "
    # "*" and "" are filtered out before normalize_text is called.
    assert mock_norm.call_count == 3
    # Similarity called only for terms where normalize_text returned a non-None value ("term1", "term2")
    assert mock_sql_func.similarity.call_count == 2


@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_custom_threshold(mock_sql_func, mock_norm):
    """Test with a custom similarity threshold."""
    mock_sql_func.similarity.side_effect = MockSimilarityFunction
    mock_column = MagicMock(spec=Column, name="test_col")
    mock_column.__str__ = MagicMock(return_value="test_col")
    custom_threshold = 0.5

    terms = ["Term1"]
    expected_conditions = [
        MockSimilarityComparison(mock_column, "term1", custom_threshold)
    ]
    conditions = build_fuzzy_conditions(mock_column, terms, threshold=custom_threshold)

    assert conditions == expected_conditions
    mock_norm.assert_called_once_with("Term1")
    mock_sql_func.similarity.assert_called_once_with(mock_column, "term1")


@patch(
    "app.utils.build_fuzzy_conditions.normalize_text",
    side_effect=lambda x: x.upper() if x else None,
)  # Example: normalize to upper
@patch("app.utils.build_fuzzy_conditions.func")
def test_build_fuzzy_conditions_normalization_effect(mock_sql_func, mock_norm):
    """Test that the result of normalize_text is used."""
    mock_sql_func.similarity.side_effect = MockSimilarityFunction
    mock_column = MagicMock(spec=Column, name="test_col")
    mock_column.__str__ = MagicMock(return_value="test_col")

    terms = ["term1"]
    # Expect the normalized term (uppercase in this mock)
    expected_conditions = [MockSimilarityComparison(mock_column, "TERM1", 0.3)]
    conditions = build_fuzzy_conditions(mock_column, terms)

    assert conditions == expected_conditions
    mock_norm.assert_called_once_with("term1")
    mock_sql_func.similarity.assert_called_once_with(mock_column, "TERM1")
