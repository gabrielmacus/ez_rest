import pytest
from tests.mock_db_services import MockDbServices
from sqlmodel import SQLModel
from ez_rest.modules.role.models import Role
from ez_rest.modules.role.repository import RoleRepository
from ez_rest.modules.base_user.services import BaseUserServices
from ez_rest.modules.base_user.models import BaseUser
from ez_rest.modules.base_user.repository import BaseUserRepository
from ez_rest.modules.db.services import DbServices
from ez_rest.modules.password.services import PaswordServices
from fastapi import HTTPException
import time_machine
from datetime import datetime, timedelta
from jose import jwt

from ez_rest.modules.role.models import Role
from sqlmodel import Field, Relationship, SQLModel, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import BigInteger



class User2(BaseUser, table=True):
    
    username:str
    phone:str
    #role_id:int = Field(sa_column=Column(BigInteger(), ForeignKey("role.id")))
    #role:Role = Relationship(sa_relationship=relationship("Role", lazy="joined")) #generic_relationship(TRole, role_id)


class UserServices(BaseUserServices[User2]):
    _subject_claim_field = "username"

class UserRepository(BaseUserRepository[User2]):
    _identity_fields = ['username','phone']

    def __init__(self, 
                 db_services: DbServices = None, 
                 password_services: PaswordServices = None) -> None:
        super().__init__(User2, db_services, password_services)

@pytest.fixture
def repository():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    SQLModel.metadata.create_all(engine)

    return UserRepository(db_services=db_services)

@pytest.fixture
def role_repository():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    SQLModel.metadata.create_all(engine)

    return RoleRepository(db_services=db_services)


@pytest.mark.parametrize("identity_value, password, expected_id", 
                         [("user","123456",1),
                          ("user2","%&4$231",2),
                          ("user3","DeM}·$",3),
                          ("4231234","123456",1),
                          ("22222222","111111",None),
                          ("user4","111111",None),
                          ("user","ABCDEF",None)])
def test_validate_user(repository, identity_value, password, expected_id):
    services = UserServices(
        repository=repository
    )
    user1 = User2(
        id=1,
        username="user",
        phone="4231234",
        password="123456"
    )
    user2 = User2(
        id=2,
        username="user2",
        phone="1111111",
        password="%&4$231"
    )
    user3 = User2(
        id=3,
        username="user3",
        phone="22222222",
        password="DeM}·$"
    )
    repository.create(user1)
    repository.create(user2)
    repository.create(user3)
    
    validated_user = services.validate_user(identity_value, password)
    if expected_id is None:
        assert validated_user == None
    else:
        assert validated_user.id == expected_id

@pytest.mark.parametrize("username,password,exception_expected", 
                         [("useruser","123123",True),
                          ("myuser","000000",True),
                          ("myuser","123456",False),
                          ("4231234","123456",False)])
def test_handle_token_generation(repository, role_repository, monkeypatch, username, password, exception_expected):

    monkeypatch.setenv(f'ACCESS_TOKEN_EXPIRE_MINUTES', "10")
    monkeypatch.setenv(f'ACCESS_TOKEN_SECRET', "qwerty")
    monkeypatch.setenv(f'ACCESS_TOKEN_ALGORITHM', "HS256")

    monkeypatch.setenv(f'REFRESH_TOKEN_EXPIRE_MINUTES', "20")
    monkeypatch.setenv(f'REFRESH_TOKEN_SECRET', "000000")
    monkeypatch.setenv(f'REFRESH_TOKEN_ALGORITHM', "HS256")

    services = UserServices(
        repository=repository
    )

    scopes = ["user:read","user:create"]
    role = Role(
        id=1,
        name="Sales Manager",
        scopes=scopes
    )

    user = User2(
        id=1,
        username="myuser",
        phone="4231234",
        password="123456",
        role_id=1
    )

    role_repository.create(role)
    repository.create(user)
    

    dt = datetime(2020,1,1,0,0,0)
    with time_machine.travel(dt):
        
        if not exception_expected:
            token_response = services.handle_token_generation(username, password)

            payload = jwt.decode(token_response.access_token, "qwerty", algorithms=["HS256"])
            assert payload['sub'] == user.username
            assert payload["scopes"] == scopes
            assert datetime.utcfromtimestamp(payload['exp']) == dt + timedelta(minutes=10)
            assert datetime.utcfromtimestamp(payload['iat']) == dt

            payload = jwt.decode(token_response.refresh_token, "000000", algorithms=["HS256"])
            assert payload['sub'] == user.username
            assert payload["scopes"] == []
            assert datetime.utcfromtimestamp(payload['exp']) == dt + timedelta(minutes=20)
            assert datetime.utcfromtimestamp(payload['iat']) == dt
        else:
            with pytest.raises(HTTPException):
                services.handle_token_generation(username, password)
        




'''
@pytest.mark.parametrize("env_var_prefix, expire_minutes", 
                         [("ACCESS",10),
                          ("REFRESH",20)])
def test_create_token(repository, monkeypatch, env_var_prefix, expire_minutes):
    scopes = ["user:read","user:create"]
    secret = "qwerty"
    algorithm = "HS256"

    monkeypatch.setenv(f'{env_var_prefix}_TOKEN_EXPIRE_MINUTES', str(expire_minutes))
    monkeypatch.setenv(f'{env_var_prefix}_TOKEN_SECRET', secret)
    monkeypatch.setenv(f'{env_var_prefix}_TOKEN_ALGORITHM', algorithm)

    services = UserServices(
        repository=repository
    )
    user = User2(
        id=1,
        username="myuser",
        phone="4231234",
        password="123456"
    )

    
    dt = datetime(2020,1,1,0,0,0)
    with time_machine.travel(dt):
        token = services.create_token(user, scopes, expire_minutes, secret, algorithm)
        payload = jwt.decode(token, secret, algorithms=[algorithm])

        assert payload['sub'] == user.username
        assert payload["scopes"] == scopes
        assert datetime.utcfromtimestamp(payload['exp']) == dt + timedelta(minutes=expire_minutes)
        assert datetime.utcfromtimestamp(payload['iat']) == dt
'''