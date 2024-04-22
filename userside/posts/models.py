from django.db import models
from monogdb_connections import db


posts_collections = db['Posts']
friendes_collections = db['Friends']


