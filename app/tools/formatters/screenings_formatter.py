import logging
from typing import List, Tuple, Optional
from collections import defaultdict
import datetime

logger = logging.getLogger(__name__)

# Define a type alias for the expected row structure if needed, or use Dict/Tuple
# Genre and year are now included based on the statement builder
ScreeningRow = Tuple[
    datetime.date, datetime.time, str, str, str, Optional[str], Optional[int]
]
ScreeningRowNoTime = Tuple[
    datetime.date, str, str, Optional[str], Optional[int]
]


def format_screenings(
    screenings: List[ScreeningRow | ScreeningRowNoTime], halls_and_screening_times: bool
) -> str:
    """
    Formats a list of screening results (as tuples) into a human-readable string.

    Args:
        screenings: A list of tuples representing screening data.
                    The structure depends on `halls_and_screening_times`.
        halls_and_screening_times: Boolean indicating if time/hall info is present.

    Returns:
        A formatted string summarizing the screenings, or a message indicating none were found.
    """
    if not screenings:
        return "Δεν βρέθηκαν προβολές ταινιών που να ταιριάζουν με τα κριτήριά σας."

    formatted_lines = ["Βρέθηκαν οι ακόλουθες προβολές ταινιών:"]

    # Group screenings: Date -> Cinema -> Movie -> List of (Time, Hall) or just mark presence
    grouped_screenings = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    if halls_and_screening_times:
        # Expected row: (date, time, movie_name, cinema_name, hall_name, genre, year)
        for i, row_data in enumerate(screenings):
            try:
                # Ensure correct unpacking based on ScreeningRow type alias
                row: ScreeningRow = row_data  # type: ignore
                date_obj, time_obj, movie, cinema, hall, _genre, _year = (
                    row
                )
                date_str = (
                    date_obj.strftime("%d/%m/%Y") if date_obj else "Άγνωστη Ημερομηνία"
                )
                time_str = time_obj.strftime("%H:%M") if time_obj else "Άγνωστη Ώρα"
                hall_str = hall or "Άγνωστη Αίθουσα"
                grouped_screenings[date_str][cinema][movie].append((time_str, hall_str))
            except (TypeError, ValueError, IndexError) as e:
                logger.warning(
                    f"Skipping unexpected row format or content at index {i} in detailed mode: {type(e).__name__}. Row had {len(row_data) if isinstance(row_data, tuple) else 'N/A'} elements."
                )
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Problematic row data: {row_data}", exc_info=True)
                continue
    else:
        for i, row_data in enumerate(screenings):
            try:
                # Ensure correct unpacking based on ScreeningRowNoTime type alias
                row: ScreeningRowNoTime = row_data
                date_obj, movie, cinema, _genre, _year = row 
                date_str = (
                    date_obj.strftime("%d/%m/%Y") if date_obj else "Άγνωστη Ημερομηνία"
                )
                grouped_screenings[date_str][cinema][movie] = True
            except (TypeError, ValueError, IndexError) as e:
                logger.warning(
                    f"Skipping unexpected row format or content at index {i} in summary mode: {type(e).__name__}. Row had {len(row_data) if isinstance(row_data, tuple) else 'N/A'} elements."
                )
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Problematic row data: {row_data}", exc_info=True)
                continue

    # Format the grouped data
    for date_str, cinemas_data in sorted(grouped_screenings.items()):
        formatted_lines.append(f"\n--- {date_str} ---")
        for cinema, movies_data in sorted(cinemas_data.items()):
            formatted_lines.append(f"  Κινηματογράφος: {cinema or 'Άγνωστος'}")
            for movie, details_or_presence in sorted(movies_data.items()):
                movie_name_str = movie or "Άγνωστη Ταινία"
                if halls_and_screening_times:
                    sorted_details = sorted(details_or_presence, key=lambda x: x[0])

                    times_str_parts = [f"{t} ({h})" for t, h in sorted_details]
                    times_str = ", ".join(times_str_parts)

                    formatted_lines.append(f"    - {movie_name_str}: {times_str}")
                else:
                    formatted_lines.append(f"    - {movie_name_str}")

    return "\n".join(formatted_lines)