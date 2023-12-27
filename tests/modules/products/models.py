from ez_rest.modules.crud.models import BaseModel, BaseDTO
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Float


class Product(BaseModel):
     __tablename__ = "products"
     name:Mapped[str] = mapped_column(String(100))
     category:Mapped[str] = mapped_column(String(100))
     price:Mapped[float] = mapped_column(Float)

class ProductSaveDTO(BaseDTO):
    product_name:str
    product_category:str
    product_price:float

class ProductReadDTO(BaseDTO):
    name_category:str
    name:str
    category:str
    price:float
