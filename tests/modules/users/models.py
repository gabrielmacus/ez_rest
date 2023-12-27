from ez_rest.modules.base_user.models import BaseUserModel
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String

class UserModel(BaseUserModel):
    username:Mapped[str] = mapped_column(String(100))
    phone:Mapped[str] = mapped_column(String(100))
    email:Mapped[str] = mapped_column(String(100))


