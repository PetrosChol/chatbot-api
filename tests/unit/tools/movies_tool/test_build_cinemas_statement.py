import pytest
from unittest.mock import MagicMock
from sqlalchemy import Select  # For type hinting and mocking

# Import the function/models to test/mock
from app.tools.statement_builders.movies_statement_builder import (
    build_cinemas_statement,
)
from app.db.models.cinema_models import Screening, Movie, Hall, Cinema

# --- Mock Filters ---
MOCK_DATE_FILTER = MagicMock(name="DateFilterCondition")
MOCK_MOVIE_FILTER = MagicMock(name="MovieFilterCondition")
MOCK_CINEMA_FILTER = MagicMock(name="CinemaFilterCondition")

# --- Mock Columns (for ordering/selection verification) ---
# Use simple MagicMocks and assign necessary attributes to avoid SQLAlchemy conflicts
MockScreeningDateCol = MagicMock(key="screening_date")
MockScreeningDateCol.name = "screening_date"
MockScreeningTimeCol = MagicMock(key="screening_time")
MockScreeningTimeCol.name = "screening_time"
MockMovieNameCol = MagicMock(key="movie_name")
MockMovieNameCol.name = "movie_name"
MockCinemaNameCol = MagicMock(key="cinema_name")
MockCinemaNameCol.name = "cinema_name"
MockHallNameCol = MagicMock(key="hall_name")
MockHallNameCol.name = "hall_name"

# Mock the asc()/desc() methods
MockScreeningDateAsc = MagicMock(name="screening_date.asc()")
MockScreeningTimeAsc = MagicMock(name="screening_time.asc()")
MockMovieNameAsc = MagicMock(name="movie_name.asc()")
MockCinemaNameAsc = MagicMock(name="cinema_name.asc()")
MockScreeningDateCol.asc.return_value = MockScreeningDateAsc
MockScreeningTimeCol.asc.return_value = MockScreeningTimeAsc
MockMovieNameCol.asc.return_value = MockMovieNameAsc
MockCinemaNameCol.asc.return_value = MockCinemaNameAsc
# .key attributes are now set during initialization above

# --- Test Fixture for Mocking ---


@pytest.fixture
def mock_dependencies(mocker):
    """Fixture to mock all dependencies of build_cinemas_statement."""
    # Mock the helper filter functions
    mock_build_date = mocker.patch(
        "app.tools.statement_builders.movies_statement_builder._build_screening_date_filter",
        return_value=None,
    )
    mock_build_movie = mocker.patch(
        "app.tools.statement_builders.movies_statement_builder._build_movie_filter",
        return_value=None,
    )
    mock_build_cinema = mocker.patch(
        "app.tools.statement_builders.movies_statement_builder._build_cinema_filter",
        return_value=None,
    )

    # Mock SQLAlchemy functions and chained methods
    mock_select_obj = MagicMock(spec=Select, name="SelectObject")
    mock_select_from_obj = MagicMock(spec=Select, name="SelectFromObject")
    mock_join1_obj = MagicMock(spec=Select, name="Join1Object")  # After join(Movie)
    mock_join2_obj = MagicMock(spec=Select, name="Join2Object")  # After join(Hall)
    mock_join3_obj = MagicMock(spec=Select, name="Join3Object")  # After join(Cinema)
    mock_where_obj = MagicMock(spec=Select, name="WhereObject")
    mock_distinct_obj = MagicMock(spec=Select, name="DistinctObject")
    mock_order_by_obj = MagicMock(spec=Select, name="OrderByObject")  # Final object

    # Configure the chain: select().select_from().join().join().join().where().distinct().order_by()
    mock_select_func = mocker.patch(
        "app.tools.statement_builders.movies_statement_builder.select",
        return_value=mock_select_obj,
    )
    mock_select_obj.select_from.return_value = mock_select_from_obj
    # Explicitly chain the joins
    mock_select_from_obj.join.return_value = (
        mock_join1_obj  # First join returns mock_join1_obj
    )
    mock_join1_obj.join.return_value = (
        mock_join2_obj  # Second join returns mock_join2_obj
    )
    mock_join2_obj.join.return_value = (
        mock_join3_obj  # Third join returns mock_join3_obj
    )

    # Where might be called on join3_obj or distinct_obj
    mock_join3_obj.where.return_value = mock_where_obj
    mock_where_obj.distinct.return_value = (
        mock_distinct_obj  # If distinct is called after where
    )
    mock_join3_obj.distinct.return_value = (
        mock_distinct_obj  # If distinct is called before where (no filters)
    )

    # Order by might be called on where_obj or distinct_obj
    mock_where_obj.order_by.return_value = mock_order_by_obj
    mock_distinct_obj.order_by.return_value = mock_order_by_obj
    # Also handle the case where order_by is called directly after joins (no filters/distinct)
    mock_join3_obj.order_by.return_value = mock_order_by_obj

    # Mock and_ function
    mock_and_func = mocker.patch(
        "app.tools.statement_builders.movies_statement_builder.and_"
    )

    # --- Patch the column attributes directly on the original models using patch.object ---
    # Use the simplified MagicMocks defined above
    mocker.patch.object(Screening, "screening_date", MockScreeningDateCol)
    mocker.patch.object(Screening, "screening_time", MockScreeningTimeCol)
    mocker.patch.object(Movie, "movie_name", MockMovieNameCol)
    mocker.patch.object(Cinema, "cinema_name", MockCinemaNameCol)
    mocker.patch.object(Hall, "hall_name", MockHallNameCol)
    # --- End of change ---

    # Mock logger
    mock_logger = mocker.patch(
        "app.tools.statement_builders.movies_statement_builder.logger"
    )

    return {
        "mock_build_date": mock_build_date,
        "mock_build_movie": mock_build_movie,
        "mock_build_cinema": mock_build_cinema,
        "mock_select_func": mock_select_func,
        "mock_select_obj": mock_select_obj,
        "mock_select_from_obj": mock_select_from_obj,
        "mock_join1_obj": mock_join1_obj,
        "mock_join2_obj": mock_join2_obj,
        "mock_join3_obj": mock_join3_obj,
        "mock_where_obj": mock_where_obj,
        "mock_distinct_obj": mock_distinct_obj,
        "mock_order_by_obj": mock_order_by_obj,
        "mock_and_func": mock_and_func,
        "mock_logger": mock_logger,
        # Pass mock columns/order results for assertion checks
        "MockScreeningDateAsc": MockScreeningDateAsc,
        "MockScreeningTimeAsc": MockScreeningTimeAsc,
        "MockMovieNameAsc": MockMovieNameAsc,
        "MockCinemaNameAsc": MockCinemaNameAsc,
    }


# --- Test Cases ---


def test_build_cinemas_statement_defaults_no_times(mock_dependencies):
    """Test with default args (no filters, halls_and_screening_times=False)."""
    result = build_cinemas_statement()  # halls_and_screening_times defaults to False

    # Check helpers called with defaults
    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_movie"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_cinema"].assert_called_once_with(["*"])

    # Check select called with correct columns (no time/hall, but with genre/year)
    mock_dependencies["mock_select_func"].assert_called_once_with(
        MockScreeningDateCol,
        MockMovieNameCol,
        MockCinemaNameCol,
        Movie.genre,
        Movie.year,
    )

    # Check joins (using the original models as they appear in the source code)
    mock_dependencies["mock_select_obj"].select_from.assert_called_once_with(Screening)
    # Assert each join individually on the correct mock object
    mock_dependencies["mock_select_from_obj"].join.assert_called_once_with(Movie)
    mock_dependencies["mock_join1_obj"].join.assert_called_once_with(Hall)
    mock_dependencies["mock_join2_obj"].join.assert_called_once_with(Cinema)

    # Check where NOT called (since no filters returned)
    mock_dependencies["mock_join3_obj"].where.assert_not_called()
    mock_dependencies["mock_and_func"].assert_not_called()
    mock_dependencies["mock_logger"].info.assert_any_call(
        "No filters applied to cinema query."
    )

    # Check distinct IS called (on the object after joins, before where)
    mock_dependencies["mock_join3_obj"].distinct.assert_called_once_with()
    mock_dependencies["mock_logger"].info.assert_any_call(
        "Applying DISTINCT to cinema query results."
    )

    # Check order_by IS called on the distinct object
    mock_dependencies["mock_distinct_obj"].order_by.assert_called_once_with(
        MockScreeningDateAsc, MockCinemaNameAsc, MockMovieNameAsc
    )

    # Final result is the object returned by order_by
    assert result == mock_dependencies["mock_order_by_obj"]
    # logger.debug is not called for this path in the current implementation
    mock_dependencies["mock_logger"].debug.assert_not_called()


def test_build_cinemas_statement_defaults_with_times(mock_dependencies):
    """Test with default args (no filters, halls_and_screening_times=True)."""
    result = build_cinemas_statement(halls_and_screening_times=True)

    # Check helpers called with defaults
    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_movie"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_cinema"].assert_called_once_with(["*"])

    # Check select called with correct columns (including time/hall, genre, year)
    mock_dependencies["mock_select_func"].assert_called_once_with(
        MockScreeningDateCol,
        MockScreeningTimeCol,
        MockMovieNameCol,
        MockCinemaNameCol,
        MockHallNameCol,
        Movie.genre,
        Movie.year,
    )

    # Check joins (using the original models as they appear in the source code)
    mock_dependencies["mock_select_obj"].select_from.assert_called_once_with(Screening)
    # Assert each join individually on the correct mock object
    mock_dependencies["mock_select_from_obj"].join.assert_called_once_with(Movie)
    mock_dependencies["mock_join1_obj"].join.assert_called_once_with(Hall)
    mock_dependencies["mock_join2_obj"].join.assert_called_once_with(Cinema)

    # Check where NOT called
    mock_dependencies["mock_join3_obj"].where.assert_not_called()
    mock_dependencies["mock_and_func"].assert_not_called()
    mock_dependencies["mock_logger"].info.assert_any_call(
        "No filters applied to cinema query."
    )

    # Check distinct IS NOT called
    mock_dependencies["mock_join3_obj"].distinct.assert_not_called()
    mock_dependencies[
        "mock_where_obj"
    ].distinct.assert_not_called()  # Check both possibilities

    # Check order_by IS called on the join3 object (since where/distinct weren't)
    # Includes screening time in ordering
    mock_dependencies["mock_join3_obj"].order_by.assert_called_once_with(
        MockScreeningDateAsc, MockCinemaNameAsc, MockMovieNameAsc, MockScreeningTimeAsc
    )

    # Final result is the object returned by order_by
    # In this case, order_by was called on join3_obj, whose order_by returns mock_order_by_obj
    # Need to adjust mock setup slightly for this path
    mock_dependencies["mock_join3_obj"].order_by.return_value = mock_dependencies[
        "mock_order_by_obj"
    ]
    # Reset logger mock before re-running the function
    mock_dependencies["mock_logger"].reset_mock()
    # Re-run the function call with the corrected mock setup
    result = build_cinemas_statement(halls_and_screening_times=True)
    assert result == mock_dependencies["mock_order_by_obj"]
    # Now assert that debug was called once *after the reset*
    # The logger call is now inside the build_cinemas_statement, so we don't need to check it here
    # as it's part of the function's internal logging which is not the primary focus of this test.
    # Instead, we ensure the main logic (select, joins, order_by) is correct.
    # logger.debug is not called for this path in the current implementation
    mock_dependencies["mock_logger"].debug.assert_not_called()


def test_build_cinemas_statement_with_all_filters_no_times(mock_dependencies):
    """Test with all filters applied, halls_and_screening_times=False."""
    mock_dependencies["mock_build_date"].return_value = MOCK_DATE_FILTER
    mock_dependencies["mock_build_movie"].return_value = MOCK_MOVIE_FILTER
    mock_dependencies["mock_build_cinema"].return_value = MOCK_CINEMA_FILTER
    dates = ["2024-05-10"]
    movies = ["Movie 1"]
    cinemas = ["Cinema A"]

    result = build_cinemas_statement(
        screening_dates=dates,
        movies=movies,
        cinemas=cinemas,
        halls_and_screening_times=False,
    )

    # Check helpers called
    mock_dependencies["mock_build_date"].assert_called_once_with(dates)
    mock_dependencies["mock_build_movie"].assert_called_once_with(movies)
    mock_dependencies["mock_build_cinema"].assert_called_once_with(cinemas)

    # Check select (no time/hall, but with genre/year)
    mock_dependencies["mock_select_func"].assert_called_once_with(
        MockScreeningDateCol,
        MockMovieNameCol,
        MockCinemaNameCol,
        Movie.genre,
        Movie.year,
    )
    # Check joins (using the original models as they appear in the source code)
    mock_dependencies["mock_select_obj"].select_from.assert_called_once_with(Screening)
    # Assert each join individually on the correct mock object
    mock_dependencies["mock_select_from_obj"].join.assert_called_once_with(Movie)
    mock_dependencies["mock_join1_obj"].join.assert_called_once_with(Hall)
    mock_dependencies["mock_join2_obj"].join.assert_called_once_with(Cinema)

    # Check where IS called on join3_obj
    mock_dependencies["mock_and_func"].assert_called_once_with(
        MOCK_DATE_FILTER, MOCK_MOVIE_FILTER, MOCK_CINEMA_FILTER
    )
    mock_dependencies["mock_join3_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_logger"].info.assert_any_call(
        "Applying 3 filter conditions to cinema query."
    )

    # Check distinct IS called on the where_obj
    mock_dependencies["mock_where_obj"].distinct.assert_called_once_with()
    mock_dependencies["mock_logger"].info.assert_any_call(
        "Applying DISTINCT to cinema query results."
    )

    # Check order_by IS called on the distinct_obj
    mock_dependencies["mock_distinct_obj"].order_by.assert_called_once_with(
        MockScreeningDateAsc, MockCinemaNameAsc, MockMovieNameAsc
    )

    assert result == mock_dependencies["mock_order_by_obj"]
    # logger.debug is not called for this path in the current implementation
    mock_dependencies["mock_logger"].debug.assert_not_called()


def test_build_cinemas_statement_with_some_filters_with_times(mock_dependencies):
    """Test with some filters applied, halls_and_screening_times=True."""
    mock_dependencies["mock_build_date"].return_value = None  # No date filter
    mock_dependencies["mock_build_movie"].return_value = MOCK_MOVIE_FILTER
    mock_dependencies["mock_build_cinema"].return_value = None  # No cinema filter
    movies = ["Movie 2"]

    result = build_cinemas_statement(movies=movies, halls_and_screening_times=True)

    # Check helpers called
    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_movie"].assert_called_once_with(movies)
    mock_dependencies["mock_build_cinema"].assert_called_once_with(["*"])

    # Check select (with time/hall, genre, year)
    mock_dependencies["mock_select_func"].assert_called_once_with(
        MockScreeningDateCol,
        MockScreeningTimeCol,
        MockMovieNameCol,
        MockCinemaNameCol,
        MockHallNameCol,
        Movie.genre,
        Movie.year,
    )
    # Check joins (using the original models as they appear in the source code)
    mock_dependencies["mock_select_obj"].select_from.assert_called_once_with(Screening)
    # Assert each join individually on the correct mock object
    mock_dependencies["mock_select_from_obj"].join.assert_called_once_with(Movie)
    mock_dependencies["mock_join1_obj"].join.assert_called_once_with(Hall)
    mock_dependencies["mock_join2_obj"].join.assert_called_once_with(Cinema)

    # Check where IS called on join3_obj with only the movie filter
    mock_dependencies["mock_and_func"].assert_called_once_with(
        MOCK_MOVIE_FILTER
    )  # Only non-None filter
    mock_dependencies["mock_join3_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_logger"].info.assert_any_call(
        "Applying 1 filter conditions to cinema query."
    )

    # Check distinct IS NOT called
    mock_dependencies["mock_join3_obj"].distinct.assert_not_called()
    mock_dependencies["mock_where_obj"].distinct.assert_not_called()

    # Check order_by IS called on the where_obj
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        MockScreeningDateAsc, MockCinemaNameAsc, MockMovieNameAsc, MockScreeningTimeAsc
    )

    assert result == mock_dependencies["mock_order_by_obj"]
    # logger.debug is not called for this path in the current implementation
    mock_dependencies["mock_logger"].debug.assert_not_called()
