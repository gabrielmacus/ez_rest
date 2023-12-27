from ez_rest.modules.db.services import DbServices
from ez_rest.modules.role.repository import RoleRepository as BaseRoleRepository
from tests.modules.db_services import DbServices
from tests.modules.tables import create_tables

class RoleRepository(BaseRoleRepository):
    def __init__(self, db_services: DbServices = None) -> None:
        db_services = db_services if db_services is not None else create_tables()
        super().__init__(db_services)