import pytest
from ez_rest.modules.role.models import RoleModel
from ez_rest.modules.role.repository import RoleRepository
from datetime import datetime
from tests.mock_db_services import MockDbServices
from sqlalchemy import Table, Column, MetaData, Integer,Text, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

meta = MetaData()
roles = Table(
    'roles',
    meta,
    Column('created_at',DateTime),
    Column('updated_at',DateTime),
    Column('deleted_at',DateTime),
    Column('id', Integer, primary_key=True),
    Column('name',String),
    Column('is_admin', Boolean),
    Column('scopes', Text)
)

@pytest.fixture
def repository():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    meta.create_all(engine)

    return RoleRepository(db_services)

def test_scopes_field_role(repository):
    """Testing JSON type field"""
    item = RoleModel(
        id=1,
        name="Sales Manager",
        scopes=["product:read","product:create"]
    )
    item = repository.create(item)
    items = repository.read()

    assert items[0].scopes == ["product:read","product:create"]