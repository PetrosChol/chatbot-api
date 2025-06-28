import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Η select δεν χρειάζεται πλέον εδώ, καθώς το history tool δεν φτιάχνει SQL statement
# from sqlalchemy import select

# Υποθέτουμε ότι το tool_registry βρίσκεται στο app.tools.tool_registry
from app.tools import tool_registry  # Εισάγουμε ολόκληρο το module

# Άλλα imports που μπορεί να χρειάζονται για άλλα εργαλεία, αν υπάρχουν στο αρχείο
# from app.db.models.outage_model import Outage
# from app.db.models.cinema_models import Screening
# from app.db.models.hospital_shift_model import HospitalShift
# from app.db.models.performance_model import Performance


# Mocking data for other tools if they are tested in this file
# ... ( παραδείγματα mock data για άλλα εργαλεία )


@pytest.mark.asyncio
# Κάνουμε patch τη συνάρτηση query_thessaloniki_history που καλείται *μέσα* από το run_history
@patch("app.tools.tool_registry.query_thessaloniki_history")
async def test_run_history_success(
    mock_query_history_call_patch, mocker
):  # Το όνομα του patch argument
    """Test the run_history tool function on success."""
    mock_db = AsyncMock(spec=AsyncSession)

    expected_history_text = "Αυτό είναι ένα ιστορικό γεγονός."

    # Χρησιμοποιούμε το mocker για να αντικαταστήσουμε το mock που δημιουργήθηκε από το @patch
    # με ένα AsyncMock, ώστε να μπορούμε να χρησιμοποιήσουμε το assert_awaited_once_with.
    # Εναλλακτικά, το ίδιο το @patch μπορεί να πάρει `new_callable=AsyncMock`.
    mock_query_history_actual_mock = AsyncMock(return_value=expected_history_text)
    mocker.patch(
        "app.tools.tool_registry.query_thessaloniki_history",
        new=mock_query_history_actual_mock,
    )

    params = {"search_query": "White Tower"}

    result = await tool_registry.run_history(params=params, db=mock_db)

    # Διορθωμένη κλήση: positional argument αντί για keyword argument
    mock_query_history_actual_mock.assert_awaited_once_with(params["search_query"])
    assert result == expected_history_text
    mock_db.execute.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.tools.tool_registry.query_thessaloniki_history")
@patch("app.tools.tool_registry.logger")
async def test_run_history_query_returns_none(
    mock_tool_logger, mock_query_history_call_patch, mocker
):
    """Test run_history when query_thessaloniki_history returns None."""
    mock_db = AsyncMock(spec=AsyncSession)

    mock_query_history_actual_mock = AsyncMock(return_value=None)
    mocker.patch(
        "app.tools.tool_registry.query_thessaloniki_history",
        new=mock_query_history_actual_mock,
    )

    params = {"search_query": "Obscure topic"}
    # Το μήνυμα που επιστρέφεται από το run_history όταν το query_thessaloniki_history επιστρέφει None
    # όπως ορίζεται στο app/tools/tool_registry.py (με βάση την παρεχόμενη πληροφορία)
    expected_message_on_none = "Δεν ήταν δυνατή η ανάκτηση των ιστορικών πληροφοριών."

    result = await tool_registry.run_history(params=params, db=mock_db)

    # Διορθωμένη κλήση: positional argument
    mock_query_history_actual_mock.assert_awaited_once_with(params["search_query"])
    mock_db.execute.assert_not_awaited()
    assert result == expected_message_on_none

    # Ελέγχουμε το warning log που γίνεται από το run_history στο app/tools/tool_registry.py
    # (με βάση την παρεχόμενη πληροφορία για το app/tools/tool_registry.py)
    mock_tool_logger.warning.assert_called_once_with(
        "Η ανάκτηση του ιστορικού κειμένου απέτυχε ή επέστρεψε None."
    )


# ... (άλλες δοκιμές για άλλα εργαλεία, αν υπάρχουν)
