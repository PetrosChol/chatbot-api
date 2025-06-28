import pytest
from datetime import date, time
from typing import List, Any
from app.tools.formatters.screenings_formatter import (
    format_screenings,
    ScreeningRow,
    ScreeningRowNoTime,
)
import logging


# Helper to capture log messages
@pytest.fixture
def caplog_debug(caplog):
    caplog.set_level(logging.DEBUG)
    return caplog


def test_format_screenings_empty():
    """Tests formatting with an empty list of screenings."""
    assert (
        format_screenings([], halls_and_screening_times=True)
        == "Δεν βρέθηκαν προβολές ταινιών που να ταιριάζουν με τα κριτήριά σας."
    )
    assert (
        format_screenings([], halls_and_screening_times=False)
        == "Δεν βρέθηκαν προβολές ταινιών που να ταιριάζουν με τα κριτήριά σας."
    )


# --- Tests for detailed mode (halls_and_screening_times=True) ---
def test_format_screenings_detailed_single_full():
    """Detailed mode: single screening with all details."""
    screenings: List[ScreeningRow] = [
        (
            date(2023, 10, 26),
            time(20, 0),
            "Ταινία Α",
            "Σινεμά Χ",
            "Αίθουσα 1",
            "Δράμα",
            2022,
        )
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες προβολές ταινιών:\n"
        "\n--- 26/10/2023 ---\n"
        "  Κινηματογράφος: Σινεμά Χ\n"
        "    - Ταινία Α: 20:00 (Αίθουσα 1)"
    )
    assert format_screenings(screenings, halls_and_screening_times=True) == expected


def test_format_screenings_detailed_optional_none():
    """Detailed mode: optional fields are None."""
    screenings: List[ScreeningRow] = [
        (None, None, None, None, None, None, None)  # type: ignore
        # Using type: ignore as None is not strictly date/time but testing formatter's handling
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες προβολές ταινιών:\n"
        "\n--- Άγνωστη Ημερομηνία ---\n"
        "  Κινηματογράφος: Άγνωστος\n"
        "    - Άγνωστη Ταινία: Άγνωστη Ώρα (Άγνωστη Αίθουσα)"
    )
    # Cast to Any to satisfy type checker for this specific test case of Nones
    assert format_screenings(screenings, halls_and_screening_times=True) == expected


def test_format_screenings_detailed_multiple_times_same_movie():
    """Detailed mode: multiple times/halls for the same movie, testing time sorting."""
    screenings: List[ScreeningRow] = [
        (
            date(2023, 10, 26),
            time(22, 0),
            "Ταινία Β",
            "Σινεμά Υ",
            "Αίθουσα 2",
            "Κωμωδία",
            2023,
        ),
        (
            date(2023, 10, 26),
            time(19, 30),
            "Ταινία Β",
            "Σινεμά Υ",
            "Αίθουσα 1",
            "Κωμωδία",
            2023,
        ),
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες προβολές ταινιών:\n"
        "\n--- 26/10/2023 ---\n"
        "  Κινηματογράφος: Σινεμά Υ\n"
        "    - Ταινία Β: 19:30 (Αίθουσα 1), 22:00 (Αίθουσα 2)"
    )
    assert format_screenings(screenings, halls_and_screening_times=True) == expected


def test_format_screenings_detailed_multiple_movies_cinemas_dates():
    """Detailed mode: complex scenario with multiple movies, cinemas, and dates."""
    screenings: List[ScreeningRow] = [
        (
            date(2023, 10, 27),
            time(21, 0),
            "Ταινία Γ",
            "Σινεμά Ζ",
            "Αίθουσα VIP",
            "Sci-Fi",
            2021,
        ),
        (
            date(2023, 10, 26),
            time(20, 0),
            "Ταινία Α",
            "Σινεμά Χ",
            "Αίθουσα 1",
            "Δράμα",
            2022,
        ),
        (
            date(2023, 10, 26),
            time(22, 30),
            "Ταινία Α",
            "Σινεμά Χ",
            "Αίθουσα 1",
            "Δράμα",
            2022,
        ),
        (
            date(2023, 10, 26),
            time(19, 0),
            "Ταινία Δ",
            "Σινεμά Χ",
            "Αίθουσα 2",
            "Δράση",
            2023,
        ),
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες προβολές ταινιών:\n"
        "\n--- 26/10/2023 ---\n"
        "  Κινηματογράφος: Σινεμά Χ\n"
        "    - Ταινία Α: 20:00 (Αίθουσα 1), 22:30 (Αίθουσα 1)\n"
        "    - Ταινία Δ: 19:00 (Αίθουσα 2)\n"
        "\n--- 27/10/2023 ---\n"
        "  Κινηματογράφος: Σινεμά Ζ\n"
        "    - Ταινία Γ: 21:00 (Αίθουσα VIP)"
    )
    assert format_screenings(screenings, halls_and_screening_times=True) == expected


def test_format_screenings_detailed_malformed_row_value_error(caplog_debug: Any):
    """Detailed mode: malformed row (not enough elements) triggering ValueError/IndexError."""
    # ScreeningRow expects 7 elements
    screenings: List[Any] = [
        (date(2023, 10, 26), time(20, 0), "Ταινία Α")  # Missing elements
    ]
    format_screenings(screenings, halls_and_screening_times=True)
    assert (
        "Skipping unexpected row format or content at index 0 in detailed mode"
        in caplog_debug.text
    )
    assert (
        "Problematic row data: (datetime.date(2023, 10, 26), datetime.time(20, 0), 'Ταινία Α')"
        in caplog_debug.text
    )


def test_format_screenings_detailed_malformed_row_type_error(caplog_debug: Any):
    """Detailed mode: malformed row (wrong type, e.g. not a tuple) triggering TypeError."""
    screenings: List[Any] = ["not a tuple"]
    format_screenings(screenings, halls_and_screening_times=True)
    assert (
        "Skipping unexpected row format or content at index 0 in detailed mode"
        in caplog_debug.text
    )
    assert "Problematic row data: not a tuple" in caplog_debug.text


# --- Tests for summary mode (halls_and_screening_times=False) ---
def test_format_screenings_summary_single_full():
    """Summary mode: single screening."""
    # ScreeningRowNoTime = Tuple[datetime.date, str, str, Optional[str], Optional[int]]
    screenings: List[ScreeningRowNoTime] = [
        (date(2023, 10, 26), "Ταινία Α", "Σινεμά Χ", "Δράμα", 2022)
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες προβολές ταινιών:\n"
        "\n--- 26/10/2023 ---\n"
        "  Κινηματογράφος: Σινεμά Χ\n"
        "    - Ταινία Α"
    )
    assert format_screenings(screenings, halls_and_screening_times=False) == expected


def test_format_screenings_summary_optional_none():
    """Summary mode: optional fields are None."""
    screenings: List[ScreeningRowNoTime] = [
        (None, None, None, None, None)  # type: ignore
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες προβολές ταινιών:\n"
        "\n--- Άγνωστη Ημερομηνία ---\n"
        "  Κινηματογράφος: Άγνωστος\n"
        "    - Άγνωστη Ταινία"
    )
    assert format_screenings(screenings, halls_and_screening_times=False) == expected


def test_format_screenings_summary_multiple_movies_cinemas_dates():
    """Summary mode: complex scenario with multiple movies, cinemas, and dates."""
    screenings: List[ScreeningRowNoTime] = [
        (date(2023, 10, 27), "Ταινία Γ", "Σινεμά Ζ", "Sci-Fi", 2021),
        (date(2023, 10, 26), "Ταινία Α", "Σινεμά Χ", "Δράμα", 2022),
        (
            date(2023, 10, 26),
            "Ταινία Δ",
            "Σινεμά Χ",
            "Δράση",
            2023,
        ),  # Different movie, same cinema/date
        (
            date(2023, 10, 26),
            "Ταινία Α",
            "Σινεμά Ω",
            "Δράμα",
            2022,
        ),  # Same movie, different cinema
    ]
    expected = (
        "Βρέθηκαν οι ακόλουθες προβολές ταινιών:\n"
        "\n--- 26/10/2023 ---\n"
        "  Κινηματογράφος: Σινεμά Χ\n"
        "    - Ταινία Α\n"
        "    - Ταινία Δ\n"
        "  Κινηματογράφος: Σινεμά Ω\n"
        "    - Ταινία Α\n"
        "\n--- 27/10/2023 ---\n"
        "  Κινηματογράφος: Σινεμά Ζ\n"
        "    - Ταινία Γ"
    )
    assert format_screenings(screenings, halls_and_screening_times=False) == expected


def test_format_screenings_summary_malformed_row_value_error(caplog_debug: Any):
    """Summary mode: malformed row (not enough elements) triggering ValueError/IndexError."""
    # ScreeningRowNoTime expects 5 elements
    screenings: List[Any] = [(date(2023, 10, 26), "Ταινία Α")]  # Missing elements
    format_screenings(screenings, halls_and_screening_times=False)
    assert (
        "Skipping unexpected row format or content at index 0 in summary mode"
        in caplog_debug.text
    )
    assert (
        "Problematic row data: (datetime.date(2023, 10, 26), 'Ταινία Α')"
        in caplog_debug.text
    )


def test_format_screenings_summary_malformed_row_type_error(caplog_debug: Any):
    """Summary mode: malformed row (wrong type) triggering TypeError."""
    screenings: List[Any] = [12345]  # Not a tuple
    format_screenings(screenings, halls_and_screening_times=False)
    assert (
        "Skipping unexpected row format or content at index 0 in summary mode"
        in caplog_debug.text
    )
    assert "Problematic row data: 12345" in caplog_debug.text


def test_format_screenings_detailed_logging_enabled(caplog_debug: Any):
    """Detailed mode: Ensure debug logging for problematic row data works if enabled."""
    # This test relies on the logger level being DEBUG, which caplog_debug fixture ensures.
    screenings: List[Any] = [(date(2023, 10, 26),)]  # Malformed row
    format_screenings(screenings, halls_and_screening_times=True)
    assert (
        "Skipping unexpected row format or content at index 0 in detailed mode"
        in caplog_debug.text
    )
    # Check if the detailed exception info is logged (part of the default logging for exceptions)
    assert "Problematic row data: (datetime.date(2023, 10, 26),)" in caplog_debug.text
    # The actual exception type (e.g., IndexError) should be in the log message from the formatter
    assert (
        "IndexError" in caplog_debug.text or "ValueError" in caplog_debug.text
    )  # Depending on exact unpacking failure


def test_format_screenings_summary_logging_enabled(caplog_debug: Any):
    """Summary mode: Ensure debug logging for problematic row data works if enabled."""
    screenings: List[Any] = [(date(2023, 10, 26),)]  # Malformed row
    format_screenings(screenings, halls_and_screening_times=False)
    assert (
        "Skipping unexpected row format or content at index 0 in summary mode"
        in caplog_debug.text
    )
    assert "Problematic row data: (datetime.date(2023, 10, 26),)" in caplog_debug.text
    assert "IndexError" in caplog_debug.text or "ValueError" in caplog_debug.text
