# This file makes the formatters directory a Python package.
# You can optionally import formatters here for easier access elsewhere.

from .outages_formatter import format_outages
from .performances_formatter import format_performances
from .hospital_shifts_formatter import format_hospital_shifts
from .screenings_formatter import format_screenings

# Import the history formatter if/when created
# from .history_formatter import format_history

__all__ = [
    "format_outages",
    "format_performances",
    "format_hospital_shifts",
    "format_screenings",
    # "format_history",
    "TOOL_FORMATTERS",  # Add the mapping dictionary
]
