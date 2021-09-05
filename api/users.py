from flask import Blueprint, current_app, request, jsonify, make_response
from services import mongo
from bson import json_util
from bson.objectid import ObjectId
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
import urllib.parse as parseURI
from pymongo import ASCENDING, DESCENDING, TEXT

bp = Blueprint('users', __name__)

db = mongo.get_default_database()

user_col = db['user_collection']

user_col.create_index([('firstName', TEXT), ('lastName', TEXT), ('major', TEXT), ('enrollY', TEXT), ('gradY', TEXT), ('group', TEXT)])

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
    keys = ['firstName', 'lastName', 'email', 'room', 'major', 'group', 'enrollY', '_id']
    query = queryFromArgs(keys, request.args)

    return jsonify(queryUsers(query))

@bp.route('/search-users')
@jwt_required()
def searchUsers():

    uid = get_jwt_identity()
    print("uid:", type(uid))
    if 'search' not in request.args and 'advanced-search' not in request.args:
        return make_response("Search query not found", 403)
    query = {}
    resp = []
    argKeys = ['firstName', 'lastName', 'major', 'enrollY', 'gradY']
    if 'search' in request.args:
        searchString = parseURI.unquote(request.args['search']).replace(' ', '|')
        queryList = []
        for key in argKeys:
            queryList.append( { key : { "$regex" : searchString, "$options" : "i"} } )
        query = {"$and": [{'_id': {'$ne': ObjectId(uid)}}, {'onlineStatus': 'online'}, {"$or": queryList}]}
        #query = {"$text": { "$search": searchString }}
    else:
        pass

    resp = queryUsers(query)
    return jsonify(bsonifyList(resp))

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

def changeOnlineStatus(id, newStatus):
    updateUsers({'_id':id}, {'onlineStatus': newStatus})

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
    query = prepQuery({'_id': userId}, ['_id'])
    user_col.delete_many(query)

 
def initialize():
    #user_col.delete_many({})
    #addUser()
    pass
 
initialize()  
 
