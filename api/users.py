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

@bp.route('/get-user-status/<id>')
def getUserStatus(id):

    usr = queryUsers({'_id': id})

    if len(usr):
        usr = usr[0]
        return jsonify({'status': usr['status']})
    else:
        
        return jsonify({'status': 'unavailable'}) 

@bp.route('/get-users')
def getUsers():
    keys = ['firstName', 'lastName', 'email', 'room']
    query = queryFromArgs(keys, request.args)

    return jsonify(queryUsers(query))

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

def changeUserGroup(id, group):
    updateUsers({'_id': id}, {'group': group})

def addUser(user):
    user_col.insert_one(user)

def addUsersDev():
    user_col.delete_many({})
    users = [
        # {
        #   'firstName': "Saiid",
        #   "lastName": "El Hajj Chehade", 
        #   "email": "sae55@mail.aub.edu",
        #   'avatar': {
        #       'index': 0
        #   }
        # },
        {
          'firstName': "Karim",
          "lastName": "El Hajj Chehade", 
          "email": "saidhajjchehade@hotmail.com",
          'avatar': {
              'index': 1
          }
        },
        {
          'firstName': "Nader",
          "lastName": "Zantout", 
          "email": "nwz05@mail.aub.edu",
          'avatar': {
              'index': 1
          }
        },
        {
            'firstName': "Ahmad",
            "lastName": "Zantout",
            "email": "nwzantout@hotmail.com",
            'avatar': {
                'index': 0
            }
        },
        
        ]
     
    for user in users:

        user_obj = user_col.find_one({'firstName': user['firstName']})
        if  user_obj is None:
            user_col.insert_one(user)

    user_col.delete_many({'firstName': "Saiid"}) 

    return "Added"

def removeUser(userId):
    
    user_col.delete_one({'_id': userId})


  

 
def initialize():
    #user_col.delete_many({})
    #addUser()
    pass
 
initialize() 

