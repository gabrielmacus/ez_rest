from jose import jwt
from typing import List

class JWTServices:
    def encode(self,claims:dict,key:str,algorithm:str):
        return jwt.encode(claims, key, algorithm=algorithm)
    
    def decode(self, token:str, key:str, algorithms:List[str]):
        return jwt.decode(token, key, algorithms=algorithms)

