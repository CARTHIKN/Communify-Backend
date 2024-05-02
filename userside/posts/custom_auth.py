from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken

class TokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('Authorization')
        if not token:
            return None

        try:
            # Validate the token using Simple JWT
            access_token = AccessToken(token.split()[1])
        except (AuthenticationFailed, IndexError, KeyError):
            raise AuthenticationFailed('Invalid token')

        if not access_token.user.is_authenticated:
            raise AuthenticationFailed('User not authenticated')

        return (access_token.user, access_token)