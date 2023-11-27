from typing import Generic, TypeVar, Type, List
from ez_rest.modules.db.services import DbServices
from ..crud.repository import BaseRepository
from .models import RoleModel

class RoleRepository(BaseRepository[RoleModel]):
    def __init__(self,
                 db_services: DbServices = None) -> None:
        super().__init__(RoleModel, db_services)