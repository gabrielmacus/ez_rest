from ez_rest.modules.mapper.services import MapperServices
from ez_rest.modules.mapper.exceptions import MappingNotFoundException,InvalidFieldException
from ez_rest.modules.crud.models import BaseModel,BaseDTO
from dataclasses import dataclass
import pytest
from pydantic import BaseModel as PydancticModel, Field, EmailStr
import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class User(BaseModel):
    __tablename__ = "user"
    name:Mapped[str] = mapped_column(String)
    surname:Mapped[str] = mapped_column(String)
    password:Mapped[str] = mapped_column(String)
    email:Mapped[str] = mapped_column(String)

class PublicUser(BaseDTO):
    fullname:str = Field(max_length=20)
    email:EmailStr

class PublicUser2(PydancticModel):
    id:int
    fullname:str
    email:str

class PublicUser3(PydancticModel):
    fullname:str
    email:str

@pytest.fixture
def services():
    services = MapperServices()
    services.register(User, 
                      PublicUser,
                      lambda src: {
                          "fullname": f"{src['name']} {src['surname']}",
                          "email": src["email"]
                      })
    return services

@pytest.mark.parametrize("source, data, target_type, expected_data", [
    (
        {
            "id":1,
            "created_at":datetime.datetime(2020,1,1,0,0,0),
            "updated_at":None,
            "deleted_at":None,
            "is_deleted":False
        },
        {
            "fullname":"John Doe",
            "email":"user@user.com"
        },
        PublicUser,
        {

            "fullname":"John Doe",
            "email":"user@user.com",
            "id":1,
            "created_at":datetime.datetime(2020,1,1,0,0,0),
            "updated_at":None,
            "deleted_at":None
        }


    ),
    (
        {
            "id":1,
            "created_at":datetime.datetime(2020,1,1,0,0,0),
            "updated_at":None,
            "deleted_at":None,
            "is_deleted":False
        },
        {
            "fullname":"John Doe",
            "email":"user@user.com"
        },
        PublicUser2,
        {

            "fullname":"John Doe",
            "email":"user@user.com",
            "id":1
        }
    ),
    (
        {
            "id":1,
            "created_at":datetime.datetime(2020,1,1,0,0,0),
            "updated_at":None,
            "deleted_at":None,
            "is_deleted":False
        },
        {
            "fullname":"John Doe",
            "email":"user@user.com"
        },
        PublicUser3,
        {

            "fullname":"John Doe",
            "email":"user@user.com"
        }
    )
])
def test_map_default(services, source, data, target_type,expected_data):
    result = services.map_default(source, data, target_type)
    print(result)
    assert result == expected_data

@pytest.mark.parametrize("data, mappings, expected_data", [
    ({
        "name":"John",
        "surname":"Doe"
    },
    {
        "fullname":lambda src: f"{src['name']} {src['surname']}"
    },
    {
        "fullname":"John Doe"
    }),
    ({
        "fullname":"John Doe"
    },
    {
        "name":lambda src: src["fullname"].split(" ")[0],
        "surname":lambda src: src["fullname"].split(" ")[1]
    },
    {
        "name":"John",
        "surname":"Doe"
    })
])
def test_execute_mappings(services, data, mappings, expected_data):
    assert services.execute_mappings(data,
                                     mappings) == expected_data


# TODO: Test trying to map incomplete field (example: "name" to "fullname", that's composed by "name" and "surname")
    
@pytest.mark.parametrize("source,target_type,source_type,expected_dict,expected_exception",[
    (
        User(
            email="user@user.com",
            name="John",
            surname="Doe",
            password="123456"
        ),
        PublicUser,
        None,
        {
        "email":"user@user.com",
        "fullname":"John Doe"
        },
        None
    ),
    (
        {
            "email":"user@user.com",
            "name":"John",
            "surname":"Doe",
            "password":"123456"
        },
        PublicUser,
        User,
        {
        "email":"user@user.com",
        "fullname":"John Doe"
        },
        None
    ),
    (
        {
            "email":"user@user.com",
            "name":"John",
            "surname":"Doe",
            "password":"123456"
        },
        PublicUser,
        None,
        None,
        ValueError
    ),
    (
        {
            "email":"user@user.com",
            "name":"John",
            "surname":"Doe",
            "password":"123456"
        },
        User,
        PublicUser,
        None,
        MappingNotFoundException
    )
])
def test_map_dict(services, 
                  source, 
                  target_type, 
                  source_type, 
                  expected_dict, 
                  expected_exception):
    
    if expected_exception is None:
        dict = services.map_dict(
            source,
            target_type,
            source_type
        )

        assert dict == expected_dict
    else:
        with pytest.raises(expected_exception):
            services.map_dict(
                source,
                target_type,
                source_type
            )

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