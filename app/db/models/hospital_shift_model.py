import datetime
from typing import Optional

from sqlalchemy import Column, Date, String
from sqlmodel import Field, SQLModel


class HospitalShift(SQLModel, table=True):
    __tablename__ = "hospital_shifts"

    id: Optional[int] = Field(default=None, primary_key=True)
    hospital_shift_date: Optional[datetime.date] = Field(
        default=None, sa_column=Column(Date)
    )
    hospital_name: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    normalized_hospital_name: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    specialties: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    hospital_shift_start_time: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    hospital_shift_end_time: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    address: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    phone_number: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
