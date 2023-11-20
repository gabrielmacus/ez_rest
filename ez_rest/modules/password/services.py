from passlib.context import CryptContext

class PaswordServices:
    _password_context:CryptContext

    def __init__(self, 
                 password_context: CryptContext = None,) -> None:
        self._password_context = password_context if password_context != None else CryptContext(schemes=["bcrypt"],deprecated="auto")
    def hash_password(self, plain_password:str):
        return self._password_context.hash(plain_password)
    
    def verify_password(self, plain_pass:str, hashed_pass:str):
        return self._password_context.verify(plain_pass, hashed_pass)