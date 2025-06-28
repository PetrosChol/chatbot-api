import logging
import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_, func, ColumnElement, false, Select

from app.db.models.cinema_models import Screening, Movie, Hall, Cinema
from app.utils.build_fuzzy_conditions import build_fuzzy_conditions
from app.utils.build_regex_conditions import build_regex_conditions
from app.core.config import settings

logger = logging.getLogger(__name__)

def _build_screening_date_filter(
    screening_dates: List[str],
) -> Optional[ColumnElement[bool]]:
    """Parses screening date strings and builds an 'IN' condition."""
    if screening_dates == ["*"]:
        return None
    valid_dates = []
    has_attempted_dates = False
    invalid_formats_found = []
    for date_str in screening_dates:
        if date_str == "*" or not date_str:
            continue
        has_attempted_dates = True
        try:
            valid_dates.append(datetime.datetime.strptime(date_str, "%Y-%m-%d").date())
        except ValueError:
            invalid_formats_found.append(date_str)
            logger.warning(f"Invalid screening date format skipped: '{date_str}'")
    if invalid_formats_found:
        logger.warning(f"Invalid screening date formats found: {invalid_formats_found}")
    if valid_dates:
        logger.info(f"Applying screening date filter for: {valid_dates}")
        return Screening.screening_date.in_(valid_dates)
    elif has_attempted_dates:
        logger.warning("Screening date filter provided but no valid dates found.")
        return false()
    else:
        return None


def _build_movie_filter(movies: List[str]) -> Optional[ColumnElement[bool]]:
    """Builds fuzzy matching OR conditions for Movie.movie_name, Movie.normalized_movie_name_greek, and Movie.normalized_movie_name_english."""
    if movies == ["*"]:
        return None

    all_movie_conditions = []

    # Conditions for the primary normalized name
    conditions_primary = build_fuzzy_conditions(
        Movie.normalized_movie_name, movies, threshold=settings.FUZZY_THRESHOLD
    )
    if conditions_primary:
        all_movie_conditions.extend(conditions_primary)

    # Conditions for the Greek normalized name
    conditions_greek = build_fuzzy_conditions(
        Movie.normalized_movie_name_greek, movies, threshold=settings.FUZZY_THRESHOLD
    )
    if conditions_greek:
        all_movie_conditions.extend(conditions_greek)

    # Conditions for the English normalized name
    conditions_english = build_fuzzy_conditions(
        Movie.normalized_movie_name_english, movies, threshold=settings.FUZZY_THRESHOLD
    )
    if conditions_english:
        all_movie_conditions.extend(conditions_english)

    if all_movie_conditions:
        logger.info(
            "Applying fuzzy movie name filter conditions using primary, Greek, and English normalized columns."
        )
        return or_(*all_movie_conditions)
    else:
        return None


def _build_genre_filter(genres: List[str]) -> Optional[ColumnElement[bool]]:
    """Builds regex and fuzzy matching OR conditions for Movie.normalized_genre."""
    if genres == ["*"] or not genres:
        return None

    # build_regex_conditions and build_fuzzy_conditions handle internal normalization
    # and filtering of "*" or empty strings from the 'genres' list.
    regex_conditions = build_regex_conditions(Movie.normalized_genre, genres)
    fuzzy_conditions = build_fuzzy_conditions(
        Movie.normalized_genre, genres, threshold=settings.FUZZY_THRESHOLD
    )

    all_genre_conditions = regex_conditions + fuzzy_conditions

    if all_genre_conditions:
        logger.info(
            f"Applying {len(all_genre_conditions)} genre filter conditions (regex/fuzzy) to Movie.normalized_genre."
        )
        return or_(*all_genre_conditions)
    else:
        logger.info("No valid genre conditions generated from regex or fuzzy matching.")
        return None


def _build_year_filter(year: Optional[int]) -> Optional[ColumnElement[bool]]:
    """Builds an exact matching condition for Movie.year."""
    if year is None:
        return None
    logger.info(f"Applying movie year filter for: {year}")
    return Movie.year == year


def _build_cinema_filter(cinemas: List[str]) -> Optional[ColumnElement[bool]]:
    """Builds fuzzy OR conditions for Cinema.cinema_name."""
    if cinemas == ["*"]:
        return None

    cinema_conditions = []
    for cinema_name in cinemas:
        if cinema_name == "*" or not cinema_name:
            continue

        # Build the similarity condition using the original cinema name
        sim_condition = (
            func.similarity(Cinema.cinema_name, cinema_name) > settings.FUZZY_THRESHOLD
        )
        # Simple substring match using the original cinema name
        ilike_condition = Cinema.cinema_name.ilike(f"%{cinema_name}%")
        # Combine conditions for this specific cinema name
        condition = or_(sim_condition, ilike_condition)
        cinema_conditions.append(condition)

    if cinema_conditions:
        logger.info(
            "Applying cinema name filter conditions (fuzzy/ilike) using original names."
        )
        return or_(*cinema_conditions)
    else:
        return None


def build_cinemas_statement(
    screening_dates: List[str] = ["*"],
    movies: List[str] = ["*"],
    cinemas: List[str] = ["*"],
    halls_and_screening_times: bool = False,
    genres: List[str] = ["*"],
    year: Optional[int] = None,
) -> Select:
    """
    Constructs a SQLAlchemy Select statement to query Screening information.

    Dynamically adjusts selected columns and applies distinct based on
    whether specific screening times are requested.

    Args:
        screening_dates: List of date strings ("YYYY-MM-DD"). "*" means no filter.
        movies: List of movie names. "*" means no filter. Uses fuzzy matching.
        cinemas: List of cinema names. "*" means no filter. Uses fuzzy/ILIKE matching.
        halls_and_screening_times: If True, include specific times and hall names.
                                   If False, show distinct Movie/Cinema/Date combinations.

    Returns:
        A SQLAlchemy Select statement object ready for execution.
    """

    # --- Define Select Columns Conditionally ---
    if halls_and_screening_times:
        select_columns = [
            Screening.screening_date,
            Screening.screening_time,
            Movie.movie_name,
            Cinema.cinema_name,
            Hall.hall_name,
            Movie.genre,
            Movie.year,
        ]
    else:
        select_columns = [
            Screening.screening_date,
            Movie.movie_name,
            Cinema.cinema_name,
            Movie.genre,
            Movie.year,
        ]

    # --- Base Statement with Joins ---
    stmt = select(*select_columns)
    stmt = stmt.select_from(Screening).join(Movie).join(Hall).join(Cinema)

    # --- Build Filters ---
    filters: List[ColumnElement[bool]] = []

    date_filter = _build_screening_date_filter(screening_dates)
    if date_filter is not None:
        filters.append(date_filter)

    movie_filter = _build_movie_filter(movies)
    if movie_filter is not None:
        filters.append(movie_filter)

    cinema_filter = _build_cinema_filter(cinemas)
    if cinema_filter is not None:
        filters.append(cinema_filter)

    genre_filter = _build_genre_filter(genres)
    if genre_filter is not None:
        filters.append(genre_filter)

    year_filter = _build_year_filter(year)
    if year_filter is not None:
        filters.append(year_filter)

    # --- Apply Filters ---
    if filters:
        logger.info(f"Applying {len(filters)} filter conditions to cinema query.")
        stmt = stmt.where(and_(*filters))
    else:
        logger.info("No filters applied to cinema query.")

    # --- Apply Distinct if NOT including times ---
    if not halls_and_screening_times:
        logger.info("Applying DISTINCT to cinema query results.")
        stmt = stmt.distinct()

    # --- Apply Ordering ---
    order_columns = [
        Screening.screening_date.asc(),
        Cinema.cinema_name.asc(),
        Movie.movie_name.asc(),
    ]
    if halls_and_screening_times:
        order_columns.append(Screening.screening_time.asc())

    stmt = stmt.order_by(*order_columns)

    return stmt
