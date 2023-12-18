from fastapi.testclient import TestClient
from fastapi import FastAPI
from tests.mock_db_services import MockDbServices
from sqlalchemy import Table, Column, MetaData, Integer,Text, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ez_rest.modules.crud.models import BaseModel, BaseDTO
from typing import List, Optional, Type
from ez_rest.modules.mapper.services import mapper_services

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
    name:Optional[str] = None
    category:Optional[str] = None

class ProductReadDTO(BaseDTO):
    name:str
    category:str


mapper_services.register(
    ProductReadDTO,
    Product,
    lambda src : {
        "id":src.id,
        "name":src.name,
        "category":src.category
    }
) 

mapper_services.register(
    ProductSaveDTO,
    Product,
    lambda src : {
        "id":src.id,
        "name":src.name,
        "category":src.category
    }
) 



def test_api_create():
    pass