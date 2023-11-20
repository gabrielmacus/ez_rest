from typing import Generic, TypeVar, Type, List
from ez_rest.modules.db.services import DbServices
from ..base_crud.repository import BaseRepository
from .models import Role

class RoleRepository(BaseRepository[Role]):
    def __init__(self,
                 db_services: DbServices = None) -> None:
        super().__init__(Role, db_services)