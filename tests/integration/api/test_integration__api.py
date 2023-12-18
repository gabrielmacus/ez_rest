from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from tests.mock_db_services import MockDbServices
from sqlalchemy import Table, Column, MetaData,Integer,Text,Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ez_rest.modules.crud.models import BaseModel, BaseDTO
from typing import List, Optional, Type, Annotated
from ez_rest.modules.mapper.services import mapper_services
from ez_rest.modules.crud.repository import BaseRepository
from ez_rest.modules.crud.models import BaseModel
from ez_rest.modules.crud.controller import BaseController
from ez_rest.modules.query.models import Query
from ez_rest.modules.query.services import QueryServices
from ez_rest.modules.db.services import DbServices
from ez_rest.modules.pagination.services import PaginationServices
from ez_rest.modules.pagination.models import PaginationDTO
import pytest
import random

query_services = QueryServices()

meta = MetaData()
roles = Table(
    'products2',
    meta,
    Column('created_at',DateTime),
    Column('updated_at',DateTime),
    Column('deleted_at',DateTime),
    Column('id', Integer, primary_key=True),
    Column('name',String),
    Column('category',String),
    Column('price', Float)
)


class Product2(BaseModel):
     __tablename__ = "products2"
     price:Mapped[float] = mapped_column(Float)
     name:Mapped[str] = mapped_column(String(100))
     category:Mapped[str] = mapped_column(String(100))

class ProductSaveDTO2(BaseDTO):
    price:float
    name:str
    category:str

class ProductSavePartialDTO2(BaseDTO):
    price:Optional[float] = None
    name:Optional[str] = None
    category:Optional[str] = None

class ProductReadDTO2(BaseDTO):
    price:float
    name:str
    category:str


class ProductsRepository(BaseRepository[Product2]):
    def __init__(self, 
                 db_services: DbServices = None) -> None:
        super().__init__(Product2, db_services)

class ProductsController(BaseController[Product2]):
    def __init__(self,
                 repository:ProductsRepository,
                 pagination_services: PaginationServices = None) -> None:
        super().__init__(repository,
                         pagination_services,
                         )
    def create(self, 
               item: ProductSaveDTO2):
        return super().create(item, Product2, ProductReadDTO2)
    
    def read(self,
        query: Annotated[Query, Depends(query_services.handle_query)]):
        return super().read(ProductReadDTO2, query)
    
    def read_by_id(self, id: int) :
        return super().read_by_id(id, ProductReadDTO2)

    def update_by_id(self, 
                     id: int, 
                     partial_data: ProductSavePartialDTO2):
        return super().update_by_id(id, 
                                    partial_data, 
                                    ProductSavePartialDTO2, 
                                    Product2)

mapper_services.register(
    ProductReadDTO2,
    Product2,
    lambda src : {
        "id":src.id,
        "name":src.name,
        "category":src.category,
        "price":src.price
    }
) 

mapper_services.register(
    ProductSaveDTO2,
    Product2,
    lambda src : {
        "id":src.id,
        "name":src.name,
        "category":src.category,
        "price":src.price
    }
) 

mapper_services.register(
    Product2,
    ProductReadDTO2,
    lambda src : {
        "id":src.id,
        "name":src.name,
        "category":src.category,
        "price":src.price
    }
) 

@pytest.fixture
def client():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    meta.create_all(engine)

    products_controller = ProductsController(
        repository=ProductsRepository(db_services)
    )
    
    app = FastAPI()
    app.add_api_route('/products', 
                      products_controller.create,
                      methods=['POST'])
    app.add_api_route('/products', 
                    products_controller.read,
                    methods=['GET'],
                    response_model=PaginationDTO[ProductReadDTO2])
    return TestClient(app) 


def test_api_create(client):
    count = 100
    for i  in range(count):
        response = client.post('/products', json={
            "name":f"Apple {i}",
            "category":f"Food {i}",
            "price":1000
        })
        data = response.json()
        
        assert data["id"] == i + 1
        assert data["name"] == f"Apple {i}"
        assert data["category"] == f"Food {i}"

    response = client.get('/products?limit=1&page=1')
    data =  response.json()
    assert data["count"] == count

@pytest.mark.parametrize("count, limit, page, pages_count",
                         [(100, 10, 1, 10),
                          ])
def test_api_read(client, count, limit, page, pages_count):
    for i  in range(count):
        client.post('/products', json={
            "name":f"Ball {i}",
            "category":"Sports",
            "price": ((i+1) * 100)
        })

    response = client.get(f"/products?page={page}&limit={limit}&filter=")
    data = response.json()

    assert data["count"] == count
    assert data["page"] == page
    assert data["pages_count"] == pages_count
    assert len(data["items"]) == limit

@pytest.mark.parametrize("filter, expected_ids",
                        [
                        ("name eq 'Apple'", [1]),
                        ("name eq 'Tomato'", [3]),
                        ("name eq 'Durian'", []),
                        ("category eq 'Vegetables'",[1,2,3,4]),
                        ("(price ge 150 and (category eq 'Fruits' or category eq 'Dairy')) or (price ge 50 and category eq 'Vegetables')",[1,4,5]),
                        ("DIV(price,10) le 3",[2,3]),
                        ("SUB(DIV(price,10),1) lt 2",[2])
                        ])
def test_api_read__filter(client, filter, expected_ids):
    items = [
        {
            "name":f"Apple",
            "category":"Vegetables",
            "price": "100"
        },
        {
            "name":f"Carrot",
            "category":"Vegetables",
            "price": "20"
        },
        {
            "name":f"Tomato",
            "category":"Vegetables",
            "price": "30"
        },
        {
            "name":f"Potato",
            "category":"Vegetables",
            "price": "50"
        },
        {
            "name":f"Pineapple",
            "category":"Fruits",
            "price": "150"
        }
    ]
    for item in items:
        client.post('/products', json=item)
    response = client.get(f'/products?limit=20&page=1&filter={filter}')

    data = response.json()
    assert [i["id"] for i in data["items"]] == expected_ids