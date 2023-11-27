from sqlalchemy.engine import Engine
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
import os


TEST_DB_PATH = 'test.db'
TEST_DB_URI = f'sqlite:///{TEST_DB_PATH}'
class MockDbServices():
    
    def __init__(self) -> None:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    def get_engine(self) -> Engine:
        engine = create_engine(
            TEST_DB_URI,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=True
        )
        return engine
