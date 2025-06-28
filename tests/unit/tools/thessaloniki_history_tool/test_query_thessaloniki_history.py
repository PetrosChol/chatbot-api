import pytest
from unittest.mock import patch

# Η συνάρτηση υπό δοκιμή
from app.tools.statement_builders.thessaloniki_history_statement_builder import (
    query_thessaloniki_history,
)

# Το πραγματικό κείμενο, για σύγκριση στην περίπτωση επιτυχίας αν δεν το κάνουμε mock
# from app.tools.thessaloniki_history_data import THESSALONIKI_HISTORY_TEXT


@pytest.mark.asyncio
@patch("app.tools.statement_builders.thessaloniki_history_statement_builder.logger")
# Κάνουμε patch το THESSALONIKI_HISTORY_TEXT που χρησιμοποιείται από τη συνάρτηση υπό δοκιμή
@patch(
    "app.tools.statement_builders.thessaloniki_history_statement_builder.THESSALONIKI_HISTORY_TEXT",
    "Mocked history data.",
)
async def test_query_success_returns_mocked_data(mock_logger):
    """
    Tests that query_thessaloniki_history successfully returns the (mocked) history text.
    """
    search_query = "any query"
    expected_text = "Mocked history data."

    result = await query_thessaloniki_history(search_query)

    assert result == expected_text
    mock_logger.info.assert_any_call(
        f"Λήφθηκε ερώτημα αναζήτησης ιστορίας (μήκος: {len(search_query)}). "
        "Θα επιστραφεί ολόκληρο το ιστορικό κείμενο."
    )
    mock_logger.info.assert_any_call(
        "Επιστροφή ολόκληρου του αποθηκευμένου ιστορικού κειμένου της Θεσσαλονίκης."
    )


@pytest.mark.asyncio
@patch("app.tools.statement_builders.thessaloniki_history_statement_builder.logger")
# Κάνουμε patch το THESSALONIKI_HISTORY_TEXT ώστε να είναι κενό
@patch(
    "app.tools.statement_builders.thessaloniki_history_statement_builder.THESSALONIKI_HISTORY_TEXT",
    "",
)
async def test_query_empty_history_text_returns_none(mock_logger):
    """
    Tests that query_thessaloniki_history returns None and logs a warning
    if THESSALONIKI_HISTORY_TEXT is empty.
    """
    search_query = "test query for empty text"

    result = await query_thessaloniki_history(search_query)

    assert result is None
    mock_logger.warning.assert_called_once_with(
        "Το κείμενο ιστορίας της Θεσσαλονίκης είναι κενό ή δεν φορτώθηκε."
    )
    mock_logger.info.assert_any_call(  # Η πρώτη κλήση info γίνεται πάντα
        f"Λήφθηκε ερώτημα αναζήτησης ιστορίας (μήκος: {len(search_query)}). "
        "Θα επιστραφεί ολόκληρο το ιστορικό κείμενο."
    )


@pytest.mark.asyncio
@patch("app.tools.statement_builders.thessaloniki_history_statement_builder.logger")
# Προσομοιώνουμε ένα σφάλμα κατά την πρόσβαση ή χρήση του THESSALONIKI_HISTORY_TEXT
# ή κατά την κλήση μιας εσωτερικής συνάρτησης (π.χ. logger.info μέσα στο try block).
# Εδώ, θα κάνουμε το logger.info μέσα στο try block να προκαλέσει σφάλμα.
async def test_query_handles_unexpected_internal_error(mock_sut_logger, mocker):
    """
    Tests handling of unexpected errors within the try block of query_thessaloniki_history.
    """
    search_query = "query leading to error"
    test_exception = Exception("Simulated internal error")

    # Κάνουμε patch το THESSALONIKI_HISTORY_TEXT ώστε να μην είναι κενό, για να περάσει τον πρώτο έλεγχο.
    mocker.patch(
        "app.tools.statement_builders.thessaloniki_history_statement_builder.THESSALONIKI_HISTORY_TEXT",
        "Some valid text.",
    )

    # Κάνουμε patch τη δεύτερη κλήση logger.info (αυτή που είναι μέσα στο try block) για να προκαλέσει σφάλμα.
    # Η πρώτη κλήση logger.info είναι έξω από το try block.
    # Η MagicMock μπορεί να έχει διαφορετικά side_effects για διαδοχικές κλήσεις.
    mock_sut_logger.info.side_effect = [
        None,  # Για την πρώτη κλήση logger.info (έξω από το try)
        test_exception,  # Για τη δεύτερη κλήση logger.info (μέσα στο try)
    ]

    result = await query_thessaloniki_history(search_query)

    assert result is None
    mock_sut_logger.error.assert_called_once_with(
        f"Απρόσμενο σφάλμα κατά την ανάκτηση του ιστορικού κειμένου (μήκος ερωτήματος: {len(search_query)}): {test_exception}",
        exc_info=True,
    )
    # Έλεγχος ότι η πρώτη κλήση info έγινε
    mock_sut_logger.info.assert_any_call(
        f"Λήφθηκε ερώτημα αναζήτησης ιστορίας (μήκος: {len(search_query)}). "
        "Θα επιστραφεί ολόκληρο το ιστορικό κείμενο."
    )
