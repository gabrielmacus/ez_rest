from typing import Generic, TypeVar, Type, List
from .models import BaseUserModel
from ..crud.repository import BaseRepository
from ..password.services import PaswordServices
from ..db.services import DbServices
from sqlalchemy import or_, column

T = TypeVar("T", bound=BaseUserModel)

class BaseUserRepository(Generic[T], BaseRepository[T]):
    _password_services:PaswordServices
    #_identity_fields:List[str]

    def __init__(self,
                 model:Type[T],
                 db_services: DbServices = None,
                 password_services:PaswordServices = None
                 ) -> None:
        self._password_services = password_services if password_services != None else PaswordServices()
        super().__init__(model, db_services)

    def create(self, item: T) -> T:
        item.password = self._password_services.hash_password(item.password)
        return super().create(item)

    """
    def read_by_identity_field(self, identity_field_value:str):
        filter = \
            or_(
                *[column(field) == identity_field_value 
                  for field in self._identity_fields]
            )
        
        results = self.read(filter)
        if len(results) == 0: return None
        return results[0]
    """