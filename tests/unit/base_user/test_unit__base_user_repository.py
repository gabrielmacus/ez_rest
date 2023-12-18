from typing import List, Type
import pytest
from ez_rest.modules.role.models import RoleModel
from ez_rest.modules.base_user.repository import BaseUserRepository
from ez_rest.modules.base_user.models import BaseUserModel
from ez_rest.modules.db.services import DbServices
from ez_rest.modules.password.services import PaswordServices
from tests.mock_db_services import MockDbServices
from sqlalchemy import BigInteger
from sqlalchemy import Table, Column, MetaData, Integer,Text, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

meta = MetaData()
users = Table(
    'users',
    meta,
    Column('created_at',DateTime),
    Column('updated_at',DateTime),
    Column('deleted_at',DateTime),
    Column('id', Integer, primary_key=True),
    Column('role_id',Integer, ForeignKey(RoleModel.id)),
    Column('password', String),
    Column('username',String,),    
    Column('email',String),
    Column('phone',String)
)
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

class MockPasswordServices():
    def hash_password(self, plain_password:str):
        return plain_password[::-1]
    
    def verify_password(self, plain_pass:str, hashed_pass:str):
        return  plain_pass[::-1] == hashed_pass



class UserModel(BaseUserModel):
    username:Mapped[str] = mapped_column(String(100),use_existing_column=True)
    email:Mapped[str] = mapped_column(String(100),use_existing_column=True)
    phone:Mapped[str] = mapped_column(String(100),use_existing_column=True)

class UserRepository(BaseUserRepository[UserModel]):
    #_identity_fields = ['username', 'email']

    def __init__(self, 
                 db_services: DbServices = None, 
                 password_services: PaswordServices = None) -> None:
        super().__init__(UserModel, db_services, password_services)

@pytest.fixture
def repository():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    meta.create_all(engine)

    return UserRepository(db_services,
                          MockPasswordServices())

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

'''
@pytest.mark.parametrize("value, expected_user_id", 
                         [("user",1),
                          ("user2",2),
                          ("user@user.com",1),
                          ("user2@user2.com",2),
                          ("000000",None),
                          ("111111",None)])
def test_read_by_identity_fields(repository, value, expected_user_id):
    user1 = UserModel(
        id=1,
        username="user",
        password="123456",
        email="user@user.com",
        phone="000000"
    )
    user2 = UserModel(
        id=2,
        username="user2",
        password="123456",
        email="user2@user2.com",
        phone="111111"
    )
    repository.create(user1)
    repository.create(user2)

    read_user = repository.read_by_identity_field(value)
    
    if expected_user_id != None:
        assert read_user.id == expected_user_id
    else:
        assert read_user is None
'''