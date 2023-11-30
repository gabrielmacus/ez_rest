from ez_rest.modules.mapper.services import MapperServices
from dataclasses import dataclass
import pytest

@dataclass
class User:
    name:str
    surname:str
    password:str
    email:str

@dataclass
class PublicUser:
    fullname:str
    email:str

@pytest.fixture
def services():
    services = MapperServices()
    services.register(User, 
                      PublicUser,
                      lambda src: {
                          "fullname": f"{src.name} {src.surname}",
                          "email": src.email
                      })
    return services

def test_map_dict(services):
    dict = services.map_dict(
        User(
            email="user@user.com",
            name="John",
            surname="Doe",
            password="123456"
        ),
        PublicUser
    )
    assert dict == {
        "email":"user@user.com",
        "fullname":"John Doe"
    }

def test_map(services):
    public_user = services.map(
        User(
            email="user@user.com",
            name="John",
            surname="Doe",
            password="123456"
        ),
        PublicUser
    )
    assert public_user.fullname == "John Doe"
    assert public_user.email == "user@user.com"