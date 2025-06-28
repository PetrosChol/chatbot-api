import datetime
from sqlalchemy.sql.elements import BinaryExpression, False_, BindParameter

# Assuming HospitalShift model is accessible for HospitalShift.hospital_shift_date
from app.db.models.hospital_shift_model import HospitalShift
from app.tools.statement_builders.hospital_shifts_statement_builder import (
    _build_hospital_shift_date_filter,
)


# --- Test Cases ---


def test_build_hospital_shift_date_filter_default_wildcard():
    """Test that ["*"] results in no filter (None)."""
    result = _build_hospital_shift_date_filter(["*"])
    assert result is None


def test_build_hospital_shift_date_filter_empty_list():
    """Test that an empty list results in no filter (None)."""
    result = _build_hospital_shift_date_filter([])
    assert result is None


def test_build_hospital_shift_date_filter_wildcard_and_empty_string():
    """Test that ["*", ""] results in no filter (None)."""
    result = _build_hospital_shift_date_filter(["*", ""])
    assert result is None


def test_build_hospital_shift_date_filter_single_valid_date():
    """Test a single valid date string."""
    date_str = "2024-03-20"
    expected_date = datetime.date(2024, 3, 20)
    result = _build_hospital_shift_date_filter([date_str])
    assert isinstance(result, BinaryExpression)
    # Check the right side of the IN clause (a BindParameter holding the list)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)  # The value inside is a list
    assert len(result.right.value) == 1
    assert result.right.value[0] == expected_date
    # Check the left side is the correct column by comparing names
    assert result.left.name == HospitalShift.hospital_shift_date.key


def test_build_hospital_shift_date_filter_multiple_valid_dates():
    """Test multiple valid date strings."""
    date_strs = ["2024-03-20", "2024-03-21"]
    expected_dates = [datetime.date(2024, 3, 20), datetime.date(2024, 3, 21)]
    result = _build_hospital_shift_date_filter(date_strs)
    assert isinstance(result, BinaryExpression)
    # Check the right side of the IN clause (a BindParameter holding the list)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    # Check if the dates in the clause match expected dates (order might vary)
    assert set(result.right.value) == set(expected_dates)
    # Check the left side is the correct column by comparing names
    assert result.left.name == HospitalShift.hospital_shift_date.key


def test_build_hospital_shift_date_filter_single_invalid_date():
    """Test a single invalid date string returns false()."""
    result = _build_hospital_shift_date_filter(["invalid-date-format"])
    assert isinstance(result, False_)  # Should return SQLAlchemy false()


def test_build_hospital_shift_date_filter_mixed_valid_invalid_dates():
    """Test mixed valid and invalid dates, only valid should be included."""
    date_strs = ["2024-03-20", "not-a-date", "2024-03-22"]
    expected_dates = [datetime.date(2024, 3, 20), datetime.date(2024, 3, 22)]
    result = _build_hospital_shift_date_filter(date_strs)
    assert isinstance(result, BinaryExpression)
    # Check the right side of the IN clause (a BindParameter holding the list)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    assert set(result.right.value) == set(expected_dates)
    # Check the left side is the correct column by comparing names
    assert result.left.name == HospitalShift.hospital_shift_date.key


def test_build_hospital_shift_date_filter_mixed_valid_wildcard_empty():
    """Test valid dates mixed with '*' and empty strings."""
    date_strs = ["2024-03-20", "*", "", "2024-03-23"]
    expected_dates = [datetime.date(2024, 3, 20), datetime.date(2024, 3, 23)]
    result = _build_hospital_shift_date_filter(date_strs)
    assert isinstance(result, BinaryExpression)
    # Check the right side of the IN clause (a BindParameter holding the list)
    assert isinstance(result.right, BindParameter)
    assert isinstance(result.right.value, list)
    assert len(result.right.value) == 2
    assert set(result.right.value) == set(expected_dates)
    # Check the left side is the correct column by comparing names
    assert result.left.name == HospitalShift.hospital_shift_date.key


def test_build_hospital_shift_date_filter_only_invalid_dates_attempted():
    """Test that only invalid dates (but not empty/wildcard) return false()."""
    result = _build_hospital_shift_date_filter(
        ["invalid1", "2024/03/20"]
    )  # Wrong format
    assert isinstance(result, False_)


def test_build_hospital_shift_date_filter_no_valid_dates_but_not_attempted():
    """Test that only wildcards/empty strings result in None, not false()."""
    result = _build_hospital_shift_date_filter(["*", "", "*"])
    assert result is None
