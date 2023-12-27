from typing import List, Type
import pytest
from ez_rest.modules.role.models import RoleModel
from ez_rest.modules.base_user.repository import BaseUserRepository
from ez_rest.modules.base_user.models import BaseUserModel
from ez_rest.modules.db.services import DbServices
from ez_rest.modules.password.services import PaswordServices
from sqlalchemy import BigInteger
from sqlalchemy import Table, Column, MetaData, Integer,Text, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from tests.modules.users.repository import UserRepository
from tests.modules.users.models import UserModel

class MockPasswordServices():
    def hash_password(self, plain_password:str):
        return plain_password[::-1]
    
    def verify_password(self, plain_pass:str, hashed_pass:str):
        return  plain_pass[::-1] == hashed_pass


# TODO: mock functions
@pytest.fixture
def repository():
    return UserRepository(password_services=MockPasswordServices())

def test_create(repository):
    user = UserModel(
        id=1,
        username="user",
        password="123456",
        email="user@user.com",
        phone="000000"
    )
    repository.create(user)
    user_results = repository.read()
    assert user_results[0].password == "654321"

