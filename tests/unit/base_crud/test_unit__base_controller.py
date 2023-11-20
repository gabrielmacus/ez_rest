from typing import List
import pytest
from ez_rest.modules.base_crud.models import BaseModel
from ez_rest.modules.base_crud.repository import BaseRepository
from ez_rest.modules.base_crud.controller import BaseController
from sqlmodel import SQLModel

class Product(BaseModel, table=False):
     name:str
     category:str


class ProductsRepository(BaseRepository):
    items = [
        Product(name="Vegetable",category="Food"),
        Product(name="Chocolate",category="Food"),
        Product(name="Meat",category="Food"),
        Product(name="Donuts",category="Food"),
        Product(name="Honey",category="Food")
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

@pytest.fixture
def controller():
    a = BaseModel()
    a.id
    repository = ProductsRepository()
    controller = BaseController(repository)

    return controller


@pytest.mark.parametrize("limit,page,expected_pages,expected_items", 
                         [(3,1,2,3),
                          (3,2,2,2)])
def test_read(controller, limit, page, expected_pages, expected_items):
    result = controller.read(limit=limit, page=page)

    assert len(result.items) == expected_items and\
        result.count == 5 and \
        result.page == page and \
        result.pages_count == expected_pages


    
def test_create(controller):
    item = controller.create(Product(
        category="Furniture",
        name="Oven"
    ))
    result = controller.read(limit = 20, page = 1)
    assert item.id == 6 and len([i for i in result.items if i.id == 6]) == 1