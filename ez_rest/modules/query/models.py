from pydantic import BaseModel
from enum import Enum
from typing import List

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

'''
class Operation(BaseModel):
    attribute:str
    operator:Operator
    value:str | int | float | List[str] | List[int] | List[float]
'''