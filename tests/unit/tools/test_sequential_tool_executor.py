import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

# Import schemas used for mocking
# Replace ToolCallSchema with a concrete example like OutagesArgs
from app.agent.schemas import (
    OutagesArgs,
    MovieScreeningsArgs,
    MusicAndTheaterPerformancesArgs,  # Added import
)

# Module to test
from app.tools import sequential_tool_executor
from app.db.models import Outage, Performance  # Import models for mocking results

# --- Mock Objects & Fixtures ---


class DummySession:
    """Simulates the async context manager for db.begin()."""

    def __init__(self):
        self.began = False
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        self.began = True
        # Return a mock transaction object if needed, otherwise self or None
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rolled_back = True
        else:
            self.committed = True
        # Prevent exception propagation by returning True if handled
        return False  # Propagate exceptions by default

    # Add commit/rollback if begin() returns a transaction object that needs them
    # async def commit(self): self.committed = True
    # async def rollback(self): self.rolled_back = True


@pytest.fixture
def mock_db_session():
    """Fixture for a mock DB session with a begin() method."""
    session = AsyncMock(spec=AsyncSession)
    session.begin = MagicMock(return_value=DummySession())
    return session


@pytest.fixture
def mock_tool_registry(mocker):
    """Fixture to patch the TOOL_REGISTRY."""
    # Use the actual tool names defined in the schemas as keys
    # Mock tools to return lists of model instances or tuples of model instances
    # as expected by the formatters.
    mock_outage_instance = MagicMock(spec=Outage)
    mock_outage_instance.outage_date = None  # Add necessary attributes for formatter
    mock_outage_instance.outage_start = None
    mock_outage_instance.outage_type = "mock_type"
    mock_outage_instance.outage_location = "mock_location"
    mock_outage_instance.outage_affected_areas = "mock_areas"
    mock_outage_instance.outage_end = None

    mock_performance_instance_tuple = (
        MagicMock(spec=Performance),
    )  # Formatter expects a list of tuples
    mock_performance_instance_tuple[0].performance_date = None
    mock_performance_instance_tuple[0].performance_start_time = None
    mock_performance_instance_tuple[0].performance_name = "mock_perf"
    mock_performance_instance_tuple[0].performance_location = "mock_loc"
    mock_performance_instance_tuple[0].performance_type = "mock_type"

    mock_registry = {
        "outages": AsyncMock(
            return_value=[mock_outage_instance]  # Return a list of Outage objects
        ),
        "cinemas": AsyncMock(side_effect=ValueError("Tool execution failed")),
        "performances": AsyncMock(
            return_value=[
                mock_performance_instance_tuple
            ]  # Return a list of tuples containing Performance objects
        ),
    }
    # Patch the actual TOOL_REGISTRY in the module under test
    return mocker.patch.dict(
        sequential_tool_executor.TOOL_REGISTRY, mock_registry, clear=True
    )


# --- Test Cases ---


@pytest.mark.asyncio
async def test_no_tool_calls_returns_empty_dict(mock_db_session):
    """Test execution with an empty list of tool calls."""
    tool_calls = []
    results = await sequential_tool_executor.execute_tools_sequentially(
        tool_calls, mock_db_session
    )
    assert results == {}
    # Verify transaction was started and committed (even if empty)
    mock_db_session.begin.assert_called_once()
    assert mock_db_session.begin.return_value.committed is True
    assert mock_db_session.begin.return_value.rolled_back is False


@pytest.mark.asyncio
@patch("app.tools.sequential_tool_executor.logger")
async def test_missing_tool_in_registry(
    mock_logger, mock_db_session, mock_tool_registry
):
    """Test execution when a requested tool is not in the registry."""
    # Instantiate schemas with default args. 'name' is set by the model.
    tool_call_success = OutagesArgs()  # name defaults to "outages"
    # Create a mock object for the missing tool call, as we can't easily
    # instantiate an Args schema with an arbitrary 'name'.
    tool_call_missing = MagicMock()
    tool_call_missing.name = "tool_missing"
    # Define the expected parameters the executor would extract if it were a Pydantic model
    # For this test, we assume it has no specific parameters needed for the error path.
    # If the executor logic changes to require specific fields even for missing tools, adjust this.
    # tool_call_missing.model_dump.return_value = {} # Example if needed

    tool_calls = [tool_call_success, tool_call_missing]

    # Expected parameters extracted from the successful tool call model
    expected_success_params = tool_call_success.model_dump(exclude={"name"})
    # The formatter for "outages" will be called.
    # The mock_tool_registry provides a mock Outage object.
    # The outages_formatter will produce a specific string based on this.
    # We don't need to patch the formatter itself if the mock data is correct.
    expected_formatted_outage_result = "Βρέθηκαν οι ακόλουθες προγραμματισμένες διακοπές:\n\n--- Άγνωστη Ημερομηνία ---\n- Τύπος: mock_type, Τοποθεσία: mock_location, Περιοχές: mock_areas, Ώρες: Άγνωστη - Άγνωστη"
    expected_results = {
        "outages": expected_formatted_outage_result,
        "tool_missing": {"error": "Tool 'tool_missing' not available."},
    }

    results = await sequential_tool_executor.execute_tools_sequentially(
        tool_calls, mock_db_session
    )

    assert results == expected_results
    # Check logs
    mock_logger.warning.assert_called_once_with(
        "Tool 'tool_missing' not found in registry."
    )
    # Check that the successful tool (mapped to "outages" in fixture) was called with extracted params
    mock_tool_registry["outages"].assert_awaited_once_with(
        params=expected_success_params, db=mock_db_session
    )
    # Verify transaction committed
    mock_db_session.begin.assert_called_once()
    assert mock_db_session.begin.return_value.committed is True
    assert mock_db_session.begin.return_value.rolled_back is False


@pytest.mark.asyncio
async def test_successful_tool_execution(mock_db_session, mock_tool_registry):
    """Test successful execution of multiple tools."""
    # Instantiate schemas with specific arguments. 'name' is set by the model.
    tool_call_1 = OutagesArgs(locations=["Area 51"])  # name defaults to "outages"
    # Instantiate the correct schema for the 'performances' tool
    tool_call_2 = MusicAndTheaterPerformancesArgs(
        performance_names=["Concert"]
    )  # name defaults to "performances"

    tool_calls = [tool_call_1, tool_call_2]

    # Expected parameters extracted from the models
    expected_params_1 = tool_call_1.model_dump(exclude={"name"})
    expected_params_2 = tool_call_2.model_dump(exclude={"name"})

    # The formatters will be called with the mock model instances.
    expected_formatted_outage_result = "Βρέθηκαν οι ακόλουθες προγραμματισμένες διακοπές:\n\n--- Άγνωστη Ημερομηνία ---\n- Τύπος: mock_type, Τοποθεσία: mock_location, Περιοχές: mock_areas, Ώρες: Άγνωστη - Άγνωστη"
    expected_formatted_performance_result = "Βρέθηκαν οι ακόλουθες παραστάσεις:\n\n--- Άγνωστη Ημερομηνία ---\n- Παράσταση: mock_perf, Τοποθεσία: mock_loc, Είδος: mock_type, Ώρα Έναρξης: Άγνωστη"

    expected_results = {
        "outages": expected_formatted_outage_result,
        "performances": expected_formatted_performance_result,
    }

    results = await sequential_tool_executor.execute_tools_sequentially(
        tool_calls, mock_db_session
    )

    assert results == expected_results
    # Check tool calls using actual tool names and extracted params
    mock_tool_registry["outages"].assert_awaited_once_with(
        params=expected_params_1, db=mock_db_session
    )
    mock_tool_registry["performances"].assert_awaited_once_with(
        params=expected_params_2, db=mock_db_session
    )
    # Verify transaction committed
    mock_db_session.begin.assert_called_once()
    assert mock_db_session.begin.return_value.committed is True
    assert mock_db_session.begin.return_value.rolled_back is False


@pytest.mark.asyncio
@patch("app.tools.sequential_tool_executor.logger")
async def test_tool_execution_failure(mock_logger, mock_db_session, mock_tool_registry):
    """Test execution when one tool fails."""
    # Instantiate schemas with default/specific arguments. 'name' is set by the model.
    tool_call_1 = OutagesArgs()  # name="outages"
    tool_call_2 = MovieScreeningsArgs(
        movies=["Fail Movie"]
    )  # name="cinemas" (maps to failing tool in fixture)
    tool_call_3 = MusicAndTheaterPerformancesArgs()  # name="performances"

    tool_calls = [tool_call_1, tool_call_2, tool_call_3]

    # Expected parameters extracted from the models
    expected_params_1 = tool_call_1.model_dump(exclude={"name"})
    expected_params_2 = tool_call_2.model_dump(exclude={"name"})

    error_message = (
        "Tool execution failed"  # From mock_tool_registry['cinemas'] side_effect
    )

    # Expect the exception to propagate out because we re-raise it now
    with pytest.raises(ValueError, match=error_message):
        await sequential_tool_executor.execute_tools_sequentially(
            tool_calls, mock_db_session
        )

    # Check tool calls using actual tool names and extracted params
    mock_tool_registry["outages"].assert_awaited_once_with(
        params=expected_params_1, db=mock_db_session
    )
    mock_tool_registry["cinemas"].assert_awaited_once_with(
        params=expected_params_2, db=mock_db_session
    )
    # The third tool should NOT have been called because the second one failed and raised
    mock_tool_registry["performances"].assert_not_awaited()
    # Check logs
    mock_logger.error.assert_called_once()
    # Check specific parts of the log message
    log_args, log_kwargs = mock_logger.error.call_args
    assert (
        "Error executing tool 'cinemas'" in log_args[0]
    )  # Use actual failing tool name
    assert (
        error_message in log_args[0]
    )  # Check if the original exception message is included
    assert log_kwargs.get("exc_info") is True  # Check if stack trace was logged

    # Verify transaction was rolled back because the exception propagated
    mock_db_session.begin.assert_called_once()
    assert mock_db_session.begin.return_value.committed is False
    assert mock_db_session.begin.return_value.rolled_back is True


@pytest.mark.asyncio
@patch("app.tools.sequential_tool_executor.logger")
async def test_tool_execution_failure_stops_transaction(
    mock_logger, mock_db_session, mock_tool_registry
):
    """Test execution failure where the exception propagates and causes rollback."""
    # Modify the failing tool mock to re-raise the exception
    failing_tool_exception = ValueError("Critical tool failure")
    # Assume tool_fail maps to "cinemas" in the mock registry
    mock_tool_registry["cinemas"].side_effect = failing_tool_exception

    # Instantiate schemas with default/specific arguments. 'name' is set by the model.
    tool_call_1 = OutagesArgs()  # name="outages"
    tool_call_2 = MovieScreeningsArgs(movies=["Critical Fail Movie"])  # name="cinemas"
    tool_call_3 = MusicAndTheaterPerformancesArgs()  # name="performances"

    tool_calls = [tool_call_1, tool_call_2, tool_call_3]

    # Expected parameters extracted from the models that should be called
    expected_params_1 = tool_call_1.model_dump(exclude={"name"})
    expected_params_2 = tool_call_2.model_dump(exclude={"name"})
    # expected_params_3 is not needed as the tool won't be called

    # Expect the exception to propagate out of the function
    with pytest.raises(ValueError, match="Critical tool failure"):
        await sequential_tool_executor.execute_tools_sequentially(
            tool_calls, mock_db_session
        )

    # Check which tools were called using actual names and extracted params
    mock_tool_registry["outages"].assert_awaited_once_with(
        params=expected_params_1, db=mock_db_session
    )
    mock_tool_registry["cinemas"].assert_awaited_once_with(
        params=expected_params_2, db=mock_db_session
    )
    mock_tool_registry["performances"].assert_not_awaited()  # Should not be reached

    # Check logs (error should still be logged before re-raising)
    mock_logger.error.assert_called_once()
    log_args, log_kwargs = mock_logger.error.call_args
    assert (
        "Error executing tool 'cinemas'" in log_args[0]
    )  # Use actual failing tool name
    assert str(failing_tool_exception) in log_args[0]
    assert log_kwargs.get("exc_info") is True

    # Verify transaction was rolled back because the exception propagated
    mock_db_session.begin.assert_called_once()
    assert mock_db_session.begin.return_value.committed is False
    assert mock_db_session.begin.return_value.rolled_back is True
