import pytest
from unittest.mock import MagicMock
from sqlalchemy import Select  # For type hinting

# Import the function to test
from app.tools.statement_builders.hospital_shifts_statement_builder import (
    build_hospital_shifts_statement,
)

# Import the model for context, although its methods/attributes will be mocked
from app.db.models.hospital_shift_model import HospitalShift

# --- Mock Filters ---
# Create reusable mock filter objects to be returned by helper mocks
MOCK_DATE_FILTER = MagicMock(name="DateFilterCondition")
MOCK_NAME_FILTER = MagicMock(name="NameFilterCondition")
MOCK_SPECIALTY_FILTER = MagicMock(name="SpecialtyFilterCondition")

# --- Test Fixture for Mocking ---


@pytest.fixture
def mock_dependencies(mocker):
    """Fixture to mock all dependencies of build_hospital_shifts_statement."""
    # Mock the helper functions
    mock_build_date = mocker.patch(
        "app.tools.statement_builders.hospital_shifts_statement_builder._build_hospital_shift_date_filter",
        return_value=None,
    )
    mock_build_name = mocker.patch(
        "app.tools.statement_builders.hospital_shifts_statement_builder._build_hospital_name_filter",
        return_value=None,
    )
    mock_build_specialty = mocker.patch(
        "app.tools.statement_builders.hospital_shifts_statement_builder._build_specialties_filter",
        return_value=None,
    )

    # Mock SQLAlchemy functions and chained methods
    mock_select_obj = MagicMock(spec=Select)  # Mock the Select object
    mock_where_obj = MagicMock(spec=Select)  # Mock the object returned by where()
    mock_order_by_obj = MagicMock(spec=Select)  # Mock the object returned by order_by()

    # Configure the chain: select().where().order_by()
    mock_select_func = mocker.patch(
        "app.tools.statement_builders.hospital_shifts_statement_builder.select",
        return_value=mock_select_obj,
    )
    mock_select_obj.where.return_value = mock_where_obj
    # If where is called, order_by is called on its result
    mock_where_obj.order_by.return_value = mock_order_by_obj
    # If where is NOT called, order_by is called on the select result directly
    mock_select_obj.order_by.return_value = mock_order_by_obj  # Handle both cases

    # Mock and_ function
    mock_and_func = mocker.patch(
        "app.tools.statement_builders.hospital_shifts_statement_builder.and_"
    )

    # Create the final mock objects that the .asc() calls should return
    mock_date_asc_result = MagicMock(
        name="Result of HospitalShift.hospital_shift_date.asc()"
    )
    mock_name_asc_result = MagicMock(name="Result of HospitalShift.hospital_name.asc()")

    # Create mock column objects
    mock_shift_date_col = MagicMock(name="MockHospitalShift.hospital_shift_date")
    mock_hospital_name_col = MagicMock(name="MockHospitalShift.hospital_name")

    # Configure the .asc() method on the mock columns to return the final mock objects
    mock_shift_date_col.asc.return_value = mock_date_asc_result
    mock_hospital_name_col.asc.return_value = mock_name_asc_result

    # Patch the actual column attributes on the HospitalShift class
    mocker.patch.object(HospitalShift, "hospital_shift_date", new=mock_shift_date_col)
    mocker.patch.object(HospitalShift, "hospital_name", new=mock_hospital_name_col)

    return {
        "mock_build_date": mock_build_date,
        "mock_build_name": mock_build_name,
        "mock_build_specialty": mock_build_specialty,
        "mock_select_func": mock_select_func,
        "mock_select_obj": mock_select_obj,
        "mock_where_obj": mock_where_obj,
        "mock_order_by_obj": mock_order_by_obj,
        "mock_and_func": mock_and_func,
        "mock_date_asc": mock_date_asc_result,
        "mock_name_asc": mock_name_asc_result,
    }


# --- Test Cases ---


def test_build_hospital_shifts_statement_defaults(mock_dependencies):
    """Test with default arguments: no filters applied, default order."""
    result = build_hospital_shifts_statement()

    # Check helpers called with defaults
    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_specialty"].assert_called_once_with(["*"])

    # Check select called
    mock_dependencies["mock_select_func"].assert_called_once_with(HospitalShift)

    # Check where NOT called (since no filters returned)
    mock_dependencies["mock_select_obj"].where.assert_not_called()
    mock_dependencies["mock_and_func"].assert_not_called()

    # Check order_by IS called on the initial select object
    mock_dependencies["mock_select_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )

    # The final result should be the object returned by order_by
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_hospital_shifts_statement_with_date_filter(mock_dependencies):
    """Test with only a date filter applied."""
    mock_dependencies["mock_build_date"].return_value = MOCK_DATE_FILTER
    dates = ["2024-03-20"]

    result = build_hospital_shifts_statement(hospital_shift_dates=dates)

    mock_dependencies["mock_build_date"].assert_called_once_with(dates)
    mock_dependencies["mock_build_name"].assert_called_once_with(["*"])  # Default
    mock_dependencies["mock_build_specialty"].assert_called_once_with(["*"])  # Default

    # Check select and where called
    mock_dependencies["mock_select_func"].assert_called_once_with(HospitalShift)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_DATE_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )

    # Check order_by called on the object returned by where
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )

    # Final result is the object returned by order_by
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_hospital_shifts_statement_with_name_filter(mock_dependencies):
    """Test with only a name filter applied."""
    mock_dependencies["mock_build_name"].return_value = MOCK_NAME_FILTER
    names = ["General Hospital"]

    result = build_hospital_shifts_statement(hospital_names=names)

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(names)
    mock_dependencies["mock_build_specialty"].assert_called_once_with(["*"])

    mock_dependencies["mock_select_func"].assert_called_once_with(HospitalShift)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_NAME_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_hospital_shifts_statement_with_specialty_filter(mock_dependencies):
    """Test with only a specialty filter applied."""
    mock_dependencies["mock_build_specialty"].return_value = MOCK_SPECIALTY_FILTER
    specialties = ["Cardiology"]

    result = build_hospital_shifts_statement(specialties=specialties)

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_specialty"].assert_called_once_with(specialties)

    mock_dependencies["mock_select_func"].assert_called_once_with(HospitalShift)
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_SPECIALTY_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_hospital_shifts_statement_with_all_filters(mock_dependencies):
    """Test with date, name, and specialty filters applied."""
    mock_dependencies["mock_build_date"].return_value = MOCK_DATE_FILTER
    mock_dependencies["mock_build_name"].return_value = MOCK_NAME_FILTER
    mock_dependencies["mock_build_specialty"].return_value = MOCK_SPECIALTY_FILTER
    dates = ["2024-03-20"]
    names = ["City Hospital"]
    specialties = ["Neurology", "Pediatrics"]

    result = build_hospital_shifts_statement(
        hospital_shift_dates=dates, hospital_names=names, specialties=specialties
    )

    mock_dependencies["mock_build_date"].assert_called_once_with(dates)
    mock_dependencies["mock_build_name"].assert_called_once_with(names)
    mock_dependencies["mock_build_specialty"].assert_called_once_with(specialties)

    mock_dependencies["mock_select_func"].assert_called_once_with(HospitalShift)
    # Check and_ called with all filters
    mock_dependencies["mock_and_func"].assert_called_once_with(
        MOCK_DATE_FILTER, MOCK_NAME_FILTER, MOCK_SPECIALTY_FILTER
    )
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]


def test_build_hospital_shifts_statement_some_filters_none(mock_dependencies):
    """Test when some helper functions return None (no filter)."""
    mock_dependencies["mock_build_date"].return_value = None  # e.g., dates = ["*"]
    mock_dependencies["mock_build_name"].return_value = MOCK_NAME_FILTER
    mock_dependencies["mock_build_specialty"].return_value = (
        None  # e.g., specialties = ["*"]
    )
    names = ["Regional Hospital"]

    result = build_hospital_shifts_statement(
        hospital_names=names
    )  # Defaults for others

    mock_dependencies["mock_build_date"].assert_called_once_with(["*"])
    mock_dependencies["mock_build_name"].assert_called_once_with(names)
    mock_dependencies["mock_build_specialty"].assert_called_once_with(["*"])

    mock_dependencies["mock_select_func"].assert_called_once_with(HospitalShift)
    # and_ should only be called with the non-None filter
    mock_dependencies["mock_and_func"].assert_called_once_with(MOCK_NAME_FILTER)
    mock_dependencies["mock_select_obj"].where.assert_called_once_with(
        mock_dependencies["mock_and_func"].return_value
    )
    mock_dependencies["mock_where_obj"].order_by.assert_called_once_with(
        mock_dependencies["mock_date_asc"], mock_dependencies["mock_name_asc"]
    )
    assert result == mock_dependencies["mock_order_by_obj"]
