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
    path('post/<str:post_id>/',views.GetPostByIDAPIView.as_view(), name='get_post_by_id'),
    path('post/<str:post_id>/update/', views.UpdatePostAPIView.as_view(), name='update_post'),
    path('post/<str:post_id>/delete/', views.DeletePostAPIView.as_view(), name='delete_post'),
    path('user/post/like/', views.LikePostAPIView.as_view(), name='like_post'),
    path('user/post/fetch-like/', views.LikedPostsAPIView.as_view(), name='fetct-like'),
    path('user/comment/', views.CreateCommentAPIView.as_view(), name='user-comment'),
    path('user/comment/reply/', views.CreateReplyCommentsAPIView.as_view(), name="user-comment-reply"),
    path('user/comment/replied-comments/', views.FetchRepliedCommentsAPIView.as_view(), name='fetch_replied_comments'),
    path('user/like-comments-count/', views.LikeAndCommentsCount.as_view(), name="like-comment-count"),
    path('user/check-user-likes/', views.CheckUserLikes.as_view(), name='check_user_likes'),
    path('user/notification-count/', views.NotificationCount.as_view(), name = "notificatin-count"),
    path('user/all-notification/', views.AllNotifications.as_view(), name = "notificatins"),
    path('user/mark-notification-as-seen/', views.MarkNotificationsAsSeen.as_view(), name = "mark-notification-as-seen"),
    path('user/save-post/', views.SavePost.as_view(), name = "save-post"),
    path('user/fetch-saved-post/', views.FetchSavedPosts.as_view(), name = "fetch-saved-post"),
    path('user/post-report/', views.CreatePostReport.as_view(), name = "post-report"),
    path('user/comment-report/', views.CreateCommentReport.as_view(), name = "comment-report"),

    path('user/comment/<str:post_id>/', views.get_comments, name='get_comments'),
    path('user/all-comment/<str:post_id>/', views.get_comments_and_replies, name='get_comments_for_post'),

    # -------------------------------- ADMIN SIDE ----------------------------------

    path('admin/list-reported-posts/', views.ListReportedPosts.as_view(), name='list_reported_posts'),
    path('admin/list-reported-posts/<str:post_id>/', views.DeleteReportedPost.as_view(), name='delete-reported-post'),
    path('admin/list-reported-comments/', views.ListReportedComments.as_view(), name='list_reported_comments'),
    path('admin/list-reported-comments/<str:comment_id>/delete/', views.DeleteReportedComment.as_view(), name='delete-reported-comment'),







    
]