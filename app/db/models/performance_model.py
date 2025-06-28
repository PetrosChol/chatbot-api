import datetime
from typing import Optional

from sqlalchemy import Column, Date, String, Time
from sqlmodel import Field, SQLModel


class Performance(SQLModel, table=True):
    __tablename__ = "performances"

    id: Optional[int] = Field(default=None, primary_key=True)
    performance_date: Optional[datetime.date] = Field(
        default=None, sa_column=Column(Date)
    ) 
    performance_name: Optional[str] = Field(
        default=None, sa_column=Column(String)
    ) 
    normalized_performance_name: Optional[str] = Field(
        default=None, sa_column=Column(String)
    ) 
    performance_location: Optional[str] = Field(
        default=None, sa_column=Column(String)
    ) 
    normalized_performance_location: Optional[str] = Field(
        default=None, sa_column=Column(String)
    ) 
    performance_type: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    performance_start_time: Optional[datetime.time] = Field(
        default=None, sa_column=Column(Time)
    )
