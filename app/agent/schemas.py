from pydantic import BaseModel, Field
from typing import List, Union, Optional, Literal
from enum import Enum


# Define Enum classes for specific fields
class OutageTypeEnum(str, Enum):
    POWER = "power"
    WATER = "water"
    BOTH = "*"  # Represents 'any' or 'all' types


class CinemaEnum(str, Enum):
    VILLAGE = "Village"
    ODEON = "Odeon"
    CINEPLEXX = "Cineplexx"
    ALL = "*"  # Represents 'any' or 'all' cinemas


class PerformanceTypeEnum(str, Enum):
    MUSICAL = "musical"
    THEATRICAL = "theatrical"
    BOTH = "*"  # Represents 'any' or 'all' types


# --- Tool Argument Schemas ---


class OutagesArgs(BaseModel):
    """Arguments for querying power or water outages."""

    name: Literal["outages"] = "outages"  # Tool name identifier
    outage_dates: List[str] = Field(
        default=["*"], description="List of dates (YYYY-MM-DD) or '*' for any date."
    )
    outage_type: OutageTypeEnum = Field(
        default=OutageTypeEnum.BOTH,
        description="Type of outage ('power', 'water', or '*').",
    )
    locations: List[str] = Field(
        default=["*"], description="List of locations or '*' for any location."
    )
    affected_areas: List[str] = Field(
        default=["*"], description="List of affected areas or '*' for any area."
    )


class MovieScreeningsArgs(BaseModel):
    """Arguments for querying movie screenings."""

    name: Literal["cinemas"] = "cinemas"  # Tool name identifier matches registry key
    screening_dates: List[str] = Field(
        default=["*"], description="List of dates (YYYY-MM-DD) or '*' for any date."
    )
    movies: List[str] = Field(
        default=["*"], description="List of movie titles or '*' for any movie."
    )
    cinemas: List[CinemaEnum] = Field(
        default=[CinemaEnum.ALL],
        description="List of cinema names or '*' for any cinema.",
    )
    halls_and_screening_times: bool = Field(
        default=False,
        description="True if user wants to know about details including specific screening times and hall names. False for more general information.",
    )
    genres: List[str] = Field(
        default=["*"], description="List of movie genres or '*' for any genre."
    )
    year: Optional[int] = Field(
        default=None, description="Movie release year or None for any year."
    )


class HospitalShiftsArgs(BaseModel):
    """Arguments for querying hospital shifts."""

    name: Literal["hospital_shifts"] = "hospital_shifts"  # Tool name identifier
    hospital_shift_dates: List[str] = Field(
        default=["*"], description="List of dates (YYYY-MM-DD) or '*' for any date."
    )
    hospital_names: List[str] = Field(
        default=["*"], description="List of hospital names or '*' for any hospital."
    )
    hospital_shifts_start_time: str = Field(
        default="*",
        description="Start time of hospital shifts (HH:MM:SS) or '*' for any start time.",
    )
    hospital_shifts_end_time: str = Field(
        default="*",
        description="End time of hospital shifts (HH:MM:SS) or '*' for any end time.",
    )
    specialties: List[str] = Field(
        default=["*"],
        description="List of medical specialties or '*' for any specialty.",
    )
    include_contact_info: bool = Field(
        default=False,
        description="True if user wants hospital address and phone number.",
    )


class ThessalonikiHistoryArgs(BaseModel):
    """Arguments for querying Thessaloniki history documents."""

    name: Literal["history"] = "history"  # Tool name identifier
    search_query: str = Field(
        ...,
        description="The specific question or topic to search for in the history documents.",
    )


class MusicAndTheaterPerformancesArgs(BaseModel):
    """Arguments for querying musical and theatrical performances."""

    name: Literal["performances"] = "performances"  # Tool name identifier
    performance_dates: List[str] = Field(
        default=["*"], description="List of dates (YYYY-MM-DD) or '*' for any date."
    )
    performance_names: List[str] = Field(
        default=["*"],
        description="List of performance titles or '*' for any performance.",
    )
    performance_locations: List[str] = Field(
        default=["*"],
        description="List of performance locations or '*' for any location.",
    )
    performance_type: PerformanceTypeEnum = Field(
        default=PerformanceTypeEnum.BOTH,
        description="Type of performance ('musical', 'theatrical', or '*').",
    )


# Union of all possible tool argument schemas
ToolArgsUnion = Union[
    OutagesArgs,
    MovieScreeningsArgs,
    HospitalShiftsArgs,
    ThessalonikiHistoryArgs,
    MusicAndTheaterPerformancesArgs,
]

# --- Agent Response Schemas ---


class ResponseSchema(BaseModel):
    """Schema for the response determining tool usage or direct reply."""

    reasoning: str = Field(
        ...,
        description="The reasoning process for the decision, explaining why tools were chosen, why clarification is needed, or why a direct response is given.",
    )
    direct_response: Optional[str] = Field(
        default=None,
        description="A direct text response to the user, used for greetings, thanks, clarifications, or off-topic refusals. **This response must be in the same language as the user's original query.** If this is populated, 'tools' should be empty.",
    )
    tools: List[ToolArgsUnion] = Field(
        default=[],
        description="List of tools to be called with their specific arguments. Should be empty if 'direct_response' is populated.",
    )


class FinalResponseSchema(BaseModel):
    """Schema for the final synthesized response to the user."""

    reasoning: str = Field(
        ...,
        description="Brief explanation of how the final response was constructed based on the tool results or why no information was found.",
    )
    response_to_user: str = Field(
        ...,
        description="The final, user-facing response, synthesized from the gathered information or indicating lack of information. **Must be in the same language as the user's original query.**",
    )
