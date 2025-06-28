# Map tool names to their formatter functions
from .outages_formatter import format_outages
from .performances_formatter import format_performances
from .hospital_shifts_formatter import format_hospital_shifts
from .screenings_formatter import format_screenings

TOOL_FORMATTERS = {
    "outages": format_outages,
    "performances": format_performances,
    "hospital_shifts": format_hospital_shifts,
    "cinemas": format_screenings,
}
