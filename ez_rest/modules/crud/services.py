from fastapi import APIRouter
from typing import TypeVar, Generic
from .controller import BaseController


class CrudServices[TController:BaseController]():
    _controller:TController

    def __init__(self,
                 controller:TController) -> None:
        self._controller = controller

    def map_create_route(self, router:APIRouter):
        router.add_api_route('/', 
                             self._controller.create, 
                             methods=['POST'])
    
    def map_read_route(self, router:APIRouter):
        router.add_api_route('/',
                             self._controller.read)
    
