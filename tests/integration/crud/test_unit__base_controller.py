from typing import List, Optional, Type
from tests.mock_db_services import MockDbServices
from ez_rest.modules.crud.repository import BaseRepository
from ez_rest.modules.crud.models import BaseModel, BaseDTO
from ez_rest.modules.crud.controller import BaseController
from ez_rest.modules.db.services import DbServices
from ez_rest.modules.mapper.services import mapper_services
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped
import pytest
from ez_rest.modules.pagination.services import PaginationServices
from fastapi import HTTPException, status
from ez_rest.modules.query.services import QueryServices
from ez_rest.modules.query.models import Query

from sqlalchemy.orm import relationship
from sqlalchemy import BigInteger
from sqlalchemy import Table, Column, MetaData, Integer,Text, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from pydantic import ValidationError

from fastapi import Depends
from typing import Annotated

meta = MetaData()
roles = Table(
    'products',
    meta,
    Column('created_at',DateTime),
    Column('updated_at',DateTime),
    Column('deleted_at',DateTime),
    Column('id', Integer, primary_key=True),
    Column('name',String),
    Column('category',String),
)


class Product(BaseModel):
     __tablename__ = "products"
     name:Mapped[str] = mapped_column(String(100))
     category:Mapped[str] = mapped_column(String(100))

class ProductSaveDTO(BaseDTO):
    product_name:str
    product_category:str

class ProductSavePartialDTO(BaseDTO):
    product_name:Optional[str] = None
    product_category:Optional[str] = None

class ProductReadDTO(BaseDTO):
    name_category:str


mapper_services.register(
    ProductSaveDTO,
    Product,
    lambda src : {
        "id":src.id,
        "name":src.product_name,
        "category":src.product_category
    }
) 


def map_product_read_dto(src:ProductSavePartialDTO):
    data = {}
    partial_data = src.model_dump(exclude_unset=True)
    if "product_name" in partial_data:
        data["name"] = partial_data["product_name"]
    if "product_category" in partial_data:
        data["category"] = partial_data["product_category"]

    return data

mapper_services.register(
    ProductSavePartialDTO,
    Product,
    map_product_read_dto
)
   
mapper_services.register(
    Product,
    ProductReadDTO,
    lambda src : {
        "id":src.id,
        "name_category":f'{src.name} {src.category}' if src.category is not None else src.name
    }
)
query_services = QueryServices()

class ProductsRepository(BaseRepository[Product]):
    def __init__(self, 
                 db_services: DbServices = None) -> None:
        super().__init__(Product, db_services)

class ProductsController(BaseController[Product]):
    def __init__(self,
                 repository:ProductsRepository,
                 pagination_services: PaginationServices = None) -> None:
        super().__init__(repository,
                         pagination_services,
                         )
    def create(self, 
               item: ProductSaveDTO):
        return super().create(item, Product, ProductReadDTO)
    
    def read(self,
        query: Annotated[Query, Depends(query_services.handle_query)]):
        return super().read(ProductReadDTO, query)
    
    def read_by_id(self, id: int) :
        return super().read_by_id(id, ProductReadDTO)

    def update_by_id(self, 
                     id: int, 
                     partial_data: ProductSavePartialDTO):
        return super().update_by_id(id, 
                                    partial_data, 
                                    ProductSavePartialDTO, 
                                    Product)


@pytest.fixture
def controller():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    meta.create_all(engine)

    return ProductsController( repository=ProductsRepository(db_services=db_services))

@pytest.mark.parametrize("limit,page,expected_pages,expected_items", 
                         [(3,1,2,3),
                          (3,2,2,2)])
def test_controller_read(controller, limit, page, expected_pages, expected_items):
    for i in range(0,5):
        controller.create(ProductSaveDTO(
            product_category="Furniture",
            product_name=f"Oven {i}"
        ))
    result = controller.read(Query(
        filter=None,
        limit=limit,
        page=page
    ))

    assert len(result.items) == expected_items and\
        result.count == 5 and \
        result.page == page and \
        result.pages_count == expected_pages

def test_controller_create(controller):

    item = ProductSaveDTO(
            product_category="Furniture",
            product_name="Oven"
        )
    created_item = controller.create(item)
    
    assert created_item.id == 1


@pytest.mark.parametrize("id,found", 
                         [(1,True),
                          (2,True),
                          (6,False)])
def test_controller_read_by_id(controller,id, found):
    controller.create(ProductSaveDTO(
        product_category="Furniture",
        product_name=f"Oven"
    ))
    controller.create(ProductSaveDTO(
        product_category="Furniture",
        product_name=f"Fridge"
    ))

    if found: 
        item = controller.read_by_id(id)
        assert item.id == id
    else:
        with pytest.raises(HTTPException) as ex:
             item = controller.read_by_id(id)
        assert ex.value.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.parametrize("id,partial_data, expected_name_category", 
                         [(1,{"product_name":"Carrot"},"Carrot Food"),
                          (1,{"product_name":"Carrot","product_category":None},"Carrot"),
                          (1,{"product_name":"Ball","product_category":"Sports"},"Ball Sports"),
                          (2,{"product_name":"Ball"},None),
                          (3,{"product_name":"Ball","product_category":"Sports"},None)
                          ])
def test_controller_update_by_id(controller, id, partial_data, expected_name_category):
    controller.create(ProductSaveDTO(
        product_category="Food",
        product_name=f"Apple"
    ))
       

    if expected_name_category != None:
        controller.update_by_id(
            id,
            ProductSavePartialDTO(**partial_data)
        )
        updated_item = controller.read_by_id(id)
        assert updated_item.name_category == expected_name_category
    else:
        with pytest.raises(HTTPException) as ex:
            controller.update_by_id(
                id,
                ProductSavePartialDTO(**partial_data)
            )
    
        assert ex.value.status_code == status.HTTP_404_NOT_FOUND

def test_controller_delete_by_id(controller:ProductsController):
    controller.create(ProductSaveDTO(
        id = 1,
        product_category="Food",
        product_name=f"Apple"
    ))
    controller.create(ProductSaveDTO(
        id = 2,
        product_category="Food",
        product_name=f"Carrot"
    ))
    controller.create(ProductSaveDTO(
        id = 3,
        product_category="Food",
        product_name=f"Pineapple"
    ))
    
    controller.delete_by_id(2)
    result = controller.read(Query(
        filter=None,
        limit=20,
        page=1
    ))
    
    assert len(result.items) == 2
    assert [i.id for i in result.items] == [1,3]