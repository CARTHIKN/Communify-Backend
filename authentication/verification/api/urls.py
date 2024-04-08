from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [

    path("register/", views.RegisterView.as_view(), name="user-register"),
    path("register/otp", views.VerifyOTPView.as_view(), name="user-registe-otp"),
    path("login/", views.LoginView.as_view(), name="user-login"),
    path("forgotpassword/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),


    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]