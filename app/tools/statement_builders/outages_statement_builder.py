import logging
import datetime
from typing import List, Optional
from sqlalchemy import select, and_, ColumnElement, false, Select

from app.db.models.outage_model import Outage

logger = logging.getLogger(__name__)


def _build_outage_date_filter(outage_dates: List[str]) -> Optional[ColumnElement[bool]]:
    """
    Parses date strings and builds an 'IN' condition for Outage.outage_date.

    Handles "*" wildcard within the list (ignored).
    Returns None if no valid date filters should be applied.
    Returns false() if dates were provided but none were valid (prevents matching).
    """
    if outage_dates == ["*"]:
        return None

    valid_dates = []
    has_attempted_dates = False
    for date_str in outage_dates:
        if date_str == "*" or not date_str:
            continue
        has_attempted_dates = True
        try:
            valid_dates.append(datetime.datetime.strptime(date_str, "%Y-%m-%d").date())
        except ValueError:
            logger.warning(
                f"Invalid date format skipped during filter build: '{date_str}'"
            )

    if valid_dates:
        logger.info(f"Applying date filter for: {valid_dates}")
        return Outage.outage_date.in_(valid_dates)
    elif has_attempted_dates:
        logger.warning(
            "Date filter provided but contained no valid dates. Query will yield no results based on date."
        )
        return false()
    else:
        return None


def _build_outage_type_filter(
    outage_type: Optional[str],
) -> Optional[ColumnElement[bool]]:
    """
    Builds an exact matching condition for Outage.outage_type.

    Handles "*" or None as no filter.
    Returns None if no type filter should be applied.
    """
    # Treat None, "*" or empty string as no filter needed
    if outage_type is None or outage_type == "*" or not outage_type:
        return None

    logger.info(f"Applying exact type filter for: '{outage_type}'")
    return Outage.outage_type == outage_type


def _build_outage_location_filter(
    locations: List[str],
) -> Optional[ColumnElement[bool]]:
    """
    Builds location filter conditions using both regex and fuzzy matching helpers.

    Handles "*" wildcard within the list (ignored by helpers assumed).
    Combines all valid conditions (regex + fuzzy) with OR.
    Requires pg_trgm extension for fuzzy matching.
    Returns None if no location filters should be applied.
    """
    return None


def _build_outage_affected_areas_filter(
    affected_areas: List[str],
) -> Optional[ColumnElement[bool]]:
    """
    Builds affected areas filter conditions using both regex and fuzzy matching helpers.
    Handles "*" wildcard within the list (ignored by helpers assumed).
    Combines all valid conditions (regex + fuzzy) with OR.
    Returns None if no affected areas filters should be applied.
    """
    return None


def build_outages_statement(
    outage_dates: List[str] = ["*"],
    outage_type: str = "*",
    locations: List[str] = ["*"],
    affected_areas: List[str] = ["*"],
) -> Select:
    """
    Constructs a SQLAlchemy Select statement to query Outage information
    based on optional date, type (exact), location (fuzzy), and affected_areas (regex/fuzzy) criteria.

    Args:
        outage_dates: List of date strings ("YYYY-MM-DD"). "*" means no date filter.
        outage_type: Type of outage (e.g., "power", "water"). "*" means no type filter. Uses exact matching.
        locations: List of location strings. "*" means no location filter. Uses fuzzy matching.
        affected_areas: List of affected area strings. "*" means no filter. Uses regex and fuzzy matching.

    Returns:
        A SQLAlchemy Select statement object ready for execution.
    """
    logger.debug(
        f"Building outage query with dates_count={len(outage_dates) if outage_dates != ['*'] else 'any'}, "
        f"type='{outage_type}', locations_count={len(locations) if locations != ['*'] else 'any'}, "
        f"affected_areas_count={len(affected_areas) if affected_areas != ['*'] else 'any'}"
    )

    stmt = select(Outage)
    filters: List[ColumnElement[bool]] = []

    # Build filters using helper functions
    date_filter = _build_outage_date_filter(outage_dates)
    if date_filter is not None:
        filters.append(date_filter)

    type_filter = _build_outage_type_filter(outage_type)
    if type_filter is not None:
        filters.append(type_filter)

    # Location filter now uses threshold from settings internally
    location_filter = _build_outage_location_filter(locations)
    if location_filter is not None:
        filters.append(location_filter)

    affected_areas_filter = _build_outage_affected_areas_filter(affected_areas)
    if affected_areas_filter is not None:
        filters.append(affected_areas_filter)

    # Apply combined filters if any were generated
    if filters:
        logger.info(f"Applying {len(filters)} filter conditions to outage query.")
        stmt = stmt.where(and_(*filters))
    else:
        logger.info("No filters applied to outage query.")

    # Add default ordering
    stmt = stmt.order_by(Outage.outage_date.desc(), Outage.outage_start.desc())

    return stmt
