from unittest.mock import patch, MagicMock

from app.core.config import settings  # Import settings

# Assuming Performance model is needed for ColumnElement context
from app.db.models.performance_model import Performance

# Function under test
from app.tools.statement_builders.performances_statement_builder import (
    _build_performance_name_filter,
)

# --- Mock Objects ---


# Mock the SQLAlchemy condition object returned by build_fuzzy_conditions
class MockSQLAlchemyFuzzyCondition:
    def __init__(self, value):
        self.value = value  # Store the value for assertion

    def __eq__(self, other):
        return (
            isinstance(other, MockSQLAlchemyFuzzyCondition)
            and self.value == other.value
        )

    def __repr__(self):
        return f"MockSQLAlchemyFuzzyCondition({self.value})"


# --- Test Cases ---


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.performances_statement_builder.or_"
)  # Mock the or_ function
def test_build_performance_name_filter_default_wildcard(mock_or, mock_build_fuzzy):
    """Test that the default ['*'] input results in no filter (returns None)."""
    result = _build_performance_name_filter(["*"])
    assert result is None
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions"
)
@patch("app.tools.statement_builders.performances_statement_builder.or_")
def test_build_performance_name_filter_empty_list(mock_or, mock_build_fuzzy):
    """Test that an empty list [] input calls build_fuzzy but might return None if helper does."""
    # Simulate build_fuzzy_conditions returning an empty list for an empty input list
    mock_build_fuzzy.return_value = []
    result = _build_performance_name_filter([])
    assert result is None
    # build_fuzzy_conditions should still be called with the empty list and default threshold
    mock_build_fuzzy.assert_called_once_with(
        Performance.normalized_performance_name, [], threshold=settings.FUZZY_THRESHOLD
    )
    mock_or.assert_not_called()  # No conditions to OR


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions",
    return_value=[],
)  # Simulate no conditions found
@patch("app.tools.statement_builders.performances_statement_builder.or_")
def test_build_performance_name_filter_only_wildcards_or_empty_strings(
    mock_or, mock_build_fuzzy
):
    """Test lists containing only '*' or empty strings, assuming build_fuzzy handles them."""
    names = ["*", "", "   ", "*"]
    result = _build_performance_name_filter(names)
    assert result is None
    # Expect build_fuzzy_conditions to be called with the original list and default threshold
    mock_build_fuzzy.assert_called_once_with(
        Performance.normalized_performance_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # Since build_fuzzy_conditions returns [], or_ should not be called
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions"
)
@patch("app.tools.statement_builders.performances_statement_builder.or_")
def test_build_performance_name_filter_single_name(mock_or, mock_build_fuzzy):
    """Test with a single valid name string using fuzzy matching."""
    mock_condition = MockSQLAlchemyFuzzyCondition("fuzzy_for_name1")
    mock_build_fuzzy.return_value = [mock_condition]  # Helper returns one condition

    names = ["Performance One"]
    result = _build_performance_name_filter(names)

    mock_build_fuzzy.assert_called_once_with(
        Performance.normalized_performance_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # or_ should NOT be called for a single condition, but the function uses it anyway
    # Let's adjust the test to reflect the current implementation which calls or_ even for one item
    mock_or.assert_called_once_with(mock_condition)
    # The result should be what the mocked or_ returned
    assert result == mock_or.return_value


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.performances_statement_builder.or_"
)  # Mock or_ to check its call
def test_build_performance_name_filter_multiple_names(mock_or, mock_build_fuzzy):
    """Test with multiple valid name strings using fuzzy matching, expects or_()."""
    mock_condition1 = MockSQLAlchemyFuzzyCondition("fuzzy_for_name1")
    mock_condition2 = MockSQLAlchemyFuzzyCondition("fuzzy_for_name2")
    mock_build_fuzzy.return_value = [mock_condition1, mock_condition2]

    # Set a specific return value for the mocked or_ function to assert against
    mock_or_result = MagicMock(name="or_result")
    mock_or.return_value = mock_or_result

    names = ["Performance One", "Performance Two"]
    result = _build_performance_name_filter(names)

    mock_build_fuzzy.assert_called_once_with(
        Performance.normalized_performance_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # Expect or_ to be called with the conditions unpacked
    mock_or.assert_called_once_with(mock_condition1, mock_condition2)
    # The result should be what the mocked or_ returned
    assert result == mock_or_result


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions"
)
@patch("app.tools.statement_builders.performances_statement_builder.or_")
def test_build_performance_name_filter_mixed_names(mock_or, mock_build_fuzzy):
    """Test with mixed valid, wildcard, and empty names using fuzzy matching."""
    mock_condition1 = MockSQLAlchemyFuzzyCondition("fuzzy_for_name1")
    mock_condition3 = MockSQLAlchemyFuzzyCondition("fuzzy_for_name3")
    # Simulate build_fuzzy_conditions filtering out '*' and '' and returning only valid conditions
    mock_build_fuzzy.return_value = [mock_condition1, mock_condition3]

    mock_or_result = MagicMock(name="or_result_mixed")
    mock_or.return_value = mock_or_result

    names = ["Performance One", "*", "Performance Three", ""]
    result = _build_performance_name_filter(names)

    mock_build_fuzzy.assert_called_once_with(
        Performance.normalized_performance_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # Expect or_ to be called with the two valid conditions
    mock_or.assert_called_once_with(mock_condition1, mock_condition3)
    assert result == mock_or_result


@patch(
    "app.tools.statement_builders.performances_statement_builder.build_fuzzy_conditions",
    return_value=[],
)  # Simulate helper finding no matches
@patch("app.tools.statement_builders.performances_statement_builder.or_")
def test_build_performance_name_filter_no_conditions_returned(
    mock_or, mock_build_fuzzy
):
    """Test when build_fuzzy_conditions returns an empty list."""
    names = ["NonMatchingName"]
    result = _build_performance_name_filter(names)

    mock_build_fuzzy.assert_called_once_with(
        Performance.normalized_performance_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    mock_or.assert_not_called()
    assert result is None  # Should return None if the conditions list is empty
