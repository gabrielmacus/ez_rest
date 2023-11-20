from .repository import BaseUserRepository
from .models import BaseUser, TokenResponse
from ..password.services import PaswordServices
from ..jwt.services import JWTServices
from fastapi import HTTPException, status
from fastapi.security import SecurityScopes
from typing import List
from jose import JWTError
import datetime
import os
from typing import Generic, TypeVar, Type, List

T = TypeVar("T", bound=BaseUser)


class BaseUserServices(Generic[T]):
    _subject_claim_field:str
    _repository:BaseUserRepository[T]
    _password_services:PaswordServices
    _jwt_services:JWTServices

    def __init__(self, 
                 repository:BaseUserRepository[T],
                 password_services:PaswordServices = None,
                 jwt_services:JWTServices = None
                 ) -> None:
        self._repository = repository
        self._password_services = password_services if password_services != None else PaswordServices()
        self._jwt_services = jwt_services if jwt_services != None else JWTServices()

    def validate_user(self,
                    identity_value:str, 
                    plain_password:str) -> T | None:
        """Checks if user exists in repository and verifies password

        Args:
            identity_value (str): Value corresponding to a login field (username, email, etc)
            plain_password (str): Plain password

        Returns:
            T | None: Returns user if data is valid, otherwise returns None
        """

        user = self._repository.read_by_identity_field(identity_value)
        if user is None or not self._password_services\
                                    .verify_password(plain_password, user.password):
            return None
        print("HERE!!",user)
        return user
           
    def create_token(self, 
                     user:T, 
                     scopes:List[str],
                     expire_minutes:int,
                     secret:str,
                     algorithm:str) -> str:
        """_summary_

        Args:
            user (T): User instance
            scopes (List[str]): User associated scopes
            expire_minutes (int): Token duration in minutes
            secret (str): Secret that will be use to encrypt data
            algorithm (str): Algorithm to make the encryption

        Returns:
            str: Generated JWT
        """
        expires_delta = datetime.timedelta(minutes=int(expire_minutes))
        expiration_date = datetime.datetime.utcnow() + expires_delta

        data_to_encode = {
            "iat":datetime.datetime.utcnow(),
            "sub":getattr(user, self._subject_claim_field),
            "exp":expiration_date,
            "scopes":scopes
        }

        return self._jwt_services.encode(data_to_encode, secret, algorithm)

    def create_access_token(self,
                            user:T, 
                            scopes:List[str]) -> str:
        """Calls create_token with access token parameters from .env
        | .env variables:
        | ACCESS_TOKEN_EXPIRE_MINUTES
        | ACCESS_TOKEN_SECRET
        | ACCESS_TOKEN_ALGORITHM

        Args:
            user (T): User instance
            scopes (List[str]): User associated scopes

        Returns:
            str: Generated JWT
        """
        expire_minutes = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))
        secret = os.getenv('ACCESS_TOKEN_SECRET')
        algorithm = os.getenv('ACCESS_TOKEN_ALGORITHM')

        return self.create_token(user, 
                                 scopes, 
                                 expire_minutes, 
                                 secret, 
                                 algorithm)

    def create_refresh_token(self,
                            user:T):
        expire_minutes = int(os.getenv('REFRESH_TOKEN_EXPIRE_MINUTES'))
        secret = os.getenv('REFRESH_TOKEN_SECRET')
        algorithm = os.getenv('REFRESH_TOKEN_ALGORITHM')
        """Calls create_token with refresh token parameters from .env
        | .env variables:
        | REFRESH_TOKEN_EXPIRE_MINUTES
        | REFRESH_TOKEN_SECRET
        | REFRESH_TOKEN_ALGORITHM

        Args:
            user (T): User instance

        Returns:
            str: Generated JWT
        """
        return self.create_token(user, 
                                 [], 
                                 expire_minutes, 
                                 secret, 
                                 algorithm)

    def handle_token_generation(self, 
                              identity_value:str, 
                              plain_password:str) -> TokenResponse:
        """Handles token generation

        Args:
            identity_value (str): Value corresponding to a login field (username, email, etc)
            plain_password (str): Plain password

        Raises:
            HTTPException: If credentials are not valid

        Returns:
            TokenResponse: Object instance with access_token and refresh_token
        """
        user = self.validate_user(identity_value, plain_password)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate":"Bearer"}
            )
        
        # TODO: Load scopes associated to user role
        scopes = []
        access_token = self.create_access_token(user, scopes)
        refresh_token = self.create_refresh_token(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )




        
        