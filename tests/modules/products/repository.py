
class ProductsRepository(BaseRepository[Product2]):
    def __init__(self, 
                 db_services: DbServices = None) -> None:
        super().__init__(Product2, db_services)