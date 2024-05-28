
from django.http import JsonResponse
from . serializers import UserRegisterSerializer, UserProfileSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed,ParseError
from verification.models import OTP, CustomUser,UserProfile
from django.contrib.auth import authenticate
from django.core.mail import send_mail
import random
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from rest_framework_simplejwt.tokens import RefreshToken
import base64
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from verification.tasks import send_otp_email





class RegisterView(APIView):
    def post(self, request):
        
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            email = serializer.validated_data.get('email')

           
            if CustomUser.objects.filter(username=username, is_verified=True).exists():
                return Response({'error': 'Username is already taken'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate OTP
            otp = random.randint(100000, 999999)

            user = serializer.save(otp=otp)

            send_otp_email.delay(email, otp)

            # Save OTP in OTP model
            OTP.objects.create(email=email, otp=otp)

            content = {'message': 'OTP sent to your email'}
            return Response(content, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class VerifyOTPView(APIView):
    def post(self, request):
        otp = request.data.get('otp')
        email = request.data.get('email')

        # Find the user with the given email and matching OTP
        try:
            user = CustomUser.objects.get(email=email, otp=otp)
        except CustomUser.DoesNotExist:
            # If the user does not exist or OTP is invalid
            return Response({'error': 'Invalid OTP '}, status=status.HTTP_400_BAD_REQUEST)

        # OTP is verified, update user's verification status and clear OTP
        user.is_verified = True
        user.otp = None
        user.save()

        return Response({'message': 'OTP verification successful'}, status=status.HTTP_200_OK)

        

class LoginView(APIView):
    def post(self, request):
        username_or_email = request.data.get('username_or_email')
        password = request.data.get('password')

        if '@' in username_or_email:
            user = CustomUser.objects.filter(email=username_or_email, is_verified=True).first()
        else:
            user = authenticate(username=username_or_email, password=password)

        if user is not None and user.check_password(password):
            if user.is_blocked:
                return Response({'error': 'You are blocked by the user.'}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            refresh["username"] = str(user.username)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'isAdmin': user.is_superuser
            })
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginAndRegisterView(APIView):
    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        
        
        
        user = CustomUser.objects.filter(email=email, is_verified=True).first()
        
        if user:
            refresh = RefreshToken.for_user(user)
            refresh["username"] = str(user.username)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'isAdmin': user.is_superuser,
                'username': username,
            }, status=status.HTTP_200_OK)
        else:
            password = generate_random_password()  
            new_user = CustomUser.objects.create_user(email=email, username=username, password=password, phone="0" ,is_verified=True)

            refresh_new_user = RefreshToken.for_user(new_user)
            refresh_new_user["username"] = str(new_user.username)

            return Response({
                'message': 'User created successfully',
                'email': email,
                'username': username,
                'access': str(refresh_new_user.access_token),
                'refresh': str(refresh_new_user),
                'isAdmin': new_user.is_superuser
            }, status=status.HTTP_201_CREATED)
        
        
def generate_random_password():
    import random
    import string

    password_length = 10
    characters = string.ascii_letters + string.digits + string.punctuation
    random_password = ''.join(random.choice(characters) for i in range(password_length))
    return random_password




class ForgotPasswordView(APIView):
    def post(self, request):

        email = request.data.get('email')
        user1=CustomUser.objects.filter(email=email,is_verified=True).first()
        username = user1.username            
        # Check if username is already taken
        if CustomUser.objects.filter(username=username, is_verified=True).exists():
            
        # Generate OTP
            user = CustomUser.objects.filter(username=username, is_verified=True).first()
            otp = random.randint(100000, 999999)

            # Save user with OTP
            user.otp = otp
            user.save()
            send_otp_email.delay(email, otp)

            OTP.objects.create(email=email, otp=otp)

            content = {'message': 'OTP sent to your email'}
            return Response(content, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Email with this user not found'}, status=status.HTTP_400_BAD_REQUEST)
        



class ChangePasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = CustomUser.objects.filter(email=email,is_verified=True).first()
        user.password = make_password(password)
        user.save()
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
    




class ProfilePictureUpdateAPIView(APIView):
    def post(self, request, format=None):
        username = request.data.get('username')
        profile_picture_url = request.data.get('profile_picture_url')

        try:
            custom_user = CustomUser.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({"error": "CustomUser not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user_profile, created = UserProfile.objects.get_or_create(user=custom_user)
        except Exception as e:
            return Response({"error": "Error fetching/creating user profile."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if 'remove' in request.data and request.data['remove'] == 'true':
            # Handle removal of profile picture
            user_profile.profile_picture = None
            user_profile.remove = False
        else:
            # Update profile picture URL
            user_profile.profile_picture = profile_picture_url
            user_profile.remove = True

        user_profile.save()
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    

class UpdateProfileAPIView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        bio = request.data.get('bio')
        dob = request.data.get('dob')

        try:
            custom_user = CustomUser.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({"error": "CustomUser not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            user_profile, created = UserProfile.objects.get_or_create(user=custom_user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

        user_profile.bio = bio
        user_profile.dob = dob
        user_profile.save()

        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)


class UserProfileAPIView(APIView):
    def get(self, request, username, format=None):
        try:
            custom_user = CustomUser.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response({"error": "CustomUser not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            user_profile = UserProfile.objects.filter(user=custom_user).first()
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            
            return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
        

class UserDetails(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = CustomUser.objects.get(id=request.user.id)
        data = UserSerializer(user).data
        data['isAdmin'] = user.is_superuser
        
            
        content = data
        return Response(content)
    


class UserSearch(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        username = request.GET.get('username', '')

        if not username.strip():  
            return Response({'users': []}) 
        users = CustomUser.objects.filter(username__icontains=username)

        serialized_users = []
        for user in users:
            profile_picture_url = ''
            try:
                profile = user.profile
                profile_picture_url = profile.profile_picture if profile.profile_picture else ''
            except UserProfile.DoesNotExist:
                pass

            serialized_user = {
                'username': user.username,
                'email': user.email,
                'profile_picture': profile_picture_url,
            }
            serialized_users.append(serialized_user)

        return Response({'users': serialized_users})
    

class ValidateTokenView(APIView):
    def post(self, request):
        try:
            token = request.headers['Authorization'].split()[1]
            AccessToken(token)  # This will raise an exception if the token is invalid
            return Response({'valid': True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'valid': False}, status=status.HTTP_401_UNAUTHORIZED)





# ----------------------------- ADMIN ----------------------------------------

class AdminLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        
        if username and password:
            # Check if a user with the provided username exists
            user = CustomUser.objects.filter(username=username).first()
            
            # Authenticate the user if found
            if user and user.check_password(password):
                refresh = RefreshToken.for_user(user)
                refresh["username"] = str(user.username)
             

                # Check if the user is an admin
                if user.is_superuser:
                    return Response({
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                        'isAdmin': True
                    })
                else:
                    return Response({'error': 'No superuser with these credentials'}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Both username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        

class UserListView(APIView):
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10 

    def get(self, request, format=None):
        users = CustomUser.objects.filter(is_verified=True).order_by('created_at')

        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(users, request)
        
        serializer = UserSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)
    
    def patch(self, request, user_id, format=None):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action == 'block':
            user.is_blocked = True
            user.save()
            return Response({'message': 'User blocked successfully'}, status=status.HTTP_200_OK)
        elif action == 'unblock':
            user.is_blocked = False
            user.save()
            return Response({'message': 'User unblocked successfully'}, status=status.HTTP_200_OK)
        



class ChangeUsernameAPIView(APIView):
    def post(self, request, *args, **kwargs):
        current_username = request.data.get('username')
        new_username = request.data.get('newUsername')

        if CustomUser.objects.filter(username=new_username).exists():
            return Response({'message': 'Username is already taken'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, username=current_username)

        user.username = new_username
        user.save()

        response_data = {
            'message': 'Username changed successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'is_admin':user.is_staff,
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)