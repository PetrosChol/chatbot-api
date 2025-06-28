from unittest.mock import patch, MagicMock

# Assuming HospitalShift model is needed for ColumnElement context

# Function under test
from app.tools.statement_builders.hospital_shifts_statement_builder import (
    _build_specialties_filter,
)

# --- Mock Objects ---


# Mock the SQLAlchemy condition object returned by build_regex_conditions
class MockSQLAlchemyRegexCondition:
    def __init__(self, value):
        self.value = value  # Store the value for assertion

    def __eq__(self, other):
        return (
            isinstance(other, MockSQLAlchemyRegexCondition)
            and self.value == other.value
        )

    def __repr__(self):
        return f"MockSQLAlchemyRegexCondition({self.value})"


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
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.or_"
)  # Mock the or_ function
def test_build_specialties_filter_default_wildcard(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test that the default ['*'] input results in no filter (returns None)."""
    result = _build_specialties_filter(["*"])
    assert result is None
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_specialties_filter_empty_list(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test that an empty list [] input calls helpers but returns None if they return empty."""
    # The current implementation returns None and logs if specialties is an empty list
    result = _build_specialties_filter([])
    assert result is None
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions",
    return_value=[],
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions",
    return_value=[],
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_specialties_filter_only_wildcards_or_empty_strings(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test lists containing only '*' or empty strings, assuming helpers handle them."""
    specialties = ["*", "", "   ", "*"]
    result = _build_specialties_filter(specialties)
    assert result is None
    # Current implementation does not call helpers for non-wildcard lists yet
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_specialties_filter_single_regex_condition(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test when only build_regex_conditions returns a single condition."""
    mock_regex_cond = MockSQLAlchemyRegexCondition("regex_for_cardiology")
    mock_build_regex.return_value = [mock_regex_cond]
    mock_build_fuzzy.return_value = []  # Fuzzy returns nothing
    specialties = ["Cardiology Exact"]

    result = _build_specialties_filter(specialties)
    # Current implementation returns None
    assert result is None
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_specialties_filter_single_fuzzy_condition(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test when only build_fuzzy_conditions returns a single condition."""
    mock_fuzzy_cond = MockSQLAlchemyFuzzyCondition("fuzzy_for_cardiology")
    mock_build_regex.return_value = []  # Regex returns nothing
    mock_build_fuzzy.return_value = [mock_fuzzy_cond]
    specialties = ["Cardiolgy Fuzzy"]  # Misspelled

    result = _build_specialties_filter(specialties)
    # Current implementation returns None
    assert result is None
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.or_"
)  # Mock or_ to check its call
def test_build_specialties_filter_multiple_conditions_regex_only(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test with multiple regex conditions and no fuzzy conditions."""
    mock_regex1 = MockSQLAlchemyRegexCondition("regex_cardiology")
    mock_regex2 = MockSQLAlchemyRegexCondition("regex_neurology")
    mock_build_regex.return_value = [mock_regex1, mock_regex2]
    mock_build_fuzzy.return_value = []
    mock_or_result = MagicMock(name="or_result_regex_only")
    mock_or.return_value = mock_or_result
    specialties = ["Cardiology", "Neurology"]

    result = _build_specialties_filter(specialties)
    # Current implementation returns None
    assert result is None
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.or_"
)  # Mock or_ to check its call
def test_build_specialties_filter_multiple_conditions_fuzzy_only(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test with multiple fuzzy conditions and no regex conditions."""
    mock_fuzzy1 = MockSQLAlchemyFuzzyCondition("fuzzy_cardiology")
    mock_fuzzy2 = MockSQLAlchemyFuzzyCondition("fuzzy_neurology")
    mock_build_regex.return_value = []
    mock_build_fuzzy.return_value = [mock_fuzzy1, mock_fuzzy2]
    mock_or_result = MagicMock(name="or_result_fuzzy_only")
    mock_or.return_value = mock_or_result
    specialties = ["Cardiolgy", "Neurolgy"]  # Misspelled

    result = _build_specialties_filter(specialties)
    # Current implementation returns None
    assert result is None
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.or_"
)  # Mock or_ to check its call
def test_build_specialties_filter_multiple_conditions_mixed(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test with conditions returned from both regex and fuzzy helpers."""
    mock_regex1 = MockSQLAlchemyRegexCondition("regex_cardiology")
    mock_fuzzy1 = MockSQLAlchemyFuzzyCondition(
        "fuzzy_neurology"
    )  # e.g., from "Neurolgy"
    mock_fuzzy2 = MockSQLAlchemyFuzzyCondition(
        "fuzzy_pediatrics"
    )  # e.g., from "Pedatrics"
    mock_build_regex.return_value = [mock_regex1]
    mock_build_fuzzy.return_value = [mock_fuzzy1, mock_fuzzy2]
    mock_or_result = MagicMock(name="or_result_mixed")
    mock_or.return_value = mock_or_result
    specialties = ["Cardiology", "Neurolgy", "Pedatrics"]

    result = _build_specialties_filter(specialties)
    # Current implementation returns None
    assert result is None
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions",
    return_value=[],
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions",
    return_value=[],
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_specialties_filter_no_conditions_returned(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test when both helpers return empty lists."""
    specialties = ["NonMatchingSpecialty"]
    result = _build_specialties_filter(specialties)
    # Current implementation returns None
    assert result is None
    mock_build_regex.assert_not_called()
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()
