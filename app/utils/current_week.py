import datetime
from zoneinfo import ZoneInfo


def current_week() -> str:
    """
    Return the next 7 days starting from the current Greek date
    (calculated *inside* the function) in format: day name: corresponding date.
    """
    # Calculate current_date *each time* the function is called
    current_date = datetime.datetime.now(ZoneInfo("Europe/Athens")).date()
    days = []
    for i in range(7):
        day_date = current_date + datetime.timedelta(days=i)
        day_name = day_date.strftime("%A")
        days.append(f"{day_name}: {day_date}")
    return "\n".join(days)
