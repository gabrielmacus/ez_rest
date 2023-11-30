from .repository import BaseRepository
from ..pagination.services import PaginationServices
from ..pagination.models import PaginationDTO
from .models import BaseModel, BaseDTO
from typing import TypeVar,Generic,List, Type
from ez_rest.modules.mapper.services import mapper_services as mapper, MapperServices
from abc import ABC, abstractmethod
from fastapi import HTTPException

TModel = TypeVar("TModel", bound=BaseModel)
TDtoIn = TypeVar("TDtoIn", bound=BaseDTO)
TDtoOut = TypeVar("TDtoOut", bound=BaseDTO)

class BaseController(ABC, Generic[TModel]):
    _repository:BaseRepository[TModel]
    _pagination_services:PaginationServices
    _mapper_services:MapperServices

    def __init__(
            self, 
            repository:BaseRepository,
            pagination_services:PaginationServices = None,
            mapper_services:MapperServices = None
        ) -> None:
        self._repository = repository
        self._pagination_services = PaginationServices() if pagination_services is None else pagination_services
        self._mapper_services = mapper if mapper_services is None else mapper_services

    def create(self, 
               item:TDtoIn, 
               type_in:Type[TModel], 
               type_out:Type[TDtoOut]):
        new_item = self._mapper_services.map(item, type_in)
        created_item = self._repository.create(new_item)
        return  self._mapper_services.map(created_item, type_out)
    
    def read(
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
        
        items = [self._mapper_services.map(item, type_out) for item in items]

        return PaginationDTO(
            count=count,
            page=page, 
            pages_count=pages_count, 
            items=items
        )

    def read_by_id(self,
                id:int, 
                type_out:Type[TDtoOut]) -> TDtoOut:
        item = self._repository.readById(id)
        if item is None:
            raise HTTPException(404)
        
        return self._mapper_services.map(item, type_out)

    def update_by_id( self, 
                    id:int,
                    partial_item:TDtoIn,
                    type_in:Type[TDtoIn],
                    type_out:Type[TModel]):
        
        item = self._repository.readById(id)
        if item is None:
            raise HTTPException(404)
        
        partial_data = self._mapper_services.map_dict(
            type_in(**partial_item.dict(exclude_unset=True)),
            type_out
        )
        
        self._repository.updateById(partial_data, id)
        
        
