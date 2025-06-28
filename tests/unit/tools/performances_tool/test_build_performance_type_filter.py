from unittest.mock import patch

# Assuming Performance model is needed for ColumnElement context
from app.db.models.performance_model import Performance

# Function under test
from app.tools.statement_builders.performances_statement_builder import (
    _build_performance_type_filter,
)

# --- Mock Objects ---


# Mock the SQLAlchemy comparison object returned by build_fuzzy_conditions
class MockSQLAlchemyComparison:
    def __init__(self, value):
        self.value = value  # Store the value for assertion

    def __eq__(self, other):
        return isinstance(other, MockSQLAlchemyComparison) and self.value == other.value

    def __repr__(self):
        return f"MockSQLAlchemyComparison({self.value})"


# --- Test Cases ---


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions"
)
def test_build_performance_type_filter_none_input(mock_build_fuzzy):
    """Test that None input results in no filter (returns None)."""
    result = _build_performance_type_filter(None)
    assert result is None
    mock_build_fuzzy.assert_not_called()


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions"
)
def test_build_performance_type_filter_wildcard_input(mock_build_fuzzy):
    """Test that '*' input results in no filter (returns None)."""
    result = _build_performance_type_filter("*")
    assert result is None
    mock_build_fuzzy.assert_not_called()


def test_build_performance_type_filter_valid_type():
    """Test with a valid type string, expects an exact match condition."""
    perf_type = "musical"
    result = _build_performance_type_filter(perf_type)

    assert result is not None
    assert result.left.name == Performance.performance_type.key
    assert result.right.value == perf_type
    assert result.operator.__name__ == "eq"


def test_build_performance_type_filter_no_fuzzy_conditions_returned():
    """Test when a type is provided but it's not a special case (None, '*', empty)."""
    # This test now checks for exact match behavior
    perf_type = (
        "NonMatchingType"  # Not 'musical' or 'theatrical' but still a valid string
    )
    result = _build_performance_type_filter(perf_type)

    assert result is not None
    assert result.left.name == Performance.performance_type.key
    assert result.right.value == perf_type
    assert result.operator.__name__ == "eq"


def test_build_performance_type_filter_empty_string_input():
    """Test with an empty string input, should result in no filter."""
    perf_type = ""
    result = _build_performance_type_filter(perf_type)
    assert result is None


def test_build_performance_type_filter_greek_type():
    """Test with a Greek type string, expects an exact match condition."""
    perf_type = "Μουσική"  # Greek for Music
    result = _build_performance_type_filter(perf_type)

    assert result is not None
    assert result.left.name == Performance.performance_type.key
    assert result.right.value == perf_type
    assert result.operator.__name__ == "eq"
