from ez_rest.modules.base_user.services import BaseUserServices
from tests.modules.users.models import UserModel

class UserServices(BaseUserServices[UserModel]):
    _identity_fields = ['username','phone']
    _subject_claim_field = "username"
