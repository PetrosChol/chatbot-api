import datetime
from sqlalchemy.sql.elements import BinaryExpression, False_, BindParameter

# Assuming Performance model is accessible for Performance.performance_date
from app.db.models.performance_model import Performance
from app.tools.statement_builders.performances_statement_builder import (
    _build_performance_date_filter,
)


# --- Test Cases ---


def test_build_performance_date_filter_default_wildcard():
    """Test that ["*"] results in no filter (None)."""
    result = _build_performance_date_filter(["*"])
    assert result is None


def test_build_performance_date_filter_empty_list():
    """Test that an empty list results in no filter (None)."""
    result = _build_performance_date_filter([])
    assert result is None


def test_build_performance_date_filter_wildcard_and_empty_string():
    """Test that ["*", ""] results in no filter (None)."""
    result = _build_performance_date_filter(["*", ""])
    assert result is None


def test_build_performance_date_filter_single_valid_date():
    """Test a single valid date string."""
    date_str = "2024-03-10"
    expected_date = datetime.date(2024, 3, 10)
    result = _build_performance_date_filter([date_str])
    assert isinstance(result, BinaryExpression)
    # Check the right side of the IN clause (a BindParameter holding the list)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)  # The value inside is a list
    assert len(result.right.value) == 1
    assert result.right.value[0] == expected_date
    # Check the left side is the correct column by comparing keys
    assert result.left.key == Performance.performance_date.key


def test_build_performance_date_filter_multiple_valid_dates():
    """Test multiple valid date strings."""
    date_strs = ["2024-03-10", "2024-03-11"]
    expected_dates = [datetime.date(2024, 3, 10), datetime.date(2024, 3, 11)]
    result = _build_performance_date_filter(date_strs)
    assert isinstance(result, BinaryExpression)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    # Check if the dates in the clause match expected dates (order might vary)
    assert set(result.right.value) == set(expected_dates)
    assert result.left.key == Performance.performance_date.key


def test_build_performance_date_filter_single_invalid_date():
    """Test a single invalid date string returns false()."""
    result = _build_performance_date_filter(["invalid-date-format"])
    assert isinstance(result, False_)  # Should return SQLAlchemy false()


def test_build_performance_date_filter_mixed_valid_invalid_dates():
    """Test mixed valid and invalid dates, only valid should be included."""
    date_strs = ["2024-03-10", "invalid-date", "2024-03-12"]
    expected_dates = [datetime.date(2024, 3, 10), datetime.date(2024, 3, 12)]
    result = _build_performance_date_filter(date_strs)
    assert isinstance(result, BinaryExpression)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    assert set(result.right.value) == set(expected_dates)
    assert result.left.key == Performance.performance_date.key


def test_build_performance_date_filter_mixed_valid_wildcard_empty():
    """Test valid dates mixed with '*' and empty strings."""
    date_strs = ["2024-03-10", "*", "", "2024-03-13"]
    expected_dates = [datetime.date(2024, 3, 10), datetime.date(2024, 3, 13)]
    result = _build_performance_date_filter(date_strs)
    assert isinstance(result, BinaryExpression)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    assert set(result.right.value) == set(expected_dates)
    assert result.left.key == Performance.performance_date.key


def test_build_performance_date_filter_only_invalid_dates_attempted():
    """Test that only invalid dates (but not empty/wildcard) return false()."""
    result = _build_performance_date_filter(["invalid1", "2024/12/31"])  # Wrong format
    assert isinstance(result, False_)


def test_build_performance_date_filter_no_valid_dates_but_not_attempted():
    """Test that only wildcards/empty strings result in None, not false()."""
    result = _build_performance_date_filter(["*", "", "*"])
    assert result is None
