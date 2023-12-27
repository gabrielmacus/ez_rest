from sqlalchemy.orm import relationship
from sqlalchemy import BigInteger, Float
from sqlalchemy import Table, Column, MetaData, Integer,Text, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from tests.modules.db_services import DbServices
from ez_rest.modules.role.models import RoleModel

meta = MetaData()
products = Table(
    'products',
    meta,
    Column('created_at',DateTime),
    Column('updated_at',DateTime),
    Column('deleted_at',DateTime),
    Column('id', Integer, primary_key=True),
    Column('name',String),
    Column('category',String),
    Column('price',Float)
)

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
    Column('phone',String),
    Column('email',String)
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

def create_tables():
    db_services = DbServices()
    engine = db_services.get_engine()
    meta.create_all(engine)
    return db_services