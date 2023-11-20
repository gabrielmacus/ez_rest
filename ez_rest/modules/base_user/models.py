from ..base_crud.models import BaseModel
from ..role.models import Role
from pydantic import BaseModel as PydanticModel
from typing import List, Optional, TypeVar, Generic
from sqlmodel import Field, Relationship, SQLModel, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import BigInteger

class BaseUser(BaseModel, table=False):
    __abstract__ = True

    role_id:int = Field(sa_column=Column(BigInteger(), ForeignKey("role.id")))
    role:Role = Relationship(sa_relationship=relationship("Role", lazy="joined")) #generic_relationship(TRole, role_id)

    password:str
    
    
class TokenResponse(PydanticModel):
    access_token:str
    refresh_token:str