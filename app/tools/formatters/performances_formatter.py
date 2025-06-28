import logging
from typing import List
from app.db.models.performance_model import Performance

logger = logging.getLogger(__name__)


def format_performances(performances: List[Performance]) -> str:
    """
    Formats a list of Performance objects into a human-readable string.

    Args:
        performances: A list of Performance model instances.

    Returns:
        A formatted string summarizing the performances, or a message indicating none were found.
    """
    if not performances:
        return "Δεν βρέθηκαν παραστάσεις που να ταιριάζουν με τα κριτήριά σας."

    formatted_lines = ["Βρέθηκαν οι ακόλουθες παραστάσεις:"]

    # Group by date for better readability
    performances_by_date = {}
    # The input 'performances' is expected to be a list of tuples, each containing one Performance object.
    for perf_tuple in performances:
        if (
            not perf_tuple
        ):  # Handle potential empty tuples if the query returns nothing in a row
            logger.warning("Encountered an empty tuple in performance results.")
            continue
        perf = perf_tuple[0]  # Extract the Performance object from the tuple
        date_str = (
            perf.performance_date.strftime("%d/%m/%Y")
            if perf.performance_date
            else "Άγνωστη Ημερομηνία"
        )
        if date_str not in performances_by_date:
            performances_by_date[date_str] = []
        performances_by_date[date_str].append(perf)  # Append the extracted object

    for date_str, daily_performances in sorted(performances_by_date.items()):
        formatted_lines.append(f"\n--- {date_str} ---")
        # Sort by time, then name
        key_func = lambda p: (
            p.performance_start_time is None,
            p.performance_start_time,
            p.performance_name or "",
        )
        for perf in sorted(daily_performances, key=key_func):
            line = f"- Παράσταση: {perf.performance_name or 'Άγνωστο Όνομα'}"
            if perf.performance_location:
                line += f", Τοποθεσία: {perf.performance_location}"
            if perf.performance_type:
                line += f", Είδος: {perf.performance_type}"
            if perf.performance_start_time:
                line += (
                    f", Ώρα Έναρξης: {perf.performance_start_time.strftime('%H:%M')}"
                )
            else:
                line += ", Ώρα Έναρξης: Άγνωστη"
            formatted_lines.append(line)

    return "\n".join(formatted_lines)
