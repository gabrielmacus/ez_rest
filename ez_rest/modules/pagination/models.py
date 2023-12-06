from pydantic import BaseModel
from typing import List, TypeVar, Generic
T = TypeVar("T")

# https://github.com/tiangolo/fastapi/issues/653#issuecomment-984509798
class PaginationDTO(BaseModel, Generic[T]):
    count:int
    page:int
    pages_count:int
    items:List[T]