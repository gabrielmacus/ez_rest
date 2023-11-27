from ez_rest.modules.crud.models import BaseModel
from ez_rest.modules.crud.repository import BaseRepository
from ez_rest.modules.pagination.models import PaginationDTO
from ez_rest.modules.pagination.services import PaginationServices
from ..crud.controller import BaseController
from .repository import RoleRepository
from .models import RoleDTO, RoleModel
from typing import Generic, TypeVar, Type, List

class RoleController(BaseController[RoleRepository]):
    def create(self, 
               item: RoleDTO):
        return super().create(item, RoleModel, RoleDTO)
    