
from . serializers import UserRegisterSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed,ParseError
from verification.models import OTP, CustomUser
from django.contrib.auth import authenticate
from django.core.mail import send_mail
import random
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterView(APIView):
    def post(self, request):

        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            email = serializer.validated_data.get('email')

            # Check if username is already taken
            if CustomUser.objects.filter(username=username, is_verified=True).exists():
                return Response({'error': 'Username is already taken'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate OTP
            otp = random.randint(100000, 999999)
            print("OTP:", otp)

            # Save user with OTP
            user = serializer.save(otp=otp)

            # Send OTP via email
            send_otp_email(email, otp)

            # Save OTP in OTP model
            OTP.objects.create(email=email, otp=otp)

            content = {'message': 'OTP sent to your email'}
            return Response(content, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def send_otp_email(email, otp):
    print("this tooooooo")
    subject = 'OTP Verification'
    message = f'Your OTP is: {otp}'
    from_email = 'carthikn1920@gmail.com'  # Update with your email
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)


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
            user1=CustomUser.objects.filter(email=username_or_email,is_verified=True).first()
            username = user1.username            
            user = CustomUser.objects.filter(username=username, is_verified=True).first()

        else:
            user = authenticate(username=username_or_email, password=password)

        if user is not None and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            refresh["username"] = str(user.username)
            print("-----------------")
            print(str(user.username))

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'isAdmin' :user.is_superuser
            })
        
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        



class ForgotPasswordView(APIView):
    def post(self, request):

        email = request.data.get('email')
        user1=CustomUser.objects.filter(email=email,is_verified=True).first()
        username = user1.username            
        # Check if username is already taken
        if CustomUser.objects.filter(username=username, is_verified=True).exists():
            
        # Generate OTP
            user = CustomUser.objects.filter(username=username, is_verified=True).first()
            print(user)
            otp = random.randint(100000, 999999)
            print("OTP:", otp)

            # Save user with OTP
            user.otp = otp
            print(user.otp)
            print(user.username)
            user.save()


            # Send OTP via email
            send_otp_email(email, otp)

        # Save OTP in OTP model
            OTP.objects.create(email=email, otp=otp)

            content = {'message': 'OTP sent to your email'}
            return Response(content, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Email with this user not found'}, status=status.HTTP_400_BAD_REQUEST)
        



class ChangePasswordView(APIView):
    def post(self, request):
        print("===============================")
        email = request.data.get('email')
        print("===============================")
        password = request.data.get('password')
        user = CustomUser.objects.filter(email=email,is_verified=True).first()
        user.password = make_password(password)
        user.save()
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)