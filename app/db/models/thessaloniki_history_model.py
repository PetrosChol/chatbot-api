from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class ThessalonikiHistory(SQLModel, table=True):
    __tablename__ = "thessaloniki_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    text: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    questions: Optional[str] = Field(
        default=None, sa_column=Column(String)
    )
    text_embedding: List[float] = Field(
        sa_column=Column(Vector(1536))
    ) 
    questions_embedding: List[float] = Field(
        sa_column=Column(Vector(1536))
    )
