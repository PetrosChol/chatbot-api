import logging
import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_, ColumnElement, false, Select

from app.db.models.hospital_shift_model import HospitalShift
from app.utils.build_regex_conditions import build_regex_conditions
from app.utils.build_fuzzy_conditions import build_fuzzy_conditions
from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_hospital_shift_date_filter(
    hospital_shift_dates: List[str],
) -> Optional[ColumnElement[bool]]:
    """
    Parses hospital shift date strings and builds an 'IN' condition.
    Handles "*" wildcard within the list (ignored).
    Returns None if no valid date filters should be applied.
    Returns false() if dates were provided but none were valid (prevents matching).
    """
    if hospital_shift_dates == ["*"]:
        return None

    valid_dates = []
    has_attempted_dates = False
    invalid_formats_found = []

    for date_str in hospital_shift_dates:
        if date_str == "*" or not date_str:
            continue
        has_attempted_dates = True
        try:
            # Convert 'YYYY-MM-DD' string to date object
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            valid_dates.append(date_obj)
        except ValueError:
            invalid_formats_found.append(date_str)
            logger.warning(f"Invalid hospital shift date format skipped: '{date_str}'")

    if invalid_formats_found:
        logger.warning(
            f"Invalid date formats found in input: {invalid_formats_found}. These dates were skipped."
        )

    if valid_dates:
        logger.info(f"Applying hospital shift date filter for: {valid_dates}")
        return HospitalShift.hospital_shift_date.in_(valid_dates)
    elif has_attempted_dates:
        logger.warning(
            "Hospital shift date filter provided but contained no valid dates. Query will yield no results based on date."
        )
        return false()
    else:
        return None


def _build_hospital_name_filter(
    hospital_names: List[str],
) -> Optional[ColumnElement[bool]]:
    """
    Builds hospital name filter conditions using regex helper.
    Builds hospital name filter conditions using both regex and fuzzy matching helpers.
    Handles "*" wildcard within the list (ignored by helpers assumed).
    Combines all valid conditions (regex + fuzzy) with OR.
    Returns None if no name filters should be applied.
    """
    if hospital_names == ["*"]:
        return None

    regex_conditions = build_regex_conditions(
        HospitalShift.normalized_hospital_name, hospital_names
    )
    # Define a threshold for fuzzy matching, could be configurable
    fuzzy_threshold = settings.FUZZY_THRESHOLD
    fuzzy_conditions = build_fuzzy_conditions(
        HospitalShift.normalized_hospital_name,
        hospital_names,
        threshold=fuzzy_threshold,
    )

    # Combine all conditions (regex + fuzzy)
    all_conditions = regex_conditions + fuzzy_conditions

    if not all_conditions:
        logger.info(
            "No valid hospital name conditions found for regex or fuzzy matching."
        )
        return None

    if len(all_conditions) == 1:
        logger.info("Applying single hospital name filter condition (regex or fuzzy).")
        return all_conditions[0]
    else:
        logger.info(
            f"Applying {len(all_conditions)} hospital name filter conditions (regex + fuzzy) combined with OR."
        )
        return or_(*all_conditions)


def _build_specialties_filter(
    specialties: List[str],
) -> Optional[ColumnElement[bool]]:
    """
    Builds filter conditions for HospitalShift.specialties.
    Currently, this function is a placeholder and always returns None,
    meaning no specialty filter will be applied.
    Handles "*" wildcard within the list (ignored).
    Returns None if no specialty filters should be applied.
    """
    # Placeholder: Always return None to not filter by specialties yet.
    # This means queries will return shifts for all specialties.
    if (
        specialties == ["*"] or not specialties or specialties == []
    ): 
        logger.info(
            "No specific specialties requested or wildcard used; not applying specialty filter."
        )
        return None

    logger.info(
        f"Specialty filter requested for {len(specialties)} specialties, but current implementation does not filter by specialty. Returning all specialties."
    )
    return None


# Helper function for time filtering
def _build_hospital_shift_time_filter(
    start_time_str: str, end_time_str: str
) -> Optional[ColumnElement[bool]]:
    """
    Builds time filter conditions for hospital shifts.
    Compares times as strings in "HH:MM:SS" format.
    Returns None if no time filters should be applied.
    """
    time_conditions: List[ColumnElement[bool]] = []

    if start_time_str != "*":
        try:
            datetime.datetime.strptime(start_time_str, "%H:%M:%S")
            time_conditions.append(
                HospitalShift.hospital_shift_start_time >= start_time_str
            )
            logger.info(
                f"Applying hospital shift start time filter: >= {start_time_str}"
            )
        except ValueError:
            logger.warning(
                f"Invalid hospital shift start time format: '{start_time_str}'. Filter skipped."
            )

    if end_time_str != "*":
        try:
            datetime.datetime.strptime(end_time_str, "%H:%M:%S")
            time_conditions.append(
                HospitalShift.hospital_shift_end_time <= end_time_str
            )
            logger.info(f"Applying hospital shift end time filter: <= {end_time_str}")
        except ValueError:
            logger.warning(
                f"Invalid hospital shift end time format: '{end_time_str}'. Filter skipped."
            )

    if not time_conditions:
        return None
    if len(time_conditions) == 1:
        return time_conditions[0]
    return and_(*time_conditions)


def build_hospital_shifts_statement(
    hospital_shift_dates: List[str] = ["*"],
    hospital_names: List[str] = ["*"],
    hospital_shifts_start_time: str = "*",
    hospital_shifts_end_time: str = "*",
    specialties: List[str] = ["*"],
    include_contact_info: bool = False,
) -> Select:
    """
     Constructs a SQLAlchemy Select statement to query HospitalShift information
     based on optional date, name (regex/fuzzy), shift time, and specialty criteria.

    Args:
        hospital_shift_dates: List of date strings ("YYYY-MM-DD"). "*" means no date filter.
        hospital_names: List of hospital name terms. "*" means no name filter. Uses regex and fuzzy matching.
        hospital_shifts_start_time: Start time of the shift ("HH:MM:SS"). "*" means any start time.
        hospital_shifts_end_time: End time of the shift ("HH:MM:SS"). "*" means any end time.
        specialties: List of medical specialties. "*" means no specialty filter.
        include_contact_info: Boolean indicating whether to include contact info.

    Returns:
        A SQLAlchemy Select statement object ready for execution.
    """
    logger.debug(
        f"Building hospital shift query with dates_count={len(hospital_shift_dates) if hospital_shift_dates != ['*'] else 'any'}, "
        f"names_count={len(hospital_names) if hospital_names != ['*'] else 'any'}, "
        f"start_time={hospital_shifts_start_time}, end_time={hospital_shifts_end_time}, "
        f"specialties_count={len(specialties) if specialties != ['*'] else 'any'}, "
        f"include_contact_info={include_contact_info}"
    )

    stmt = select(HospitalShift)
    filters: List[ColumnElement[bool]] = []

    # Build filters using helper functions
    date_filter = _build_hospital_shift_date_filter(hospital_shift_dates)
    if date_filter is not None:
        filters.append(date_filter)

    name_filter = _build_hospital_name_filter(hospital_names)
    if name_filter is not None:
        filters.append(name_filter)

    time_filter = _build_hospital_shift_time_filter(
        hospital_shifts_start_time, hospital_shifts_end_time
    )
    if time_filter is not None:
        filters.append(time_filter)

    specialties_filter = _build_specialties_filter(specialties)
    if (
        specialties_filter is not None
    ):
        filters.append(specialties_filter)

    if filters:
        logger.info(
            f"Applying {len(filters)} filter conditions to hospital shift query."
        )
        stmt = stmt.where(and_(*filters))
    else:
        logger.info("No filters applied to hospital shift query.")

    stmt = stmt.order_by(
        HospitalShift.hospital_shift_date.asc(), HospitalShift.hospital_name.asc()
    )

    return stmt
