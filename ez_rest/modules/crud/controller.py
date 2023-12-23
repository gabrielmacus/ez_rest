from .repository import BaseRepository
from ..pagination.services import PaginationServices
from ..pagination.models import PaginationDTO
from .models import BaseModel, BaseDTO
from typing import TypeVar,Generic,List, Type
from ..mapper.services import mapper_services as mapper, MapperServices
from abc import ABC, abstractmethod
from fastapi import HTTPException, status
from ..query.services import QueryServices
from ..query.models import Query


query_services = QueryServices()

class BaseController[TModel: BaseModel](ABC):
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

    def create[TDtoIn :BaseDTO, 
               TDtoOut:BaseDTO](self, 
               item:TDtoIn, 
               type_in:Type[TModel], 
               type_out:Type[TDtoOut]):
        new_item = self._mapper_services.map(item, type_in)
        created_item = self._repository.create(new_item)
        return  self._mapper_services.map(created_item, type_out)
    
    def read[TDtoOut:BaseDTO](
            self,
            type_out:Type[TDtoOut],
            query:Query
    ) -> PaginationDTO[TDtoOut]:
        
        count = self._repository.count(query.filter)
        offset = self._pagination_services.get_offset(query.page, query.limit)
        items = self._repository.read(
            query.filter,
            query.limit,
            offset,
            query.order_by,
            query.fields)
        pages_count = self._pagination_services.get_pages_count(
            count, 
            query.limit)
        
        items = [self._mapper_services.map(item, type_out) for item in items]

        return PaginationDTO(
            count=count,
            page=query.page, 
            pages_count=pages_count, 
            items=items
        )

    def read_by_id[TDtoOut:BaseDTO](self,
                id:int, 
                type_out:Type[TDtoOut]) -> TDtoOut:
        item = self._repository.readById(id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        
        return self._mapper_services.map(item, type_out)

    def update_by_id[TDtoIn:BaseDTO]( self, 
                    id:int,
                    partial_item:dict,
                    type_in:Type[TDtoIn],
                    type_out:Type[TModel]):
        
        item = self._repository.readById(id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        
        partial_data = self._mapper_services.map_dict(
            partial_item, #type_in(**partial_item.model_dump(exclude_unset=True)),
            type_out,
            type_in
        )
        
        self._repository.updateById(partial_data, id)

    def delete_by_id(self, id:int):
        self._repository.deleteById(id)
        
