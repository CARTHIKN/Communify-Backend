from django.urls import path
from . import views

urlpatterns = [
    path('create-post/', views.CreatePostAPIView.as_view(), name='create_post_api'),
    path('post-lists/', views.PostListAPIView.as_view(), name='create_post_api'),
    path('user/posts/', views.UserPostListAPIView.as_view(), name='user-posts'),
    path('user/follow/', views.CreateFriendAPIView.as_view(), name='user-follow'),
    path('user/unfollow/', views.DeleteFriendAPIView.as_view(), name='user-unfollow'),
    path('user/check-following/<str:username>/<str:friend_username>/', views.CheckFollowingAPIView.as_view(), name='user-following-check'),
    path('user/friends-count/<str:username>/', views.FollowerFollowingCountAPIView.as_view(), name='user-following-check'),




    
]