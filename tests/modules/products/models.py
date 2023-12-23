from ez_rest.modules.crud.models import BaseModel, BaseDTO
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String


class Product(BaseModel):
     __tablename__ = "products"
     name:Mapped[str] = mapped_column(String(100))
     category:Mapped[str] = mapped_column(String(100))

class ProductSaveDTO(BaseDTO):
    product_name:str
    product_category:str

class ProductReadDTO(BaseDTO):
    name_category:str
