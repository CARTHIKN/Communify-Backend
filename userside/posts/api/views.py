from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from monogdb_connections import db
from bson.json_util import dumps 
import base64
import json
from django.core.files.uploadedfile import InMemoryUploadedFile
from bson import ObjectId
from datetime import datetime
from posts.models import friendes_collections

posts_collection = db['Posts']



class CreatePostAPIView(APIView):
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
        print(username)

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
            print("haeii")

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
        print("fakldfjlksd")
        return Response({'message': 'Friend removed successfully'}, status=status.HTTP_200_OK)



class CheckFollowingAPIView(APIView):
    def get(self, request, username, friend_username):
        print("hello")
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
        print(post_id)

       
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
