import pytest
from unittest.mock import MagicMock
from sqlalchemy import Select  # For type hinting

# Import the function to test
from app.tools.statement_builders.performances_statement_builder import (
    build_performances_statement,
)

# Import the model for context
from app.db.models.performance_model import Performance

# --- Mock Filters ---
MOCK_DATE_FILTER = MagicMock(name="DateFilterCondition")
MOCK_NAME_FILTER = MagicMock(name="NameFilterCondition")
MOCK_LOCATION_FILTER = MagicMock(name="LocationFilterCondition")
MOCK_TYPE_FILTER = MagicMock(name="TypeFilterCondition")

# --- Test Fixture for Mocking ---


@pytest.fixture
def mock_dependencies(mocker):
    """Fixture to mock all dependencies of build_performances_statement."""
    # Mock the helper functions
    mock_build_date = mocker.patch(
        "app.tools.statement_builders.performances_statement_builder._build_performance_date_filter",
        return_value=None,
    )
    mock_build_name = mocker.patch(
        "app.tools.statement_builders.performances_statement_builder._build_performance_name_filter",
        return_value=None,
    )
    mock_build_location = mocker.patch(
        "app.tools.statement_builders.performances_statement_builder._build_performance_location_filter",
        return_value=None,
    )
    mock_build_type = mocker.patch(
        "app.tools.statement_builders.performances_statement_builder._build_performance_type_filter",
        return_value=None,
    )

    # Mock SQLAlchemy functions and chained methods
    mock_select_obj = MagicMock(spec=Select)
    mock_where_obj = MagicMock(spec=Select)
    mock_order_by_obj = MagicMock(spec=Select)

    mock_select_func = mocker.patch(
        "app.tools.statement_builders.performances_statement_builder.select",
        return_value=mock_select_obj,
    )
    mock_select_obj.where.return_value = mock_where_obj
    mock_where_obj.order_by.return_value = (
        mock_order_by_obj  # Final object in this chain
    )

    # Mock and_ function
    mock_and_func = mocker.patch(
        "app.tools.statement_builders.performances_statement_builder.and_"
    )

    # Create final mock objects for .asc() calls
    mock_date_asc_result = MagicMock(
        name="Result of Performance.performance_date.asc()"
    )
    mock_name_asc_result = MagicMock(
        name="Result of Performance.performance_name.asc()"
    )

    # Create mock column objects
    mock_perf_date_col = MagicMock(name="MockPerformance.performance_date")
    mock_perf_name_col = MagicMock(name="MockPerformance.performance_name")

    # Configure .asc() method on mock columns
    mock_perf_date_col.asc.return_value = mock_date_asc_result
    mock_perf_name_col.asc.return_value = mock_name_asc_result

    # Patch actual column attributes on the Performance class
    mocker.patch.object(Performance, "performance_date", new=mock_perf_date_col)
    mocker.patch.object(Performance, "performance_name", new=mock_perf_name_col)

    return {
        "mock_build_date": mock_build_date,
        "mock_build_name": mock_build_name,
        "mock_build_location": mock_build_location,
        "mock_build_type": mock_build_type,
        "mock_select_func": mock_select_func,
        "mock_select_obj": mock_select_obj,
        "mock_where_obj": mock_where_obj,
        "mock_order_by_obj": mock_order_by_obj,
        "mock_and_func": mock_and_func,
        "mock_date_asc": mock_date_asc_result,
        "mock_name_asc": mock_name_asc_result,
    }


# --- Test Cases ---


def test_build_performances_statement_defaults(mock_dependencies):
    """Test with default arguments: no filters applied, default order."""
    result = build_performances_statement()

    # Check helpers called with defaults
    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with("*")

    # Check select called
    mock_dependencies["mock_select_func"].assert_called_once_with(Performance)

    # Check where NOT called
    mock_dependencies["mock_select_obj"].where.assert_not_called()
    mock_dependencies["mock_and_func"].assert_not_called()

    # Check order_by IS called on the initial select object
    mock_dependencies["mock_select_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )

    # The final result should be the object returned by order_by on the select object
    assert result == mock_dependencies["mock_select_obj"].order_by.return_value


def test_build_performances_statement_with_date_filter(mock_dependencies):
    """Test with only a date filter applied."""
    mock_dependencies["mock_build_date"].return_value = MOCK_DATE_FILTER
    dates = ["2024-03-10"]

    result = build_performances_statement(performance_dates=dates)

    mock_dependencies["mock_build_date"].assert_called_once_with(dates)
    mock_dependencies["mock_build_name"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with("*")

    mock_dependencies["mock_select_func"].assert_called_once_with(Performance)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_DATE_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_performances_statement_with_name_filter(mock_dependencies):
    """Test with only a name filter applied."""
    mock_dependencies["mock_build_name"].return_value = MOCK_NAME_FILTER
    names = ["Concert A"]

    result = build_performances_statement(performance_names=names)

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(names)
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with("*")

    mock_dependencies["mock_select_func"].assert_called_once_with(Performance)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_NAME_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_performances_statement_with_location_filter(mock_dependencies):
    """Test with only a location filter applied."""
    mock_dependencies["mock_build_location"].return_value = MOCK_LOCATION_FILTER
    locations = ["Venue B"]

    result = build_performances_statement(performance_locations=locations)

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_location"].assert_called_once_with(locations)
    mock_dependencies["mock_build_type"].assert_called_once_with("*")

    mock_dependencies["mock_select_func"].assert_called_once_with(Performance)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_LOCATION_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_performances_statement_with_type_filter(mock_dependencies):
    """Test with only a type filter applied."""
    mock_dependencies["mock_build_type"].return_value = MOCK_TYPE_FILTER
    perf_type = "Music"

    result = build_performances_statement(performance_type=perf_type)

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with(perf_type)

    mock_dependencies["mock_select_func"].assert_called_once_with(Performance)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_TYPE_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_performances_statement_with_all_filters(mock_dependencies):
    """Test with date, name, location, and type filters applied."""
    mock_dependencies["mock_build_date"].return_value = MOCK_DATE_FILTER
    mock_dependencies["mock_build_name"].return_value = MOCK_NAME_FILTER
    mock_dependencies["mock_build_location"].return_value = MOCK_LOCATION_FILTER
    mock_dependencies["mock_build_type"].return_value = MOCK_TYPE_FILTER
    dates = ["2024-03-10"]
    names = ["Play X"]
    locations = ["Theatre Y"]
    perf_type = "Theatre"

    result = build_performances_statement(
        performance_dates=dates,
        performance_names=names,
        performance_locations=locations,
        performance_type=perf_type,
    )

    mock_dependencies["mock_build_date"].assert_called_once_with(dates)
    mock_dependencies["mock_build_name"].assert_called_once_with(names)
    mock_dependencies["mock_build_location"].assert_called_once_with(locations)
    mock_dependencies["mock_build_type"].assert_called_once_with(perf_type)

    mock_dependencies["mock_select_func"].assert_called_once_with(Performance)
    # Check and_ called with all filters
    mock_dependencies["mock_and_func"].assert_called_once_with(
        MOCK_DATE_FILTER, MOCK_NAME_FILTER, MOCK_LOCATION_FILTER, MOCK_TYPE_FILTER
    )
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_performances_statement_some_filters_none(mock_dependencies):
    """Test when some helper functions return None (no filter)."""
    mock_dependencies["mock_build_date"].return_value = None  # e.g., dates = ["*"]
    mock_dependencies["mock_build_name"].return_value = MOCK_NAME_FILTER
    mock_dependencies["mock_build_location"].return_value = (
        None  # e.g., locations = ["*"]
    )
    mock_dependencies["mock_build_type"].return_value = MOCK_TYPE_FILTER
    names = ["Opera Z"]
    perf_type = "Opera"

    result = build_performances_statement(
        performance_names=names, performance_type=perf_type
    )

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(names)
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with(perf_type)

    mock_dependencies["mock_select_func"].assert_called_once_with(Performance)
    # and_ should only be called with the non-None filters
    mock_dependencies["mock_and_func"].assert_called_once_with(
        MOCK_NAME_FILTER, MOCK_TYPE_FILTER
    )
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]
