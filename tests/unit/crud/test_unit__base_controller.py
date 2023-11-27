from typing import List, Optional
from ez_rest.modules.crud.repository import BaseRepository
from ez_rest.modules.crud.models import BaseModel, BaseDTO
from ez_rest.modules.crud.controller import BaseController
from ez_rest.modules.mapper.services import mapper_services
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped
import pytest
from ez_rest.modules.pagination.services import PaginationServices
from automapper import mapper
from datetime import datetime, UTC


class Product(BaseModel):
     __tablename__ = "products"
     name:Mapped[str] = mapped_column(String(100))
     category:Mapped[str] = mapped_column(String(100))

class ProductSaveDTO(BaseDTO):
    id:Optional[int]
    product_name:str
    product_category:str

class ProductReadDTO(BaseDTO):
    name_category:str

mapper_services.register(
    ProductSaveDTO,
    Product,
    lambda src : Product(
        id=src.id,
        name=src.product_name,
        category=src.product_category
    )
)

mapper_services.register(
    Product,
    ProductReadDTO,
    lambda src : ProductReadDTO(
        id=src.id,
        name_category=f'{src.name} {src.category}'
    )
)


class ProductsRepository(BaseRepository[Product]):
    items = [
        Product(id=1,created_at=datetime.now(UTC),name="Vegetable",category="Food"),
        Product(id=2,created_at=datetime.now(UTC),name="Chocolate",category="Food"),
        Product(id=3,created_at=datetime.now(UTC),name="Meat",category="Food"),
        Product(id=4,created_at=datetime.now(UTC),name="Donuts",category="Food"),
        Product(id=5,created_at=datetime.now(UTC),name="Honey",category="Food")
    ]
    
    def __init__(self) -> None:
        pass
    
    def read(self, 
             query=None, 
             limit: int = None, 
             offset: int = None, 
             include_deleted: bool = False) -> List:
        

        if offset != None:
            items = self.items[offset:limit + offset]
        else:
            items = self.items[:limit]

        return items
    
    def create(self, item: any) -> any:
        item.id = len(self.items) + 1
        self.items.append(item)
        return item

    def count(self, query=None, include_deleted: bool = False) -> int:
        return len(self.items)

class ProductsController(BaseController[Product]):
    def __init__(self,
                 pagination_services: PaginationServices = None) -> None:
        super().__init__(ProductsRepository(), pagination_services)
    def create(self, 
               item: ProductSaveDTO):
        return super().create(item, Product, ProductReadDTO)
    
    def read(self, 
             query: List = [], 
             page: int = 1, 
             limit: int = None):
        return super().read(ProductReadDTO, query, page, limit)

@pytest.mark.parametrize("limit,page,expected_pages,expected_items", 
                         [(3,1,2,3),
                          (3,2,2,2)])
def test_read(limit, page, expected_pages, expected_items):
    controller = ProductsController()
    result = controller.read(limit=limit, page=page)

    assert len(result.items) == expected_items and\
        result.count == 5 and \
        result.page == page and \
        result.pages_count == expected_pages

def test_create():
    controller = ProductsController()
    item = controller.create(ProductSaveDTO(
        product_category="Furniture",
        product_name="Oven"
    ))
    result = controller.read(limit = 20, page = 1)
    assert item.id == 6 and len([i for i in result.items if i.id == 6]) == 1