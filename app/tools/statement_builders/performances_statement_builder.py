import logging
import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_, ColumnElement, false, Select

from app.db.models.performance_model import Performance
from app.utils.build_fuzzy_conditions import build_fuzzy_conditions
from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_performance_date_filter(
    performance_dates: List[str],
) -> Optional[ColumnElement[bool]]:
    """
    Parses performance date strings and builds an 'IN' condition.
    Handles "*" wildcard within the list (ignored).
    Returns None if no valid date filters should be applied.
    Returns false() if dates were provided but none were valid (prevents matching).
    """
    if performance_dates == ["*"]:
        return None

    valid_date_objects = []
    has_attempted_dates = False
    invalid_formats_found = []

    for date_str in performance_dates:
        if date_str == "*" or not date_str:
            continue
        has_attempted_dates = True
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            valid_date_objects.append(date_obj)
        except ValueError:
            invalid_formats_found.append(date_str)
            logger.warning(f"Invalid performance date format skipped: '{date_str}'")

    if invalid_formats_found:
        logger.warning(
            f"Invalid date formats found in input: {invalid_formats_found}. These dates were skipped."
        )

    if valid_date_objects:
        logger.info(f"Applying performance date filter for: {valid_date_objects}")
        return Performance.performance_date.in_(valid_date_objects)
    elif has_attempted_dates:
        logger.warning(
            "Performance date filter provided but contained no valid dates. Query will yield no results based on date."
        )
        return false()
    else:
        return None


def _build_performance_name_filter(
    performance_names: List[str],
) -> Optional[ColumnElement[bool]]:
    """
    Builds fuzzy matching OR conditions for Performance.performance_name.
    Handles "*" wildcard within the list (ignored by helper).
    Returns None if no name filters should be applied.
    """
    if performance_names == ["*"]:
        return None

    name_conditions = build_fuzzy_conditions(
        Performance.normalized_performance_name,
        performance_names,
        threshold=settings.FUZZY_THRESHOLD,
    )

    if name_conditions:
        logger.info("Applying fuzzy name filter conditions using normalized column.")
        return or_(*name_conditions)
    else:
        return None


def _build_performance_location_filter(
    performance_locations: List[str],
) -> Optional[ColumnElement[bool]]:
    """
    Builds fuzzy matching OR conditions for Performance.performance_location.
    Handles "*" wildcard within the list (ignored by helper).
    Returns None if no location filters should be applied.
    """
    if performance_locations == ["*"]:
        return None

    location_conditions = build_fuzzy_conditions(
        Performance.normalized_performance_location,
        performance_locations,
        threshold=settings.FUZZY_THRESHOLD,
    )

    if location_conditions:
        logger.info(
            "Applying fuzzy location filter conditions using normalized column."
        )
        return or_(*location_conditions)
    else:
        return None


def _build_performance_type_filter(
    performance_type: Optional[str],
) -> Optional[ColumnElement[bool]]:
    """
    Builds an exact matching condition for Performance.performance_type.
    Handles "*" or None as no filter.
    Returns None if no type filter should be applied.
    """
    # Treat None, "*" or empty string as no filter needed
    if performance_type is None or performance_type == "*" or not performance_type:
        return None

    logger.info(f"Applying exact type filter for: '{performance_type}'")
    return Performance.performance_type == performance_type


def build_performances_statement(
    performance_dates: List[str] = ["*"],
    performance_names: List[str] = ["*"],
    performance_locations: List[str] = ["*"],
    performance_type: str = "*",
) -> Select:
    """
    Constructs a SQLAlchemy Select statement to query Performance information
    based on optional date, name (fuzzy), location (fuzzy), and type (fuzzy) criteria.

    Args:
        performance_dates: List of date strings ("YYYY-MM-DD"). "*" means no date filter.
        performance_names: List of performance names. "*" means no name filter. Uses fuzzy matching.
        performance_locations: List of location strings. "*" means no location filter. Uses fuzzy matching.
        performance_type: Type of performance (e.g., "music", "theatre"). "*" means no type filter. Uses fuzzy matching.

    Returns:
        A SQLAlchemy Select statement object ready for execution.
    """
    logger.debug(
        f"Building performance query with dates_count={len(performance_dates) if performance_dates != ['*'] else 'any'}, "
        f"names_count={len(performance_names) if performance_names != ['*'] else 'any'}, "
        f"locations_count={len(performance_locations) if performance_locations != ['*'] else 'any'}, "
        f"type='{performance_type}'"
    )

    stmt = select(Performance)
    filters: List[ColumnElement[bool]] = []

    # Build filters using helper functions
    date_filter = _build_performance_date_filter(performance_dates)
    if date_filter is not None:
        filters.append(date_filter)

    name_filter = _build_performance_name_filter(performance_names)
    if name_filter is not None:
        filters.append(name_filter)

    location_filter = _build_performance_location_filter(performance_locations)
    if location_filter is not None:
        filters.append(location_filter)

    type_filter = _build_performance_type_filter(performance_type)
    if type_filter is not None:
        filters.append(type_filter)

    # Apply combined filters if any were generated
    if filters:
        logger.info(f"Applying {len(filters)} filter conditions to performance query.")
        stmt = stmt.where(and_(*filters))
    else:
        logger.info("No filters applied to performance query.")

    # Add default ordering
    stmt = stmt.order_by(
        Performance.performance_date.asc(), Performance.performance_name.asc()
    ) 
    return stmt
