import logging
from typing import Optional
from app.tools.thessaloniki_history_data import THESSALONIKI_HISTORY_TEXT

logger = logging.getLogger(__name__)


async def query_thessaloniki_history(search_query: str) -> Optional[str]:
    """
    Ανακτά ολόκληρη την τεκμηρίωση της ιστορίας της Θεσσαλονίκης.
    Η παράμετρος search_query αγνοείται προς το παρόν, καθώς επιστρέφεται
    ολόκληρο το κείμενο.

    Returns:
        Το ιστορικό κείμενο ως string, ή None σε περίπτωση απρόσμενου σφάλματος.
    """
    logger.info(
        f"Λήφθηκε ερώτημα αναζήτησης ιστορίας (μήκος: {len(search_query)}). "
        "Θα επιστραφεί ολόκληρο το ιστορικό κείμενο."
    )

    try:
        history_text = THESSALONIKI_HISTORY_TEXT
        if not history_text:
            logger.warning(
                "Το κείμενο ιστορίας της Θεσσαλονίκης είναι κενό ή δεν φορτώθηκε."
            )
            return None

        logger.info(
            "Επιστροφή ολόκληρου του αποθηκευμένου ιστορικού κειμένου της Θεσσαλονίκης."
        )
        return history_text
    except Exception as e:
        logger.error(
            f"Απρόσμενο σφάλμα κατά την ανάκτηση του ιστορικού κειμένου (μήκος ερωτήματος: {len(search_query)}): {e}",
            exc_info=True,
        )
        return None
