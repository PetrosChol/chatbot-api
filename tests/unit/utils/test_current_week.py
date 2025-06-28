import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from app.utils.current_week import current_week


@pytest.fixture
def mock_datetime_now():
    """Fixture to mock datetime.datetime.now"""
    fixed_date = datetime.datetime(
        2023, 5, 15, 12, 0, 0, tzinfo=ZoneInfo("Europe/Athens")
    )
    with patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_date
        mock_dt.side_effect = datetime.datetime
        mock_dt.timedelta = datetime.timedelta
        yield mock_dt


def test_current_week_internal_date(mock_datetime_now):
    """Test that current_week returns expected 7-day period starting from current date."""
    # Call the function which should use our mocked date (May 15, 2023 - a Monday)
    result = current_week()

    # Expected output based on our fixed date
    expected_lines = [
        "Monday: 2023-05-15",
        "Tuesday: 2023-05-16",
        "Wednesday: 2023-05-17",
        "Thursday: 2023-05-18",
        "Friday: 2023-05-19",
        "Saturday: 2023-05-20",
        "Sunday: 2023-05-21",
    ]
    expected_output = "\n".join(expected_lines)

    # Verify the function produces the expected output
    assert result == expected_output

    # Verify datetime.now was called with the correct timezone
    mock_datetime_now.now.assert_called_once_with(ZoneInfo("Europe/Athens"))
