from .repository import BaseUserRepository
from .models import BaseUserModel, TokenResponse, TokenConfig
from ..password.services import PaswordServices
from ..jwt.services import JWTServices
from fastapi import HTTPException, status
from fastapi.security import SecurityScopes
from typing import List
from jose import JWTError
import datetime
import os
from typing import Generic, TypeVar, Type, List
from ..singleton.models import SingletonMeta

TModel = TypeVar("TModel", bound=BaseUserModel)
TRepository = TypeVar("TRepository", bound=BaseUserRepository)

class BaseUserServices(Generic[TModel], metaclass=SingletonMeta):
    _subject_claim_field:str
    _repository:BaseUserRepository[TModel]
    _user_type:Type[TModel]
    _password_services:PaswordServices
    _jwt_services:JWTServices

    def __init__(self, 
                 repository:BaseUserRepository[TModel],
                 user_type:Type[TModel],
                 password_services:PaswordServices = None,
                 jwt_services:JWTServices = None
                 ) -> None:
        self._user_type = user_type
        self._repository = repository
        self._password_services = password_services if password_services != None else PaswordServices()
        self._jwt_services = jwt_services if jwt_services != None else JWTServices()

    def validate_user(self,
                    identity_value:str, 
                    plain_password:str) -> TModel | None:
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
        return user
           
    def create_token(self, 
                     user:TModel, 
                     scopes:List[str],
                     token_config:TokenConfig) -> str:
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
        expires_delta = datetime.timedelta(minutes=int(token_config.expire_minutes))
        expiration_date = datetime.datetime.utcnow() + expires_delta

        data_to_encode = {
            "iat":datetime.datetime.utcnow(),
            "sub":getattr(user, self._subject_claim_field),
            "exp":expiration_date,
            "scopes":scopes
        }

        return self._jwt_services.encode(data_to_encode, 
                                         token_config.secret, 
                                         token_config.algorithm)

    def create_access_token(self,
                            user:TModel, 
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
                                 TokenConfig(
                                    expire_minutes = expire_minutes, 
                                    secret = secret, 
                                    algorithm = algorithm
                                 ))

    def create_refresh_token(self,
                            user:TModel):
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
                                 TokenConfig(
                                    expire_minutes = expire_minutes, 
                                    secret = secret, 
                                    algorithm = algorithm
                                 ))

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
        
        scopes = user.role.scopes
        access_token = self.create_access_token(user, scopes)
        refresh_token = self.create_refresh_token(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    def validate_token(
        self,
        token:str,
        secret:str,
        algorithm:str
    ):
        try:
            payload = self._jwt_services.decode(
                token, 
                secret, 
                algorithms=[ algorithm ])
            
            sub:str = payload.get('sub')
            if sub is None:
                return False
            return payload
        except JWTError as e:
            # TODO: Log error
            print("HERE!",e)
            return False
    
    def check_scopes(self, 
                     token_scopes:list[str], 
                     required_scopes:SecurityScopes):
        """See https://flowlet.app/blog/oauth2-scopes-for-fine-grained-acls

        Args:
            token_scopes (list[str]): _description_
            security_scopes (SecurityScopes): _description_
        
        """
        for required_scope in required_scopes.scopes:
            required_resource,required_action = required_scope.split(":")

            if  (required_scope not in token_scopes and \
                f'{required_resource}:*' not in token_scopes) or \
                f'!{required_scope}' in token_scopes:
                return False

        return True

    def check_auth( self,
                    required_scopes:SecurityScopes,
                    token:str,
                    secret:str,
                    algorithm:str):
        
        if required_scopes.scopes:
            authenticate_value = f'Bearer scope="{required_scopes.scope_str}"'
        else:
            authenticate_value = "Bearer"

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": authenticate_value},
        )

        payload = self.validate_token(
            token,
            secret,
            algorithm
        )
        
        if payload is False:
            raise credentials_exception
    
        results = self._repository.read([
            getattr(self._user_type, self._subject_claim_field) == 
            payload.get('sub')])

        if len(results) == 0:
            raise credentials_exception
        
        if not self.check_scopes(
            payload.get('scopes',[]), 
            required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                headers={"WWW-Authenticate": authenticate_value},
            )

        return results[0]
