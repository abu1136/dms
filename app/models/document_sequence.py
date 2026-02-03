from datetime import date
from sqlalchemy import Date, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DocumentSequence(Base):
    __tablename__ = "document_sequences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sequence_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    last_number: Mapped[int] = mapped_column(Integer, default=0)
