from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel as PydanticModel

class BaseModel(DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    created_at:Mapped[datetime] = mapped_column(DateTime(), default=datetime.now(UTC))
    deleted_at:Mapped[Optional[datetime]]
    updated_at:Mapped[Optional[datetime]]
    def to_dict(self):
        return {field.name:getattr(self, field.name) for field in self.__table__.c}

class BaseDTO(PydanticModel):
    id:int
    created_at:Optional[datetime]
    deleted_at:Optional[datetime]
    updated_at:Optional[datetime]