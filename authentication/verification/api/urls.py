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
    path("user/details/", views.UserDetails.as_view(), name="user-details"),
    path("forgotpassword/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("profile/picture/update/", views.ProfilePictureUpdateAPIView.as_view(), name="profile-picture-update"),
    path('profile/change-username/', views.ChangeUsernameAPIView.as_view(), name='user-list'),
    path('profile/update-profile/', views.UpdateProfileAPIView.as_view(), name='update_profile'),
    path('user-profile-picture/<str:username>/', views.UserProfileAPIView.as_view(), name='user_profile_api'),
    path('search/', views.UserSearch.as_view(), name='user_search'),
    path('validate-token/',views.ValidateTokenView.as_view(), name='validate_token'),

    # ---------------------ADMIN--------------------------
    path("admin/login/", views.AdminLoginView.as_view(), name="admin-login"),
    path('admin/users/', views.UserListView.as_view(), name='user-list'),
    path('admin/users/<int:user_id>/', views.UserListView.as_view(), name='user-list'),



  
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]