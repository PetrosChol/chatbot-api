import pytest
from unittest.mock import MagicMock
from sqlalchemy import Select  # For type hinting

# Import the function to test
from app.tools.statement_builders.outages_statement_builder import (
    build_outages_statement,
)

# Import the model for context, although its methods/attributes will be mocked
from app.db.models.outage_model import Outage

# --- Mock Filters ---
# Create reusable mock filter objects to be returned by helper mocks
MOCK_DATE_FILTER = MagicMock(name="DateFilterCondition")
MOCK_TYPE_FILTER = MagicMock(name="TypeFilterCondition")
MOCK_LOCATION_FILTER = MagicMock(name="LocationFilterCondition")

# --- Test Fixture for Mocking ---


@pytest.fixture
def mock_dependencies(mocker):
    """Fixture to mock all dependencies of build_outages_statement."""
    # Mock the helper functions
    mock_build_date = mocker.patch(
        "app.tools.statement_builders.outages_statement_builder._build_outage_date_filter",
        return_value=None,
    )
    mock_build_type = mocker.patch(
        "app.tools.statement_builders.outages_statement_builder._build_outage_type_filter",
        return_value=None,
    )
    mock_build_location = mocker.patch(
        "app.tools.statement_builders.outages_statement_builder._build_outage_location_filter",
        return_value=None,
    )

    # Mock SQLAlchemy functions and chained methods
    mock_select_obj = MagicMock(spec=Select)  # Mock the Select object
    mock_where_obj = MagicMock(spec=Select)  # Mock the object returned by where()
    mock_order_by_obj = MagicMock(spec=Select)  # Mock the object returned by order_by()

    # Configure the chain: select().where().order_by()
    mock_select_func = mocker.patch(
        "app.tools.statement_builders.outages_statement_builder.select",
        return_value=mock_select_obj,
    )
    mock_select_obj.where.return_value = mock_where_obj
    mock_where_obj.order_by.return_value = (
        mock_order_by_obj  # Final object in this chain
    )

    # Mock and_ function
    mock_and_func = mocker.patch(
        "app.tools.statement_builders.outages_statement_builder.and_"
    )

    # Create the final mock objects that the .desc() calls should return
    mock_date_desc_result = MagicMock(name="Result of Outage.outage_date.desc()")
    mock_start_desc_result = MagicMock(name="Result of Outage.outage_start.desc()")

    # Create mock column objects
    mock_outage_date_col = MagicMock(name="MockOutage.outage_date")
    mock_outage_start_col = MagicMock(name="MockOutage.outage_start")

    # Configure the .desc() method on the mock columns to return the final mock objects
    mock_outage_date_col.desc.return_value = mock_date_desc_result
    mock_outage_start_col.desc.return_value = mock_start_desc_result

    # Patch the actual column attributes on the Outage class to return our mock columns
    # This intercepts access like Outage.outage_date
    mocker.patch.object(Outage, "outage_date", new=mock_outage_date_col)
    mocker.patch.object(Outage, "outage_start", new=mock_outage_start_col)

    return {
        "mock_build_date": mock_build_date,
        "mock_build_type": mock_build_type,
        "mock_build_location": mock_build_location,
        "mock_select_func": mock_select_func,
        "mock_select_obj": mock_select_obj,
        "mock_where_obj": mock_where_obj,
        "mock_order_by_obj": mock_order_by_obj,
        "mock_and_func": mock_and_func,
        # Pass the final results for assertion checks in tests
        "mock_date_desc": mock_date_desc_result,
        "mock_start_desc": mock_start_desc_result,
        # Optionally pass the mock columns if needed, though likely not required for assertions
        # "mock_outage_date_col": mock_outage_date_col,
        # "mock_outage_start_col": mock_outage_start_col,
    }


# --- Test Cases ---


def test_build_outages_statement_defaults(mock_dependencies):
    """Test with default arguments: no filters applied, default order."""
    result = build_outages_statement()

    # Check helpers called with defaults
    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with("*")
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])

    # Check select called
    mock_dependencies["mock_select_func"].assert_called_once_with(Outage)

    # Check where NOT called (since no filters returned)
    mock_dependencies["mock_select_obj"].where.assert_not_called()
    mock_dependencies["mock_and_func"].assert_not_called()

    # Check order_by IS called on the initial select object (since where wasn't called)
    # Verify the correct ordering columns were used
    mock_dependencies["mock_select_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_desc"], mock_dependencies["mock_start_desc"]
    )

    # The final result should be the object returned by order_by in this case
    # Correction: If where is not called, order_by is called on the object returned by select()
    assert result == mock_dependencies["mock_select_obj"].order_by.return_value


def test_build_outages_statement_with_date_filter(mock_dependencies):
    """Test with only a date filter applied."""
    mock_dependencies["mock_build_date"].return_value = MOCK_DATE_FILTER
    dates = ["2024-01-01"]

    result = build_outages_statement(outage_dates=dates)

    mock_dependencies["mock_build_date"].assert_called_once_with(dates)
    mock_dependencies["mock_build_type"].assert_called_once_with("*")  # Default
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])  # Default

    # Check select and where called
    mock_dependencies["mock_select_func"].assert_called_once_with(Outage)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_DATE_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )

    # Check order_by called on the object returned by where
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_desc"], mock_dependencies["mock_start_desc"]
    )

    # Final result is the object returned by order_by
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_outages_statement_with_type_filter(mock_dependencies):
    """Test with only a type filter applied."""
    mock_dependencies["mock_build_type"].return_value = MOCK_TYPE_FILTER
    outage_type = "Power Outage"

    result = build_outages_statement(outage_type=outage_type)

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with(outage_type)
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])

    mock_dependencies["mock_select_func"].assert_called_once_with(Outage)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_TYPE_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_desc"], mock_dependencies["mock_start_desc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_outages_statement_with_location_filter(mock_dependencies):
    """Test with only a location filter applied."""
    mock_dependencies["mock_build_location"].return_value = MOCK_LOCATION_FILTER
    locations = ["Area 51"]

    result = build_outages_statement(locations=locations)

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with("*")
    mock_dependencies["mock_build_location"].assert_called_once_with(locations)

    mock_dependencies["mock_select_func"].assert_called_once_with(Outage)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_LOCATION_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_desc"], mock_dependencies["mock_start_desc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_outages_statement_with_all_filters(mock_dependencies):
    """Test with date, type, and location filters applied."""
    mock_dependencies["mock_build_date"].return_value = MOCK_DATE_FILTER
    mock_dependencies["mock_build_type"].return_value = MOCK_TYPE_FILTER
    mock_dependencies["mock_build_location"].return_value = MOCK_LOCATION_FILTER
    dates = ["2024-01-01"]
    outage_type = "Water Leak"
    locations = ["Main Street", "Side Street"]

    result = build_outages_statement(
        outage_dates=dates, outage_type=outage_type, locations=locations
    )

    mock_dependencies["mock_build_date"].assert_called_once_with(dates)
    mock_dependencies["mock_build_type"].assert_called_once_with(outage_type)
    mock_dependencies["mock_build_location"].assert_called_once_with(locations)

    mock_dependencies["mock_select_func"].assert_called_once_with(Outage)
    # Check and_ called with all filters
    mock_dependencies["mock_and_func"].assert_called_once_with(
        MOCK_DATE_FILTER, MOCK_TYPE_FILTER, MOCK_LOCATION_FILTER
    )
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_desc"], mock_dependencies["mock_start_desc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_outages_statement_some_filters_none(mock_dependencies):
    """Test when some helper functions return None (no filter)."""
    mock_dependencies["mock_build_date"].return_value = None  # e.g., dates = ["*"]
    mock_dependencies["mock_build_type"].return_value = MOCK_TYPE_FILTER
    mock_dependencies["mock_build_location"].return_value = (
        None  # e.g., locations = ["*"]
    )
    outage_type = "Network Down"

    result = build_outages_statement(outage_type=outage_type)  # Defaults for others

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_type"].assert_called_once_with(outage_type)
    mock_dependencies["mock_build_location"].assert_called_once_with(["*"])

    mock_dependencies["mock_select_func"].assert_called_once_with(Outage)
    # and_ should only be called with the non-None filter
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_TYPE_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_desc"], mock_dependencies["mock_start_desc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


# Add more tests if specific edge cases for combinations are needed
# e.g., test date + location, date + type, type + location
