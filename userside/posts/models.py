from django.db import models
from monogdb_connections import db


posts_collections = db['Posts']
friendes_collections = db['Friends']
likes_collections = db['Likes']
comments_collections = db['Comments']
replied_comment_collections = db['RepliedComments']
Notification = db['Notification']
saved_post = db['SavedPost']



