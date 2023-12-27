
from typing import Annotated, Type
from ez_rest.modules.crud.controller import BaseController
from ez_rest.modules.pagination.models import PaginationDTO
from ez_rest.modules.pagination.services import PaginationServices
from ez_rest.modules.query.services import QueryServices
from ez_rest.modules.query.models import Query
from tests.modules.products.models import Product, ProductSaveDTO, ProductReadDTO
from tests.modules.products.repository import ProductsRepository
import tests.modules.products.mappings
from tests.modules.tables import create_tables
from fastapi import Depends

query_services = QueryServices()
class ProductsController(BaseController[Product]):
    def __init__(self,
                 pagination_services: PaginationServices = None) -> None:
        super().__init__(ProductsRepository(),
                         pagination_services,
                         )
    def create(self, 
               item: ProductSaveDTO):
        return super().create(item, 
                              Product,
                              ProductReadDTO)
    
    def read(self, 
             query: Annotated[Query, Depends(query_services.handle_query)]) -> PaginationDTO[ProductReadDTO]:
        return super().read(ProductReadDTO, query)
    
    def read_by_id(self, id: int) :
        return super().read_by_id(id, ProductReadDTO)

    def update_by_id(self, 
                     id: int, 
                     partial_item: dict) -> ProductReadDTO:
        return super().update_by_id(id, 
                                    partial_item, 
                                    Product,
                                    ProductSaveDTO, 
                                    ProductReadDTO)
