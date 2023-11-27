from .repository import BaseRepository
from ..pagination.services import PaginationServices
from ..pagination.models import PaginationDTO
from .models import BaseModel, BaseDTO
from typing import TypeVar,Generic,List, Type
from ez_rest.modules.mapper.services import mapper_services
from abc import ABC, abstractmethod

TRepository = TypeVar("TRepository", bound=BaseRepository)
TDtoIn = TypeVar("TDtoIn", bound=BaseDTO)
TDtoOut = TypeVar("TDtoOut", bound=BaseDTO)

class BaseController(ABC, Generic[TRepository]):
    _repository:TRepository
    _pagination_services:PaginationServices

    def __init__(
            self, 
            repository:BaseRepository,
            pagination_services:PaginationServices = None
        ) -> None:
        self._repository = repository
        self._pagination_services = PaginationServices() if pagination_services == None else pagination_services

    @abstractmethod
    def create[TDtoIn, TDtoOut](self, 
               item:TDtoIn, 
               type_in:Type[BaseModel], 
               type_out:Type[TDtoOut]):
        item = mapper_services.map(item, type_in)
        created_item = self._repository.create(item)
        return  mapper_services.map(created_item, type_out)
    
    @abstractmethod
    def read[TDtoOut](
            self,
            type_out:Type[TDtoOut],
            query:List = [],
            page:int = 1, 
            limit:int = None,
    ) -> PaginationDTO[TDtoOut]:
        
        count = self._repository.count(query)
        offset = self._pagination_services.get_offset(page, limit)
        items = self._repository.read(
            query,
            limit,
            offset)
        pages_count = self._pagination_services.get_pages_count(
            count, 
            limit)
        
        items = [mapper_services.map(item, type_out) for item in items]

        return PaginationDTO(
            count=count,
            page=page, 
            pages_count=pages_count, 
            items=items
        )