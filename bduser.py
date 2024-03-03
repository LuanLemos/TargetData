# Criação de usuário
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['accounts']
collection = db['users']
