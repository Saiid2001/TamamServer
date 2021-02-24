from flask import Blueprint, current_app
from mongo import mongo

bp = Blueprint('users', __name__)

db = mongo.db

user_col = db['user_collection']
print(user_col)

@bp.route('/get-user')
def getUser():
    pass

@bp.route('/add-user')
def addUser():
    users = [
        {
          'firstName': "Saiid",
          "lastName": "El Hajj Chehade", 
          "email": "sae55@mail.aub.edu"
        },
        {
          'firstName': "Karim",
          "lastName": "El Hajj Chehade", 
          "email": "saidhajjchehade@hotmail.com"
        },
        
        ]
     
    for user in users:
        user_col.insert_one(user)
    return "Added"

def removeUser(user):
    pass

@bp.route('/get-users')
def getUsers():
    pass
  

 
def initialize():

    users = [
        {
          'firstName': "Saiid",
          "lastName": "El Hajj Chehade", 
          "email": "sae55@mail.aub.edu"
        },
        {
          'firstName': "Karim",
          "lastName": "El Hajj Chehade", 
          "email": "saidhajjchehade@hotmail.com"
        },
        
        ]

    for user in users:
        user_col.insert_one(user)

if __name__ == "__main__":
    if (user_col.find_one({'firstName': "Saiid"}) is None):
        initialize()

