from sqlmodel import JSON, Field, Column, Relationship
from typing import List, Optional, TypeVar, Generic
from ..base_crud.models import BaseModel


class Role(BaseModel, table=True):
    name:str
    is_admin:bool = False
    scopes:List[str] = Field(sa_column=Column(JSON))

    # Needed for Column(JSON)
    class Config:
        arbitrary_types_allowed = True