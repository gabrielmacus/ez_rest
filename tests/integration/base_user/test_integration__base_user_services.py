from typing import Type
import pytest
from ez_rest.modules.jwt.services import JWTServices
from tests.mock_db_services import MockDbServices
from ez_rest.modules.role.models import RoleModel
from ez_rest.modules.role.repository import RoleRepository
from ez_rest.modules.base_user.services import BaseUserServices
from ez_rest.modules.base_user.models import BaseUserModel, TokenConfig
from ez_rest.modules.base_user.repository import BaseUserRepository
from ez_rest.modules.db.services import DbServices
from ez_rest.modules.password.services import PaswordServices
from fastapi import HTTPException, status
from fastapi.security import SecurityScopes
import time_machine
from datetime import datetime, timedelta
from jose import jwt

from sqlalchemy.orm import relationship
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
    Column('username',String),
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


class UserModel(BaseUserModel):
    #__abstract__ = True
    username:Mapped[str] = mapped_column(String(100))
    phone:Mapped[str] = mapped_column(String(100))
    #role:RoleModel = Relationship(sa_relationship=relationship("RoleModel", lazy="joined"))

class UserRepository(BaseUserRepository[UserModel]):
    #_identity_fields = ['username','phone']

    def __init__(self, 
                 db_services: DbServices = None, 
                 password_services: PaswordServices = None) -> None:
        super().__init__(UserModel, db_services, password_services)

class UserServices(BaseUserServices[UserModel]):
    _identity_fields = ['username','phone']
    _subject_claim_field = "username"


@pytest.fixture
def repository():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    meta.create_all(engine)

    return UserRepository(db_services=db_services)

@pytest.fixture
def role_repository():
    db_services = MockDbServices()
    engine = db_services.get_engine()
    meta.create_all(engine)

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
    user1 = UserModel(
        id=1,
        username="user",
        phone="4231234",
        password="123456"
    )
    user2 = UserModel(
        id=2,
        username="user2",
        phone="1111111",
        password="%&4$231"
    )
    user3 = UserModel(
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

@pytest.mark.parametrize("subject_claim_field, scopes, expire_minutes, secret",
                         [
                             ("username", ["users.read","users.create"],10,"123"),
                             ("email", ["users.read"],15,"222"),
                             ("phone", ["products.read"],200,"333")
                         ])
def test_create_token(repository,
                      subject_claim_field, 
                      scopes, 
                      expire_minutes, 
                      secret
                      ):
    
    class UserModel2(BaseUserModel):
        __abstract__ = True
        username:Mapped[str] = mapped_column(String)
        email:Mapped[str] = mapped_column(String)
        phone:Mapped[str] = mapped_column(String)
    
    class UserServices2(BaseUserServices[UserModel2]):
        _identity_fields = ["username"]
        _subject_claim_field = subject_claim_field

    user = UserModel2(
        username = "johndoe",
        email="user@user.com",
        phone="123123"
    )
    services = UserServices2(repository)
    dt = datetime(2020,1,1)
    with time_machine.travel(dt):
        token = services.create_token(user,
                            scopes,
                            TokenConfig(
                                algorithm="HS256",
                                expire_minutes=expire_minutes,
                                secret=secret
                            ))
        payload = jwt.decode(token, secret)

    assert payload['sub'] == getattr(user, subject_claim_field)
    assert payload["scopes"] == scopes
    assert datetime.utcfromtimestamp(payload['exp']) == dt + timedelta(minutes=expire_minutes)
    assert datetime.utcfromtimestamp(payload['iat']) == dt


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
    role = RoleModel(
        id=1,
        name="Sales Manager",
        scopes=scopes
    )

    user = UserModel(
        id=1,
        username="myuser",
        phone="4231234",
        password="123456",
        role_id=1
    )

    role_repository.create(role)
    repository.create(user)

    dt = datetime(2020,1,1,0,0,0,0)
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


@pytest.mark.parametrize("success,algo,iat,exp,sub,scopes,secret,token",
                         [(True,"HS256",1577836800,1577837400,"johndoe",["users:read","users:create"],"qwerty","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1Nzc4MzY4MDAsInN1YiI6ImpvaG5kb2UiLCJleHAiOjE1Nzc4Mzc0MDAsInNjb3BlcyI6WyJ1c2VyczpyZWFkIiwidXNlcnM6Y3JlYXRlIl19.zHR2XTR6l62nY373XTCEaiJlo9uxqsahhKzTOc5SqFU"),
                          (False,"HS256",1577836800,1577837400,"johndoe",["users:read","users:create"],"wrongsecret","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1Nzc4MzY4MDAsInN1YiI6ImpvaG5kb2UiLCJleHAiOjE1Nzc4Mzc0MDAsInNjb3BlcyI6WyJ1c2VyczpyZWFkIiwidXNlcnM6Y3JlYXRlIl19.zHR2XTR6l62nY373XTCEaiJlo9uxqsahhKzTOc5SqFU"),
                          (False,"HS256",1577836800,1577837400,"johndoe",["users:read","users:create"],"qwerty","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1Nzc4MzY4MDAsImV4cCI6MTU3NzgzNzQwMCwic2NvcGVzIjpbInVzZXJzOnJlYWQiLCJ1c2VyczpjcmVhdGUiXX0.zzrtmu3jxo8kCpbvkz9foZkcMXfv_nuoV8WlNklaLDA")
                           ])
def test_validate_token(repository, success, algo, iat, exp, sub, scopes, secret, token):
    services = UserServices(repository)

    dt = datetime(2020,1,1,0,0,0)
    with time_machine.travel(dt):
        payload = services.validate_token(token, secret, algo)

    if success == False:
        assert payload == False
        return

    assert payload['sub'] == sub
    assert payload["scopes"] == scopes
    assert payload['exp'] == exp
    assert payload['iat'] == iat

@pytest.mark.parametrize("token_scopes, required_scopes, result",
                         [(["products:read"],["products:read"], True),
                          (["products:create","products:read", "users:read"],["products:read", "products:create"], True),
                          (["products:*"], ["products:read"],True),
                          (["products:*", "!products:create"],["products:create"],False),
                          (["users.read", "products:*", "!products:create"], ["users:read","products:create"], False),
                          (["products:*", "!products:create"],["products:read"], True),
                          (["products:create"], ["products:read"], False),
                          ([], ["products:read"], False),
                          ([],[], True),
                          (["products:*"], [], True)
                          ])
def test_check_scopes(repository, token_scopes, required_scopes, result):
    services = UserServices(repository)
    assert services.check_scopes(token_scopes, SecurityScopes(required_scopes)) == result

@pytest.mark.parametrize("expected_exception,sub,required_scopes,secret,token",
                         [(None,"johndoe",["users:read","users:create"],"qwerty","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1Nzc4MzY4MDAsInN1YiI6ImpvaG5kb2UiLCJleHAiOjE1Nzc4Mzc0MDAsInNjb3BlcyI6WyJ1c2VyczpyZWFkIiwidXNlcnM6Y3JlYXRlIl19.zHR2XTR6l62nY373XTCEaiJlo9uxqsahhKzTOc5SqFU"),
                          (None,"foobar",[],"azerty","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3MDE1NTQzMTUsInN1YiI6ImZvb2JhciIsImV4cCI6MTcwMTU1NDkxNSwic2NvcGVzIjpbInVzZXJzOnJlYWQiXX0.reEtmA82_WcQLKvmWwB_f_fpa6dDu5M8f4WY51RDvuk"),
                          # Expired token
                          (status.HTTP_401_UNAUTHORIZED,"janedoe",["users:read","users:create"],"qwerty","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1NDYzMDA4MDAsInN1YiI6ImphbmVkb2UiLCJleHAiOjE1NDYzMDE0MDAsInNjb3BlcyI6WyJ1c2VyczpyZWFkIiwidXNlcnM6Y3JlYXRlIl19.mRB6OPqkg9UeongbjDBh53jtA0vwpdYznj4noN7-YJ8"),
                          # Unexistent user
                          (status.HTTP_401_UNAUTHORIZED,"janedoe",["users:read","users:create"],"qwerty","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1Nzc4MzY4MDAsInN1YiI6ImphbmVkb2UiLCJleHAiOjE1Nzc4Mzc0MDAsInNjb3BlcyI6WyJ1c2VyczpyZWFkIiwidXNlcnM6Y3JlYXRlIl19.lKAFL0rjx7aYEFsuGQehwdXOOd2ugGOO7J-dKlEQH3o"),
                          # Wrong secret
                          (status.HTTP_401_UNAUTHORIZED,"johndoe",["users:read","users:create"],"wrongsecret","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1Nzc4MzY4MDAsInN1YiI6ImpvaG5kb2UiLCJleHAiOjE1Nzc4Mzc0MDAsInNjb3BlcyI6WyJ1c2VyczpyZWFkIiwidXNlcnM6Y3JlYXRlIl19.zHR2XTR6l62nY373XTCEaiJlo9uxqsahhKzTOc5SqFU"),
                          # No sub
                          (status.HTTP_401_UNAUTHORIZED,"",["users:read","users:create"],"qwerty","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1Nzc4MzY4MDAsImV4cCI6MTU3NzgzNzQwMCwic2NvcGVzIjpbInVzZXJzOnJlYWQiLCJ1c2VyczpjcmVhdGUiXX0.zzrtmu3jxo8kCpbvkz9foZkcMXfv_nuoV8WlNklaLDA"),
                          # No required scopes
                          (status.HTTP_403_FORBIDDEN,"johndoe",["products:read"],"qwerty","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1Nzc4MzY4MDAsInN1YiI6ImpvaG5kb2UiLCJleHAiOjE1Nzc4Mzc0MDAsInNjb3BlcyI6WyJ1c2VyczpyZWFkIiwidXNlcnM6Y3JlYXRlIl19.zHR2XTR6l62nY373XTCEaiJlo9uxqsahhKzTOc5SqFU")
                           ])
def test_check_auth(repository, 
                    expected_exception,
                    sub, 
                    required_scopes,
                    secret, 
                    token ):
    

    repository.create(UserModel(
        id = 1,
        username = "johndoe",
        phone = "123123",
        password = "111111"
    ))
    repository.create(UserModel(
        id=2,
        username ="foobar",
        phone="555555",
        password="000000"
    ))
    services = UserServices(repository)

    with time_machine.travel(datetime(2020,1,1,0,0,0)):
        if expected_exception == None:
            user = services.check_auth(
                SecurityScopes(required_scopes),
                token,
                secret,
                "HS256",
            )
            assert user.username == sub
        else:
            with pytest.raises(HTTPException) as ex:
                services.check_auth(
                    SecurityScopes(required_scopes),
                    token,
                    secret,
                    "HS256",
                )
            assert ex.value.status_code == expected_exception