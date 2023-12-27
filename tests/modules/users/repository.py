from ez_rest.modules.base_user.repository import BaseUserRepository
from ez_rest.modules.password.services import PaswordServices
from tests.modules.users.models import UserModel
from tests.modules.db_services import DbServices
from tests.modules.tables import create_tables

class UserRepository(BaseUserRepository[UserModel]):
    #_identity_fields = ['username','phone']

    def __init__(self, 
                 db_services: DbServices = None, 
                 password_services: PaswordServices = None) -> None:
        
        db_services = db_services if db_services is not None else create_tables()
        super().__init__(UserModel, db_services, password_services)