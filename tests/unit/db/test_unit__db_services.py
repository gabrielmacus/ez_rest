import pytest
from sqlalchemy.engine import Engine
from ez_rest.modules.db.services import DbServices
import os


TEST_DB_PATH = 'test.db'
TEST_DB_URI = f'sqlite:///{TEST_DB_PATH}'

os.environ['DB_CONNECTION_STRING'] = TEST_DB_URI

def test_create_engine():
    assert isinstance(DbServices().get_engine(), Engine) == True