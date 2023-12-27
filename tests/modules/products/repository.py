from ez_rest.modules.crud.repository import BaseRepository
from tests.modules.products.models import Product
from tests.modules.db_services import DbServices
from tests.modules.tables import create_tables

class ProductsRepository(BaseRepository):
    def __init__(self, 
                 db_services: DbServices = None) -> None:
        db_services = create_tables() if db_services is None else db_services
        super().__init__(Product, db_services)