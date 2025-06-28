import datetime
from zoneinfo import ZoneInfo


def current_date() -> str:
    """
    Return the current Greek date as a formatted string.
    """
    # Calculate current_date *each time* the function is called
    today = datetime.datetime.now(ZoneInfo("Europe/Athens")).date()
    return f"Current date: {today}"
