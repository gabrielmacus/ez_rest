from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from ..singleton.models import SingletonMeta
import os

class DbServices(metaclass=SingletonMeta):
    _engine:Engine = None

    def get_engine(self) -> Engine:
        if self._engine == None:
            self._engine = create_engine(
                os.getenv('DB_CONNECTION_STRING'), echo=bool(int(os.getenv("DEBUG",1)))
            )
        return self._engine