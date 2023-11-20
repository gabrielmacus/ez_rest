import pytest
from ez_rest.modules.role.models import Role
from ez_rest.modules.role.repository import RoleRepository
from sqlmodel import SQLModel
from datetime import datetime
from tests.mock_db_services import MockDbServices
from sqlmodel import SQLModel


@pytest.fixture
def repository():
    db_services = MockDbServices()
    engine = db_services.get_engine()

    SQLModel.metadata.create_all(engine)

    return RoleRepository(db_services)

def test_scopes_field_role(repository):
    """Testing JSON type field"""
    item = Role(
        id=1,
        name="Sales Manager",
        scopes=["product:read","product:create"]
    )
    item = repository.create(item)
    items = repository.read()

    assert items[0].scopes == ["product:read","product:create"]