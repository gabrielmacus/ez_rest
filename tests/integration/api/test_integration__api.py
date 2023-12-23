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

from pydantic import BaseModel as PydanticModel

query_services = QueryServices()


mapper_services.register(
    ProductPartialDTO2,
    Product2,
    lambda src : {
        "id":src["id"],
        "name":src["name"],
        "category":src["category"],
        "price":src["price"]
    }
) 

mapper_services.register(
    ProductSaveDTO2,
    Product2,
    lambda src : {
        "id":src["id"],
        "name":src["name"],
        "category":src["category"],
        "price":src["price"]
    }
) 

def map_partial(src):
    data = src.__dict__
    new_data =  {
        
    }
    if 'id' in data:
        new_data['id'] = src["id"]
    if 'price' in data:
        new_data['price'] = src["price"]
    if 'name' in data:
        new_data['name'] = src["name"]
    if 'category' in data:
        new_data['category'] = src["category"]
    return new_data

mapper_services.register(
    Product2,
    ProductPartialDTO2,
    map_partial
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
                    response_model=PaginationDTO[ProductPartialDTO2])
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
                        [
                            (100, 10, 1, 10),
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

@pytest.mark.parametrize("filter, order_by, expected_ids",
                        [
                        ("name eq 'Apple'",'name asc', [1]),
                        ("name eq 'Tomato'",'id asc', [3]),
                        ("name eq 'Durian'",'', []),
                        ("category eq 'Vegetables'",'category asc, name desc',[3,4,2,1]),
                        ("(price ge 150 and (category eq 'Fruits' or category eq 'Dairy')) or (price ge 50 and category eq 'Vegetables')",'',[1,4,5]),
                        ("DIV(price,10) le 3",'price desc',[3,2]),
                        ("SUB(DIV(price,10),1) lt 2",'',[2]),
                        ("price gt 49.5",'price asc',[4,1,5]),
                        ("price gt MUL(50,2)",'',[5])
                        ])
def test_api_read__filter_order(client, filter, order_by, expected_ids):
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
    response = client.get(f'/products?limit=20&page=1&filter={filter}&order_by={order_by}')

    data = response.json()
    assert [i["id"] for i in data["items"]] == expected_ids


@pytest.mark.parametrize("fields",
[
    ("category,name"),
    ("category"),
    ("price"),
    ("name,price")
 ])
def test_api_read__fields(client, fields):

    client.post('/products', json={
            "name":f"Apple",
            "category":"Vegetables",
            "price": "100"
    })

    response = client.get(f'/products?page=1&limit=20&fields={fields}')
    data = response.json()['items'][0]
    
    if 'category' in fields:
        assert data['category'] is not None
    else:
        assert data['category'] is None
    
    if 'name' in fields:
        assert data['name'] is not None
    else:
        assert data['name'] is None
    
    if 'price' in fields:
        assert data['price'] is not None
    else:
        assert data['price'] is None