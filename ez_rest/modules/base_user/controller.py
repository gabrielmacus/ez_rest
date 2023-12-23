from .repository import BaseUserRepository
from .services import BaseUserServices
from ez_rest.modules.pagination.services import PaginationServices
from ..crud.controller import BaseController
from fastapi import APIRouter, Depends, HTTPException, status, Security
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from .models import BaseUserModel
from abc import ABC


class BaseUserController[T: BaseUserModel](BaseController[T], ABC):
    _services:BaseUserServices

    def __init__(self, 
                 repository: BaseUserRepository[T], 
                 services:BaseUserServices = None,
                 pagination_services: PaginationServices = None) -> None:
        self._services = services
        super().__init__(repository, pagination_services)

    def get_tokens(self, data:Annotated[OAuth2PasswordRequestForm, Depends()]):
        return self._services.handle_token_generation(
            data.username, 
            data.password)