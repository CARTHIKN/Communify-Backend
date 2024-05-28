import bson
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from monogdb_connections import db
from bson.json_util import dumps 
import base64
import json
from django.core.files.uploadedfile import InMemoryUploadedFile
from bson.objectid import ObjectId
from datetime import datetime
from posts.models import friendes_collections, likes_collections, comments_collections, replied_comment_collections,Notification,saved_post, post_report, comment_report
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import BasePermission
import requests
from posts.producer import publish




posts_collection = db['Posts']

class TokenAuthenticationPermission(BasePermission):
    def has_permission(self, request, view):
        authorization_header = request.headers.get('Authorization', '')
        if not authorization_header:
            return False  # Authorization header is missing or empty
        
        token = authorization_header.split()[-1]  # Extract token from Authorization header
        return self.is_valid_token(token)

    def is_valid_token(self, token):
        response = requests.post(
            'http://authentication:8000/api/accounts/validate-token/',
            headers={'Authorization': f'Bearer {token}'}
        )
        return response.status_code == 200

class CreatePostAPIView(APIView):
    permission_classes = [TokenAuthenticationPermission] 
  
    def post(self, request, *args, **kwargs):

        caption = request.data.get('caption')  # Use request.data instead of request.POST
        image_file = request.FILES.get('image')
        username = request.data.get('username')

        if image_file and isinstance(image_file, InMemoryUploadedFile):
            # Read the image data
            image_data = image_file.read()

            # Encode the image data as base64 for storage
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            # Create a dictionary to store the post data
            current_time = datetime.now()
            post_data = {
                'username':username,
                'caption': caption,
                'image_data': encoded_image,
                'created_at': current_time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Insert the post_data into MongoDB
            posts_collection.insert_one(post_data)

            return Response({'message': 'Post created successfully'}, 
                            status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Invalid image file'}, status=status.HTTP_400_BAD_REQUEST)
    

class PostListAPIView(APIView):
    permission_classes = [TokenAuthenticationPermission] 

    def get(self, request):
        posts_cursor = posts_collection.find()

        # Convert the cursor to a list of dictionaries and serialize
        posts_list = []
        for post in posts_cursor:
            post_data = {
                'id': str(post['_id']), 
                'username':post.get('username', ''),# Convert ObjectId to string
                'caption': post.get('caption', ''),  # Use get() to handle missing fields
                'image_url': post.get('image_data', ''),  # Use get() to handle missing fields
                'created_at':self.format_created_at(post.get('created_at', ''))  # Call format_created_at method
                # Add other fields as needed
            }
            posts_list.append(post_data)

        response_data = {
            'posts': posts_list  # Wrap posts_list in a 'posts' key
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    def format_created_at(self, created_at):
        # Convert timestamp string to datetime object
        timestamp_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")

        # Convert datetime object to 12-hour format string
        formatted_created_at = timestamp_obj.strftime("%d-%m-%y")

        return formatted_created_at


class UserPostListAPIView(APIView):
    def get(self, request):
        username = request.query_params.get('username')  # Get the username from query params

        # Check if username is provided

        posts_cursor = posts_collection.find({'username': username})
     

        # Convert the cursor to a list of dictionaries and serialize
        posts_list = []
        for post in posts_cursor:
            post_data = {
                'id': str(post['_id']), 
                'username': post.get('username', ''),  # Convert ObjectId to string
                'caption': post.get('caption', ''),  # Use get() to handle missing fields
                'image_url': post.get('image_data', ''),  # Use get() to handle missing fields
                'created_at': post.get('created_at', '')
                # Add other fields as needed
            }
            posts_list.append(post_data)

        response_data = {
            'posts': posts_list  # Wrap posts_list in a 'posts' key
        }

        return Response(response_data, status=status.HTTP_200_OK)
    



class CreateFriendAPIView(APIView):
    def post(self, request):
        if 'username' not in request.data or 'friend_username' not in request.data:
            return Response({'error': 'Both username and friend_username are required'}, status=status.HTTP_400_BAD_REQUEST)

        username = request.data['username']
        friend_username = request.data['friend_username']
      

        user_friend = friendes_collections.find_one({'username': username})
        if user_friend:
            friendes_collections.update_one({'username': username}, {'$addToSet': {'following': friend_username}})
        else:
            friendes_collections.insert_one({'username': username, 'following': [friend_username]})

        friend_friend = friendes_collections.find_one({'username': friend_username})
        if friend_friend:
            friendes_collections.update_one({'username': friend_username}, {'$addToSet': {'followers': username}})
        else:
            friendes_collections.insert_one({'username': friend_username, 'followers': [username]})

        return Response({'message': 'Friend added successfully'}, status=status.HTTP_201_CREATED)
    


class DeleteFriendAPIView(APIView):
    def post(self, request):
        if 'username' not in request.data or 'friend_username' not in request.data:
            return Response({'error': 'Both username and friend_username are required'}, status=status.HTTP_400_BAD_REQUEST)

        username = request.data['username']
        friend_username = request.data['friend_username']

        user_friend = friendes_collections.find_one({'username': username})
        if user_friend:
            friendes_collections.update_one({'username': username}, {'$pull': {'following': friend_username}})

        friend_friend = friendes_collections.find_one({'username': friend_username})
        if friend_friend:
            friendes_collections.update_one({'username': friend_username}, {'$pull': {'followers': username}})
        return Response({'message': 'Friend removed successfully'}, status=status.HTTP_200_OK)



class CheckFollowingAPIView(APIView):
    def get(self, request, username, friend_username):
        # Query MongoDB to check if friend_username is in the following list of username
        user_friend = friendes_collections.find_one({'username': username})
        is_following = False
        if user_friend:
            following_list = user_friend.get('following', [])
            if friend_username in following_list:
                is_following = True

        return Response({'is_following': is_following}, status=status.HTTP_200_OK)


class FollowerFollowingCountAPIView(APIView):
    def get(self, request, username):
        user = friendes_collections.find_one({'username': username})
        if user:
            followers_count = len(user.get('followers', []))
            following_count = len(user.get('following', []))
            followers = user.get('following', [])
            post_count = posts_collection.count_documents({'username': username})
            
            return Response({'followers_count': followers_count, 'following_count': following_count, 'post_count': post_count, 'follwers_username' : followers})
            
        else:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        


class GetPostByIDAPIView(APIView):
    def get(self, request, post_id, *args, **kwargs):
        # Find the post in MongoDB using the post_id
        post = posts_collection.find_one({'_id': ObjectId(post_id)})

        if post:
            # Convert ObjectId to string before serializing
            post['_id'] = str(post['_id'])
            
            # Check if 'image_data' exists in the post and convert it to 'image_url'
            if 'image_data' in post:
                post['image_url'] = f"data:image/jpeg;base64,{post.pop('image_data')}"
            
            return Response(post, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)


class UpdatePostAPIView(APIView):
    def put(self, request, post_id, *args, **kwargs):
        caption = request.data.get('caption')  

       
        post = posts_collection.find_one({'_id': ObjectId(post_id)})
        if not post:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        posts_collection.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': {'caption': caption}}  
        )

        return Response({'message': 'Caption updated successfully'}, status=status.HTTP_200_OK)


class DeletePostAPIView(APIView):
    def delete(self, request, post_id, *args, **kwargs):
        # Check if the post exists
        post = posts_collection.find_one({'_id': ObjectId(post_id)})
        if not post:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        # Delete the post from MongoDB
        posts_collection.delete_one({'_id': ObjectId(post_id)})

        return Response({'message': 'Post deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    

class LikePostAPIView(APIView):

    def post(self, request, *args, **kwargs):
        post_id = request.data.get('postId')
        username = request.data.get('username') 
        date = datetime.now()
        
        try:
            existing_like = likes_collections.find_one({'post_id': ObjectId(post_id)})
            if existing_like:
                if username in existing_like['users']:
                    likes_collections.update_one({'_id': existing_like['_id']}, {'$pull': {'users': username}})
                    return JsonResponse({'message': 'Post unliked successfully'}, status=status.HTTP_200_OK)
                else:
                    
                    likes_collections.update_one({'_id': existing_like['_id']}, {'$push': {'users': username}})
                    post = posts_collection.find_one({'_id':ObjectId(post_id)})
                    userr = post['username']
                    data = {"by_user": username, "post_id": post_id, "notification_type": "like", 'user': userr, 'created_at': date,'seen':False}
                    Notification.insert_one(data)
                    publish(
                    method="like",
                    body={'user':userr},
                    )
                    return JsonResponse({'message': 'Post liked successfully'}, status=status.HTTP_201_CREATED)
            else:
                
                new_like = {
                    'post_id': ObjectId(post_id),
                    'users': [username],
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                likes_collections.insert_one(new_like)
                post = posts_collection.find_one({'_id':ObjectId(post_id)})
                userr = post['username']
                data = {"by_user": username, "post_id": post_id, "notification_type": "like", 'user': userr, 'created_at': date,'seen':False}
                Notification.insert_one(data)
                publish(
                    method="like",
                    body={'user':userr},
                    )

                return JsonResponse({'message': 'Post liked successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LikedPostsAPIView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username') 
        
        try:
            
            liked_posts = likes_collections.find({'users': username})
            liked_post_ids = [str(post['post_id']) for post in liked_posts]
            return JsonResponse(liked_post_ids, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        

class CreateCommentAPIView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        post_id = request.data.get('post_id')
        current_time = datetime.now()
        content = request.data.get('content')
        post = posts_collection.find_one({'_id':ObjectId(post_id)})
        userr = post['username']
        date = datetime.now()

        

        comment = {
            'post_id' : ObjectId(post_id),
            'username' : username,
            'content' : content,
            'created_at': current_time.strftime('%d-%m-%y')
        }

        comments_collections.insert_one(comment)
        data = {"by_user": username, "post_id": post_id, "notification_type": "comment", 'user': userr, 'created_at': date,'seen':False}
        Notification.insert_one(data)
        publish(
        method="comment",
        body={'user':userr},
        )
        

        return Response({'message': 'Post created successfully'}, 
                            status=status.HTTP_201_CREATED)
    

class CreateReplyCommentsAPIView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        parent_comment_id = request.data.get('parent_comment_id')
        parent_username = request.data.get('parendUsername')
        current_time = datetime.now()
        content = f"@{parent_username} {request.data.get('content')}"
        parent_comment = comments_collections.find_one({'_id': ObjectId(parent_comment_id)})
        post_id = parent_comment.get('post_id')
        post = posts_collection.find_one({'_id':ObjectId(post_id)})
        userr = post['username']

        new_comment = {
            'username': username,
            'parent_comment_id': parent_comment_id,
            'parent_username': parent_username,
            'content': content,
            'created_at': current_time.strftime('%d-%m-%y'),
            'post_id': str(post_id),
        }

        result = replied_comment_collections.insert_one(new_comment)
        data = {"by_user": username, "post_id": str(post_id), "notification_type": "comment", 'user': userr, 'created_at': current_time,'seen':False}
        Notification.insert_one(data)
        publish(
        method="comment",
        body={'user':userr},
        )

       

        if result.inserted_id:
            
            return Response({'message': 'Replied comment created successfully'}, status=status.HTTP_201_CREATED)
        else:
            # If insertion fails, return an error response
            return Response({'message': 'Failed to create replied comment'}, status=status.HTTP_400_BAD_REQUEST)
        

class FetchRepliedCommentsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        parent_comment_id = request.GET.get('parent_comment_id')
        # Check if parent_comment_id is valid
        try:
            ObjectId(parent_comment_id)
        except bson.errors.InvalidId:
            return Response({'error': 'Invalid parent_comment_id'}, status=400)
        
        replied_comments = replied_comment_collections.find({'parent_comment_id': parent_comment_id})
        replied_comments_list = list(replied_comments)
        
        # Convert ObjectId to string in the list of comments
        for comment in replied_comments_list:
            comment['_id'] = str(comment['_id'])
        
        return Response({'replied_comments': replied_comments_list}, status=200)
    

class LikeAndCommentsCount(APIView):
    def get(self, request, *args, **kwargs):
        post_id = request.GET.get('post_id')


        try:
            post_likes = likes_collections.find_one({'post_id': ObjectId(post_id)})
            if post_likes and 'users' in post_likes:
            
                likes_count = len(post_likes['users'])
            else:
                likes_count = 0
            
           
            comments_count = comments_collections.count_documents({'post_id': ObjectId(post_id)})
            replied_comments_count = replied_comment_collections.count_documents({'post_id': post_id})

            
            comments_count += replied_comments_count

            return JsonResponse({'likes_count': likes_count, 'comments_count': comments_count})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
class CheckUserLikes(APIView):
    def get(self, request):
        username = request.GET.get('username')
        post_id = request.GET.get('post_id')



        try:
            # Find the document in likes_collections based on post_id
            document = likes_collections.find_one({'post_id': ObjectId(post_id)})
            
            if document and 'users' in document:
                
                user_likes = username in document['users']
                return Response({'user_likes': user_likes})
            else:
                return Response({'error': 'Document or users array not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        

class NotificationCount(APIView):
    def get(self,request, *args, **kwargs):
        username = request.GET.get('username')
        notification = Notification.count_documents({'user':username, 'seen':False})
        return JsonResponse({"notification_count":notification})
    


class AllNotifications(APIView):
    def get(self, request, *args, **kwargs):
        username = request.GET.get('username')

        notifications = list(Notification.find({'user': username}))
        
        # Sort the notifications by 'created_at' in descending order
        notifications.sort(key=lambda x: x['created_at'], reverse=True)

        for notification in notifications:
            notification['_id'] = str(notification['_id'])

        return Response(notifications)

    
class MarkNotificationsAsSeen(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')

        notifications = list(Notification.find({'user': username, 'seen': False}))

        # Update documents to mark them as seen
        for notification in notifications:
            Notification.update_one({'_id': notification['_id']}, {'$set': {'seen': True}})



        # Return a success message or response
        return Response({'message': 'Notifications marked as seen successfully.'})
    

class SavePost(APIView):
    def post(self, request, *args, **kwargs):
        post_id = request.data.get('postId')
        username = request.data.get('username') 


        try:
            existing_document = saved_post.find_one({'username': username})

            if existing_document:
                if post_id in existing_document['posts']:
                    saved_post.update_one({'_id': existing_document['_id']}, {'$pull': {'posts': post_id}})
                    return JsonResponse({'message': 'Post saved successfully'}, status=status.HTTP_200_OK)
                else:
                    
                    saved_post.update_one({'_id': existing_document['_id']}, {'$push': {'posts': post_id}})
                    
                    return JsonResponse({'message': 'Post Unsaved successfully'}, status=status.HTTP_201_CREATED)
            else:
                
                new_save = {
                    'username': username,
                    'posts': [post_id],
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                saved_post.insert_one(new_save)
            
                return JsonResponse({'message': 'Post Saved successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class FetchSavedPosts(APIView):
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')

        try:
            saved_posts = saved_post.find_one({'username': username})
            if saved_posts:
                return JsonResponse({'saved_posts': saved_posts['posts']}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'message': 'No saved posts found for this user'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        



def get_comments(request, post_id):
    comments = comments_collections.find({'post_id': ObjectId(post_id)})
    comments_list = list(comments)
    
    for comment in comments_list:
        for field in comment:
            if isinstance(comment[field], ObjectId):
                comment[field] = str(comment[field])
    

    comments_json = json.dumps(comments_list)
    
    return JsonResponse(comments_json, safe=False)






def get_comments_and_replies(request, post_id):
    comments_cursor = comments_collections.find({'post_id': ObjectId(post_id)})
    comments_list = list(comments_cursor)

    for comment in comments_list:
        for field in comment:
            if isinstance(comment[field], ObjectId):
                comment[field] = str(comment[field])

        replied_comments_cursor = replied_comment_collections.find({'parent_comment_id': comment['_id']})
        replied_comments_list = list(replied_comments_cursor)

        for replied_comment in replied_comments_list:
            replied_comment['_id'] = str(replied_comment['_id'])

            # Fetch messages for each replied comment
            messages_cursor = replied_comment_collections.find({'parent_comment_id': replied_comment['_id']})
            messages_list = list(messages_cursor)

            for message in messages_list:
                message['_id'] = str(message['_id'])

            replied_comment['messages'] = messages_list

        comment['replied_comments'] = replied_comments_list

    comments_json = dumps({'comments': comments_list})
    return Response(comments_json)





    
class CreatePostReport(APIView):

    def post(self, request, *args, **kwargs):
        post_id = request.data.get('post_id')
        reported_by = request.data.get('reported_by')

        if not post_id or not reported_by:
            return Response({"error": "post_id, posted_by, and reported_by are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            existing_document = post_report.find_one({'post_id': post_id})

            if existing_document:
                # Increment the count by 1
                new_count = existing_document.get('count', 0) + 1
                post_report.update_one({'post_id': post_id}, {'$set': {'count': new_count}})
                return Response({"message": "Report count updated successfully."}, status=status.HTTP_200_OK)
            else:
                # If the document doesn't exist, create a new one
                new_document = {
                    'post_id': post_id,
                    # 'posted_by': posted_by,
                    'reported_by': reported_by,
                    'count': 1  # Initialize the count to 1
                }
                post_report.insert_one(new_document)
                return Response({"message": "Report created successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class CreateCommentReport(APIView):

    def post(self, request, *args, **kwargs):
        comment_id = request.data.get('comment_id')
        reported_by = request.data.get('reported_by')

        if not comment_id or not reported_by:
            return Response({"error": "post_id, posted_by, and reported_by are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            existing_document = comment_report.find_one({'comment_id': comment_id})

            if existing_document:
                # Increment the count by 1
                new_count = existing_document.get('count', 0) + 1
                comment_report.update_one({'comment_id': comment_id}, {'$set': {'count': new_count}})
                return Response({"message": "Report count updated successfully."}, status=status.HTTP_200_OK)
            else:
                # If the document doesn't exist, create a new one
                new_document = {
                    'comment_id': comment_id,
                    # 'posted_by': posted_by,
                    'reported_by': reported_by,
                    'count': 1  # Initialize the count to 1
                }
                comment_report.insert_one(new_document)
                return Response({"message": "Report created successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#------------------------------------ ADMIN SIDE --------------------------------------------#



class ListReportedPosts(APIView):

    def get(self, request, *args, **kwargs):
        try:
            reported_posts = post_report.find()
            reported_posts_list = []

            for reported_post in reported_posts:
                # Convert ObjectId to string
                reported_post['_id'] = str(reported_post['_id'])
                
                # Fetch the corresponding post data from posts collection
                post = posts_collection.find_one({'_id': ObjectId(reported_post['post_id'])})
                
                if post:
                    reported_post['posted_by'] = post.get('username')
                    reported_post['image_data'] = post.get('image_data')

                reported_posts_list.append(reported_post)

            return Response(reported_posts_list, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteReportedPost(APIView):

    def delete(self, request, post_id, *args, **kwargs):
        try:
            # Find and delete the reported post using the post_id
            result = post_report.delete_one({'post_id': post_id})
            
            if result.deleted_count == 0:
                return Response({"error": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": "Report deleted successfully."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ListReportedComments(APIView):

    def get(self, request, *args, **kwargs):
        try:
            reported_comments = comment_report.find()
            reported_posts_list = []

            for reported_comment in reported_comments:
                # Convert ObjectId to string
                reported_comment['_id'] = str(reported_comment['_id'])
                
                # Fetch the corresponding post data from posts collection
                post = comments_collections.find_one({'_id': ObjectId(reported_comment['comment_id'])})
                
                if post:
                    reported_comment['posted_by'] = post.get('username')
                    reported_comment['content'] = post.get('content')

                reported_posts_list.append(reported_comment)

            return Response(reported_posts_list, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class DeleteReportedComment(APIView):

    def delete(self, request, comment_id, *args, **kwargs):
        try:

            comment_report.delete_one({'comment_id': str(comment_id)})
        
            
            
            comments_collections.delete_one({'_id': ObjectId(comment_id)})
            
            return Response({"message": "Comment and report deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            print("kld;fjlskadfjklasdfj")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

