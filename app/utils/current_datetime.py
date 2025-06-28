import datetime
from zoneinfo import ZoneInfo


def current_datetime() -> str:
    """
    Return the current Greek date and time as a formatted string.
    """
    # Calculate current_datetime *each time* the function is called
    now = datetime.datetime.now(ZoneInfo("Europe/Athens"))
    return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
