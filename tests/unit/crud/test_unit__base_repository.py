from typing import Type
import pytest
from ez_rest.modules.crud.models import BaseModel
from ez_rest.modules.crud.repository import BaseRepository
from datetime import datetime, UTC
from ez_rest.modules.db.services import DbServices
from tests.mock_db_services import MockDbServices
from sqlalchemy import Table, Column, MetaData, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

meta = MetaData()
commodities = Table(
    'commodities',
    meta,
    Column('created_at',DateTime),
    Column('updated_at',DateTime),
    Column('deleted_at',DateTime),
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('category',String)
)

class Commodity(BaseModel):
     __tablename__ = "commodities"
     name:Mapped[str] = mapped_column(String(100))
     category:Mapped[str] = mapped_column(String(100))

class CommoditiesRepository(BaseRepository):
    def __init__(self, db_services: DbServices = None) -> None:
        super().__init__(Commodity, db_services)

@pytest.fixture
def repository():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    meta.create_all(engine)

    return BaseRepository(Commodity, db_services)

def test_create(repository):
    item = Commodity(id=1,name="Demo",category="Food")
    item = repository.create(item)

    assert item.id == 1

@pytest.mark.parametrize("name, category, include_deleted", 
                         [("Demo","Food",True),
                          ("Demo","Food",False)])
def test_read(repository, name, category, include_deleted):
    item = Commodity(
        id=1,
        name=name,
        category=category,
        deleted_at=None if include_deleted is False else datetime.now(UTC)
    )
    item = repository.create(item)
    items = repository.read(include_deleted=include_deleted)
    
    assert len(items) == 1 and items[0].id == 1

def test_read__filter(repository):
    item = Commodity(id=1,name="Demo",category="Food")
    item = repository.create(item)
    items = repository.read([Commodity.category == 'Food', Commodity.name == "Demo"])

    assert len(items) == 1 and items[0].id == 1

def test_read__filter_not_found(repository):
    item = Commodity(id=1,name="Demo",category="Food")
    item = repository.create(item)
    items = repository.read([Commodity.category == 'Sports', Commodity.name == 'Demo'])

    assert len(items) == 0

def test_update(repository):
    item = Commodity(id=1,name="Demo",category="Food")
    item = repository.create(item)

    item = Commodity(name="Vegetable", category='Food 2')
    repository.updateById(item, 1)
    items = repository.read([Commodity.category == 'Food 2'])

    assert len(items) == 1 and \
            items[0].id == 1 and \
            items[0].category == 'Food 2' and \
            items[0].name == "Vegetable"

def test_update__not_found(repository):
    item = Commodity(name="Vegetable", category='Food 2')
    with pytest.raises(Exception):
        repository.updateById(item, 2)

@pytest.mark.parametrize("soft_delete", 
                         [(True),
                          (False)])
def test_delete(repository, soft_delete):
    item = Commodity(id=1,name="Demo",category="Food")
    item = repository.create(item)

    repository.deleteById(1, soft_delete=soft_delete)
    results = repository.read([], include_deleted=not soft_delete)
    assert len([item for item in results if item.id != 1]) == 0

def test_delete__not_found(repository):
    with pytest.raises(Exception):
        repository.deleteById(2)

@pytest.mark.parametrize("items_generated,include_deleted", 
                         [(10,True),
                          (20, False)])
def test_count(repository, items_generated,include_deleted):
    for i in range(1,items_generated+1):
        item = Commodity(
            id=i,
            name="Demo",
            category="Food", 
            deleted_at=None if include_deleted is False else  datetime.now(UTC))
        item = repository.create(item)

    assert repository.count(include_deleted=include_deleted) == items_generated
