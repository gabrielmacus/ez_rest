import pytest
from ez_rest.modules.role.models import RoleModel
from ez_rest.modules.role.repository import RoleRepository
from datetime import datetime
from sqlalchemy import Table, Column, MetaData, Integer,Text, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from tests.modules.roles.repository import RoleRepository

@pytest.fixture
def repository():
    return RoleRepository()

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