from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel,Column
from sqlalchemy import BigInteger

class BaseModel(SQLModel, table=False):
    __abstract__ = True
    
    id:Optional[int] = Field(sa_column=Column(BigInteger(), default=None, primary_key=True))
    deleted_at:Optional[datetime] = None
    created_at:Optional[datetime] = Field(default_factory=datetime.utcnow,nullable=False)
    updated_at:Optional[datetime] = None