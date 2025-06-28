import datetime
from typing import List, Optional

from sqlalchemy import Column, Date, String, Time, Integer
from sqlmodel import Field, Relationship, SQLModel


# Forward references for relationships
class Hall(SQLModel, table=True):
    __tablename__ = "halls"

    id: Optional[int] = Field(default=None, primary_key=True)
    hall_name: str = Field(index=True)
    cinema_id: Optional[int] = Field(default=None, foreign_key="cinemas.id")

    cinema: "Cinema" = Relationship(back_populates="halls")
    screenings: List["Screening"] = Relationship(back_populates="hall")


class Movie(SQLModel, table=True):
    __tablename__ = "movies"

    id: Optional[int] = Field(default=None, primary_key=True)
    movie_name: str = Field(
        index=True, unique=True
    )
    normalized_movie_name: Optional[str] = Field(
        default=None, sa_column=Column(String, index=True)
    )
    movie_name_greek: Optional[str] = Field(default=None, sa_column=Column(String))
    normalized_movie_name_greek: Optional[str] = Field(
        default=None, sa_column=Column(String, index=True)
    )
    movie_name_english: Optional[str] = Field(default=None, sa_column=Column(String))
    normalized_movie_name_english: Optional[str] = Field(
        default=None, sa_column=Column(String, index=True)
    )
    genre: Optional[str] = Field(default=None, sa_column=Column(String))
    normalized_genre: Optional[str] = Field(
        default=None, sa_column=Column(String, index=True)
    )  
    year: Optional[int] = Field(default=None, sa_column=Column(Integer))

    screenings: List["Screening"] = Relationship(back_populates="movie")


class Screening(SQLModel, table=True):
    __tablename__ = "screenings"

    id: Optional[int] = Field(default=None, primary_key=True)
    screening_date: datetime.date = Field(sa_column=Column(Date))
    screening_time: datetime.time = Field(sa_column=Column(Time))
    movie_id: Optional[int] = Field(default=None, foreign_key="movies.id")
    hall_id: Optional[int] = Field(default=None, foreign_key="halls.id")

    movie: Optional[Movie] = Relationship(back_populates="screenings")
    hall: Optional[Hall] = Relationship(back_populates="screenings")


class Cinema(SQLModel, table=True):
    __tablename__ = "cinemas"

    id: Optional[int] = Field(default=None, primary_key=True)
    cinema_name: str = Field(unique=True, index=True)

    halls: List[Hall] = Relationship(back_populates="cinema")
