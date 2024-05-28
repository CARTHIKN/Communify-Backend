import requests
from django.http import JsonResponse

class TokenValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = self.get_token_from_request(request)
        if token:
            if not self.is_valid_token(token):
                return JsonResponse({'error': 'Invalid token'}, status=401)
        response = self.get_response(request)
        return response

    def get_token_from_request(self, request):
        authorization_header = request.headers.get('Authorization')
        if authorization_header and 'Bearer' in authorization_header:
            return authorization_header.split()[1]
        return None

    def is_valid_token(self, token):
        response = requests.post(
            'http://authentication:8000/api/accounts/validate-token/',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(response)
        return response.status_code == 200