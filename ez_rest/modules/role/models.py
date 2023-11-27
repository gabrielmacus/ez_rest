from typing import List
from ..crud.models import BaseModel, BaseDTO
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import JSON, String, Boolean


class RoleModel(BaseModel):
    __tablename__ = "roles"
    name:Mapped[str] = mapped_column(String(100), unique=True)
    is_admin:Mapped[bool] = mapped_column(Boolean(), default = False)
    scopes:Mapped[List[str]] = mapped_column(JSON(), default = [])

class RoleDTO(BaseDTO):
    name:str
    is_admin:bool
    scopes:List[str]