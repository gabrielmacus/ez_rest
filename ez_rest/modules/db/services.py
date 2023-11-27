from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import os

class DbServices():
    _engine:Engine = None
    
    def __new__(cls): # pragma: no cover
        if not hasattr(cls, 'instance'):
            cls.instance = super(DbServices, cls).__new__(cls)
        return cls.instance

    def get_engine(self) -> Engine:
        if self._engine == None:
            self._engine = create_engine(
                os.getenv('DB_CONNECTION_STRING'), echo=bool(int(os.getenv("DEBUG",1)))
            )
        return self._engine