import datetime
from typing import Optional

from sqlalchemy import Column, Date, String, Time
from sqlmodel import Field, SQLModel


class Outage(SQLModel, table=True):
    __tablename__ = "outages"

    id: Optional[int] = Field(default=None, primary_key=True)
    outage_date: Optional[datetime.date] = Field(
        default=None, sa_column=Column(Date)
    )
    outage_type: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )  
    outage_location: Optional[str] = Field(
        default=None, sa_column=Column(String)
    ) 
    normalized_outage_location: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )  
    outage_affected_areas: Optional[str] = Field(default=None, sa_column=Column(String))
    normalized_outage_affected_areas: Optional[str] = Field(
        default=None, sa_column=Column(String)
    ) 
    outage_start: Optional[datetime.time] = Field(
        default=None, sa_column=Column(Time)
    ) 
    outage_end: Optional[datetime.time] = Field(
        default=None, sa_column=Column(Time)
    ) 
