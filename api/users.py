from flask import Blueprint, current_app, request, jsonify
from services import mongo
from bson import json_util
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery
import json
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('users', __name__)

db = mongo.get_default_database()

user_col = db['user_collection']

@bp.route('/get-user')
@jwt_required()
def getUser():

    uid = get_jwt_identity()

    return jsonify(queryUsers({'_id': uid})[0]) 

@bp.route('/get-users')
def getUsers():
    keys = ['firstName', 'lastName', 'email']
    query = queryFromArgs(keys, request.args)

    return json_util.dumps(queryUsers(query))

def queryUsers(query):
    query = prepQuery(query, ids = ['_id'])
    resp = []
    for val in user_col.find(query):
        resp.append(val)
    return bsonifyList(resp)

def updateUsers(query, values_to_update):
    query = prepQuery(query, ids = ['_id'])

    newvals  = {'$set': values_to_update}
    user_col.update(query, newvals)

def changeUserRoom(id, room):
    updateUsers({'_id': id}, {'room': room})

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
        {
            'firstName': "Nader",
            "lastName": "Zantout",
            "email": "nwz05@mail.aub.edu"
        },
        
        ]
     
    for user in users:
        user_col.insert_one(user)
    return "Added"

def removeUser(user):
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
        {
            'firstName': "Nader",
            "lastName": "Zantout",
            "email": "nwz05@mail.aub.edu"
        },
        
        ]

    for user in users:
        user_col.insert_one(user)

if (user_col.find_one({'firstName': "Saiid"}) is None):
    initialize()

