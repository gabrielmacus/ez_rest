from ez_rest.modules.base_crud.repository import BaseRepository
from ez_rest.modules.pagination.services import PaginationServices
from ..base_crud.controller import BaseController
from .repository import RoleRepository
from .models import Role
from typing import Generic, TypeVar, Type, List

class RoleController(BaseController[Role]):
    def __init__(self, 
                 repository: RoleRepository[Role], 
                 pagination_services: PaginationServices = None) -> None:
        super().__init__(repository, pagination_services)
