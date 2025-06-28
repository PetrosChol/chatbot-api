import logging
from typing import List
from app.db.models.hospital_shift_model import HospitalShift

logger = logging.getLogger(__name__)


def format_hospital_shifts(shifts: List[HospitalShift]) -> str:
    """
    Formats a list of HospitalShift objects into a human-readable string.

    Args:
        shifts: A list of HospitalShift model instances.

    Returns:
        A formatted string summarizing the hospital shifts, or a message indicating none were found.
    """
    if not shifts:
        return (
            "Δεν βρέθηκαν εφημερίες νοσοκομείων που να ταιριάζουν με τα κριτήριά σας."
        )

    formatted_lines = ["Βρέθηκαν οι ακόλουθες εφημερίες νοσοκομείων:"]

    # Group by date for better readability
    shifts_by_date = {}
    for shift in shifts:
        date_str = (
            shift.hospital_shift_date.strftime("%d/%m/%Y")
            if shift.hospital_shift_date
            else "Άγνωστη Ημερομηνία"
        )
        if date_str not in shifts_by_date:
            shifts_by_date[date_str] = []
        shifts_by_date[date_str].append(shift)

    for date_str, daily_shifts in sorted(shifts_by_date.items()):
        formatted_lines.append(f"\n--- {date_str} ---")
        # Sort by hospital name
        for shift in sorted(daily_shifts, key=lambda s: s.hospital_name or ""):
            line = f"- Νοσοκομείο: {shift.hospital_name or 'Άγνωστο Όνομα'}"

            time_parts = []
            if shift.hospital_shift_start_time:
                time_parts.append(
                    f"Έναρξη: {shift.hospital_shift_start_time.strftime('%H:%M')}"
                )
            if shift.hospital_shift_end_time:
                time_parts.append(
                    f"Λήξη: {shift.hospital_shift_end_time.strftime('%H:%M')}"
                )

            if time_parts:
                line += f" ({', '.join(time_parts)})"

            if shift.specialties:
                # Split potentially long strings, join with comma
                specs = ", ".join(shift.specialties.splitlines())
                line += f", Ειδικότητες: {specs}"

            if shift.address:
                line += f", Διεύθυνση: {shift.address}"
            if shift.phone_number:
                line += f", Τηλέφωνο: {shift.phone_number}"

            formatted_lines.append(line)

    return "\n".join(formatted_lines)
