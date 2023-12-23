
from typing import Annotated, Type
from ez_rest.modules.crud.controller import BaseController
from ez_rest.modules.pagination.services import PaginationServices
from .models import Product, ProductSaveDTO
from .repository import ProductsRepository

class ProductsController(BaseController[Product]):
    def __init__(self,
                 repository:ProductsRepository,
                 pagination_services: PaginationServices = None) -> None:
        super().__init__(repository,
                         pagination_services,
                         )
    def create(self, 
               item: TDtoIn, 
               type_in: type[Product], 
               type_out: type[TDtoOut]):
        return super().create(item, type_in, type_out)
    
    def read(self,
        query: Annotated[Query, Depends(query_services.handle_query)]):
        return super().read(ProductPartialDTO2, query)
    
    def read_by_id(self, id: int) :
        return super().read_by_id(id, ProductPartialDTO2)

    def update_by_id(self, 
                     id: int, 
                     partial_data: ProductPartialDTO2):
        return super().update_by_id(id, 
                                    partial_data, 
                                    ProductPartialDTO2, 
                                    Product2)