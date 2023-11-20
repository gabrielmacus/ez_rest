from .repository import BaseRepository
from ..pagination.services import PaginationServices
from ..pagination.models import PaginationResult
from .models import BaseModel
from typing import TypeVar,Generic,List

T = TypeVar("T", bound=BaseModel)

class BaseController(Generic[T]):
    _repository:BaseRepository
    _pagination_services:PaginationServices

    def __init__(
            self, 
            repository:BaseRepository,
            pagination_services:PaginationServices = None
        ) -> None:
        self._repository = repository
        self._pagination_services = PaginationServices() if pagination_services == None else pagination_services

    def create(self, item:T):
        return self._repository.create(item)
    
    def read(
            self,
            query:List = [],
            page:int = 1, 
            limit:int = None,
    ) -> PaginationResult[T]:
        
        count = self._repository.count(query)
        offset = self._pagination_services.get_offset(page, limit)
        items = self._repository.read(
            query,
            limit,
            offset)
        pages_count = self._pagination_services.get_pages_count(
            count, 
            limit)

        return PaginationResult(
            count=count,
            page=page, 
            pages_count=pages_count, 
            items=items
        )