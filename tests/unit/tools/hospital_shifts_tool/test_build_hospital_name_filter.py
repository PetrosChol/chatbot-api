from unittest.mock import patch, MagicMock

from app.core.config import settings  # Import settings

# Assuming HospitalShift model is needed for ColumnElement context
from app.db.models.hospital_shift_model import HospitalShift

# Function under test
from app.tools.statement_builders.hospital_shifts_statement_builder import (
    _build_hospital_name_filter,
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
def test_build_hospital_name_filter_default_wildcard(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test that the default ['*'] input results in no filter (returns None)."""
    result = _build_hospital_name_filter(["*"])
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
def test_build_hospital_name_filter_empty_list(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test that an empty list [] input calls helpers but returns None if they return empty."""
    mock_build_regex.return_value = []
    mock_build_fuzzy.return_value = []
    result = _build_hospital_name_filter([])
    assert result is None
    # Helpers should be called with the empty list and the normalized column
    mock_build_regex.assert_called_once_with(HospitalShift.normalized_hospital_name, [])
    mock_build_fuzzy.assert_called_once_with(
        HospitalShift.normalized_hospital_name, [], threshold=settings.FUZZY_THRESHOLD
    )
    mock_or.assert_not_called()  # No conditions to OR


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions",
    return_value=[],
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions",
    return_value=[],
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_hospital_name_filter_only_wildcards_or_empty_strings(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test lists containing only '*' or empty strings, assuming helpers handle them."""
    names = ["*", "", "   ", "*"]
    result = _build_hospital_name_filter(names)
    assert result is None
    # Expect helpers to be called with the original list and the normalized column
    mock_build_regex.assert_called_once_with(
        HospitalShift.normalized_hospital_name, names
    )
    mock_build_fuzzy.assert_called_once_with(
        HospitalShift.normalized_hospital_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # Since helpers return [], or_ should not be called
    mock_or.assert_not_called()


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_hospital_name_filter_single_regex_condition(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test when only build_regex_conditions returns a single condition."""
    mock_regex_cond = MockSQLAlchemyRegexCondition("regex_for_hospital1")
    mock_build_regex.return_value = [mock_regex_cond]
    mock_build_fuzzy.return_value = []  # Fuzzy returns nothing
    names = ["Hospital One Exact"]

    result = _build_hospital_name_filter(names)

    mock_build_regex.assert_called_once_with(
        HospitalShift.normalized_hospital_name, names
    )
    mock_build_fuzzy.assert_called_once_with(
        HospitalShift.normalized_hospital_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # or_ should NOT be called for a single total condition
    mock_or.assert_not_called()
    # The result should be the single regex condition
    assert result == mock_regex_cond


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_hospital_name_filter_single_fuzzy_condition(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test when only build_fuzzy_conditions returns a single condition."""
    mock_fuzzy_cond = MockSQLAlchemyFuzzyCondition("fuzzy_for_hospital1")
    mock_build_regex.return_value = []  # Regex returns nothing
    mock_build_fuzzy.return_value = [mock_fuzzy_cond]
    names = ["Hospitel One Fuzzy"]

    result = _build_hospital_name_filter(names)

    mock_build_regex.assert_called_once_with(
        HospitalShift.normalized_hospital_name, names
    )
    mock_build_fuzzy.assert_called_once_with(
        HospitalShift.normalized_hospital_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # or_ should NOT be called for a single total condition
    mock_or.assert_not_called()
    # The result should be the single fuzzy condition
    assert result == mock_fuzzy_cond


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.or_"
)  # Mock or_ to check its call
def test_build_hospital_name_filter_multiple_conditions_regex_only(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test with multiple regex conditions and no fuzzy conditions."""
    mock_regex1 = MockSQLAlchemyRegexCondition("regex1")
    mock_regex2 = MockSQLAlchemyRegexCondition("regex2")
    mock_build_regex.return_value = [mock_regex1, mock_regex2]
    mock_build_fuzzy.return_value = []
    mock_or_result = MagicMock(name="or_result_regex_only")
    mock_or.return_value = mock_or_result
    names = ["Hospital Regex 1", "Hospital Regex 2"]

    result = _build_hospital_name_filter(names)

    mock_build_regex.assert_called_once_with(
        HospitalShift.normalized_hospital_name, names
    )
    mock_build_fuzzy.assert_called_once_with(
        HospitalShift.normalized_hospital_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # Expect or_ to be called with the two regex conditions
    mock_or.assert_called_once_with(mock_regex1, mock_regex2)
    assert result == mock_or_result


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.or_"
)  # Mock or_ to check its call
def test_build_hospital_name_filter_multiple_conditions_fuzzy_only(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test with multiple fuzzy conditions and no regex conditions."""
    mock_fuzzy1 = MockSQLAlchemyFuzzyCondition("fuzzy1")
    mock_fuzzy2 = MockSQLAlchemyFuzzyCondition("fuzzy2")
    mock_build_regex.return_value = []
    mock_build_fuzzy.return_value = [mock_fuzzy1, mock_fuzzy2]
    mock_or_result = MagicMock(name="or_result_fuzzy_only")
    mock_or.return_value = mock_or_result
    names = ["Hospital Fuzzy 1", "Hospital Fuzzy 2"]

    result = _build_hospital_name_filter(names)

    mock_build_regex.assert_called_once_with(
        HospitalShift.normalized_hospital_name, names
    )
    mock_build_fuzzy.assert_called_once_with(
        HospitalShift.normalized_hospital_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # Expect or_ to be called with the two fuzzy conditions
    mock_or.assert_called_once_with(mock_fuzzy1, mock_fuzzy2)
    assert result == mock_or_result


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions"
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.or_"
)  # Mock or_ to check its call
def test_build_hospital_name_filter_multiple_conditions_mixed(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test with conditions returned from both regex and fuzzy helpers."""
    mock_regex1 = MockSQLAlchemyRegexCondition("regex1")
    mock_fuzzy1 = MockSQLAlchemyFuzzyCondition("fuzzy1")
    mock_fuzzy2 = MockSQLAlchemyFuzzyCondition("fuzzy2")
    mock_build_regex.return_value = [mock_regex1]
    mock_build_fuzzy.return_value = [mock_fuzzy1, mock_fuzzy2]
    mock_or_result = MagicMock(name="or_result_mixed")
    mock_or.return_value = mock_or_result
    names = ["Hospital Mix 1", "Hospital Mix 2"]

    result = _build_hospital_name_filter(names)

    mock_build_regex.assert_called_once_with(
        HospitalShift.normalized_hospital_name, names
    )
    mock_build_fuzzy.assert_called_once_with(
        HospitalShift.normalized_hospital_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    # Expect or_ to be called with all conditions combined
    mock_or.assert_called_once_with(mock_regex1, mock_fuzzy1, mock_fuzzy2)
    assert result == mock_or_result


@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_fuzzy_conditions",
    return_value=[],
)
@patch(
    "app.tools.statement_builders.hospital_shifts_statement_builder.build_regex_conditions",
    return_value=[],
)
@patch("app.tools.statement_builders.hospital_shifts_statement_builder.or_")
def test_build_hospital_name_filter_no_conditions_returned(
    mock_or, mock_build_regex, mock_build_fuzzy
):
    """Test when both helpers return empty lists."""
    names = ["NonMatchingHospital"]
    result = _build_hospital_name_filter(names)

    mock_build_regex.assert_called_once_with(
        HospitalShift.normalized_hospital_name, names
    )
    mock_build_fuzzy.assert_called_once_with(
        HospitalShift.normalized_hospital_name,
        names,
        threshold=settings.FUZZY_THRESHOLD,
    )
    mock_or.assert_not_called()
    assert result is None  # Should return None if the combined list is empty
