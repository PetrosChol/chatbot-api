import datetime
from unittest.mock import patch
from sqlalchemy.sql.elements import BinaryExpression, False_, BindParameter

# Assuming models are accessible for column context
from app.db.models.cinema_models import Screening
from app.tools.statement_builders.movies_statement_builder import (
    _build_screening_date_filter,
)

# --- Test Cases ---


def test_build_screening_date_filter_default_wildcard():
    """Test that ["*"] results in no filter (None)."""
    result = _build_screening_date_filter(["*"])
    assert result is None


def test_build_screening_date_filter_empty_list():
    """Test that an empty list results in no filter (None)."""
    result = _build_screening_date_filter([])
    assert result is None


def test_build_screening_date_filter_wildcard_and_empty_string():
    """Test that ["*", ""] results in no filter (None)."""
    result = _build_screening_date_filter(["*", ""])
    assert result is None


@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_screening_date_filter_single_valid_date(mock_logger):
    """Test a single valid date string."""
    date_str = "2024-05-10"
    expected_date = datetime.date(2024, 5, 10)
    result = _build_screening_date_filter([date_str])

    assert isinstance(result, BinaryExpression)
    # Check the right side of the IN clause (a BindParameter holding the list)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)  # The value inside is a list
    assert len(result.right.value) == 1
    assert result.right.value[0] == expected_date
    # Check the left side is the correct column by comparing names/keys
    assert result.left.key == Screening.screening_date.key
    mock_logger.info.assert_called_once()
    # Check for the repr() of the list in the log message
    assert repr([expected_date]) in mock_logger.info.call_args[0][0]


@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_screening_date_filter_multiple_valid_dates(mock_logger):
    """Test multiple valid date strings."""
    date_strs = ["2024-05-10", "2024-05-11"]
    expected_dates = [datetime.date(2024, 5, 10), datetime.date(2024, 5, 11)]
    result = _build_screening_date_filter(date_strs)

    assert isinstance(result, BinaryExpression)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    assert set(result.right.value) == set(expected_dates)
    assert result.left.key == Screening.screening_date.key
    mock_logger.info.assert_called_once()
    # Check for the repr() of the list in the log message
    assert repr(expected_dates) in mock_logger.info.call_args[0][0]


@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_screening_date_filter_single_invalid_date(mock_logger):
    """Test a single invalid date string returns false()."""
    invalid_date_str = "invalid-date"
    result = _build_screening_date_filter([invalid_date_str])

    assert isinstance(result, False_)  # Should return SQLAlchemy false()
    mock_logger.warning.assert_any_call(
        f"Invalid screening date format skipped: '{invalid_date_str}'"
    )
    mock_logger.warning.assert_any_call(
        f"Invalid screening date formats found: ['{invalid_date_str}']"
    )
    mock_logger.warning.assert_any_call(
        "Screening date filter provided but no valid dates found."
    )


@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_screening_date_filter_mixed_valid_invalid_dates(mock_logger):
    """Test mixed valid and invalid dates, only valid should be included."""
    invalid_date_str = "invalid-date"
    valid_date_str1 = "2024-05-10"
    valid_date_str2 = "2024-05-12"
    date_strs = [valid_date_str1, invalid_date_str, valid_date_str2]
    expected_dates = [datetime.date(2024, 5, 10), datetime.date(2024, 5, 12)]
    result = _build_screening_date_filter(date_strs)

    assert isinstance(result, BinaryExpression)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    assert set(result.right.value) == set(expected_dates)
    assert result.left.key == Screening.screening_date.key
    mock_logger.warning.assert_any_call(
        f"Invalid screening date format skipped: '{invalid_date_str}'"
    )
    mock_logger.warning.assert_any_call(
        f"Invalid screening date formats found: ['{invalid_date_str}']"
    )
    mock_logger.info.assert_called_once()
    # Check for the repr() of the list in the log message
    assert repr(expected_dates) in mock_logger.info.call_args[0][0]


@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_screening_date_filter_mixed_valid_wildcard_empty(mock_logger):
    """Test valid dates mixed with '*' and empty strings."""
    valid_date_str1 = "2024-05-10"
    valid_date_str2 = "2024-05-13"
    date_strs = [valid_date_str1, "*", "", valid_date_str2]
    expected_dates = [datetime.date(2024, 5, 10), datetime.date(2024, 5, 13)]
    result = _build_screening_date_filter(date_strs)

    assert isinstance(result, BinaryExpression)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    assert set(result.right.value) == set(expected_dates)
    assert result.left.key == Screening.screening_date.key
    mock_logger.info.assert_called_once()
    # Check for the repr() of the list in the log message
    assert repr(expected_dates) in mock_logger.info.call_args[0][0]


@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_screening_date_filter_only_invalid_dates_attempted(mock_logger):
    """Test that only invalid dates (but not empty/wildcard) return false()."""
    invalid_date_str1 = "invalid1"
    invalid_date_str2 = "2024/05/10"  # Wrong format
    result = _build_screening_date_filter([invalid_date_str1, invalid_date_str2])

    assert isinstance(result, False_)
    mock_logger.warning.assert_any_call(
        f"Invalid screening date format skipped: '{invalid_date_str1}'"
    )
    mock_logger.warning.assert_any_call(
        f"Invalid screening date format skipped: '{invalid_date_str2}'"
    )
    mock_logger.warning.assert_any_call(
        f"Invalid screening date formats found: ['{invalid_date_str1}', '{invalid_date_str2}']"
    )
    mock_logger.warning.assert_any_call(
        "Screening date filter provided but no valid dates found."
    )


def test_build_screening_date_filter_no_valid_dates_but_not_attempted():
    """Test that only wildcards/empty strings result in None, not false()."""
    result = _build_screening_date_filter(["*", "", "*"])
    assert result is None
