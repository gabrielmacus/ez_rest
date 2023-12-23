from pydantic import BaseModel
from typing import List, TypeVar, Generic
from ..crud.models import BaseDTO

# https://github.com/tiangolo/fastapi/issues/653#issuecomment-984509798
class PaginationDTO[T:BaseDTO](BaseModel):
    count:int
    page:int
    pages_count:int
    items:List[T]