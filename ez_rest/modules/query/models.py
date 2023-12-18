
from enum import Enum
from typing import List, Optional
from sqlalchemy import ColumnElement, UnaryExpression
from dataclasses import dataclass

class Functions(Enum):
    EXTRACT = 0
    SUM = 1
    SUB = 2
    DIV = 3
    MUL = 4

class Operator(Enum):
    GT = 0
    LT = 1
    GE = 2
    LE = 3
    EQ = 4
    NE = 5
    IN = 6
    NIN = 7
    LK = 8
    ILK = 9
    NLK = 10
    NILK = 11

@dataclass
class Query():
    filter:Optional[ColumnElement[bool]]
    page:str
    limit:str
    order_by:Optional[List[UnaryExpression]]
