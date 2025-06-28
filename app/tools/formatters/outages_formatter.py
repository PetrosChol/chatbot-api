import logging
from typing import List
from app.db.models.outage_model import Outage

logger = logging.getLogger(__name__)


def format_outages(outages: List[Outage]) -> str:
    """
    Formats a list of Outage objects into a human-readable string.

    Args:
        outages: A list of Outage model instances.

    Returns:
        A formatted string summarizing the outages, or a message indicating no outages were found.
    """
    if not outages:
        return "Δεν βρέθηκαν προγραμματισμένες διακοπές που να ταιριάζουν με τα κριτήριά σας."

    formatted_lines = ["Βρέθηκαν οι ακόλουθες προγραμματισμένες διακοπές:"]

    # Group by date for better readability
    outages_by_date = {}
    for outage in outages:
        date_str = (
            outage.outage_date.strftime("%d/%m/%Y")
            if outage.outage_date
            else "Άγνωστη Ημερομηνία"
        )
        if date_str not in outages_by_date:
            outages_by_date[date_str] = []
        outages_by_date[date_str].append(outage)

    for date_str, daily_outages in sorted(outages_by_date.items()):
        formatted_lines.append(f"\n--- {date_str} ---")
        for outage in sorted(
            daily_outages, key=lambda o: (o.outage_start is None, o.outage_start)
        ):
            outage_type_display = outage.outage_type or "Άγνωστος"
            if outage.outage_type == "power":
                outage_type_display = "ρεύματος"
            elif outage.outage_type == "water":
                outage_type_display = "νερού"

            line = f"- Τύπος: {outage_type_display}"
            if outage.outage_location:
                line += f", Τοποθεσία: {outage.outage_location}"
            if outage.outage_affected_areas:
                # Split potentially long strings, join with comma
                areas = ", ".join(outage.outage_affected_areas.splitlines())
                line += f", Περιοχές: {areas}"

            start_time = (
                outage.outage_start.strftime("%H:%M")
                if outage.outage_start
                else "Άγνωστη"
            )
            end_time = (
                outage.outage_end.strftime("%H:%M") if outage.outage_end else "Άγνωστη"
            )
            line += f", Ώρες: {start_time} - {end_time}"
            formatted_lines.append(line)

    return "\n".join(formatted_lines)
