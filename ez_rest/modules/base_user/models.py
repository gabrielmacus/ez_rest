from ..crud.models import BaseModel, BaseDTO
from ..role.models import RoleModel, RoleDTO
from pydantic import BaseModel as PydanticModel
from sqlalchemy import BigInteger,ForeignKey,String
from sqlalchemy.orm import Mapped, mapped_column, relationship

class BaseUserModel(BaseModel):
    __tablename__ = "users"
    role_id: Mapped[int] = mapped_column(BigInteger(), ForeignKey(RoleModel.id))
    role:Mapped[RoleModel] = relationship(lazy="joined")
    password:Mapped[str] = mapped_column(String(200))

class BaseUserDTO(BaseDTO):
    role_id:int
    role:RoleDTO

class TokenResponse(PydanticModel):
    access_token:str
    refresh_token:str

class TokenConfig(PydanticModel):
    expire_minutes:int
    secret:str
    algorithm:str