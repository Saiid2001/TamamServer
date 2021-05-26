from flask import Blueprint, current_app, request, jsonify
from services import mongo
from bson import json_util
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery
from flask_socketio import join_room, leave_room
from flask_jwt_extended import jwt_required, get_jwt_identity
from users import queryUsers, changeUserRoom, changeUserGroup
import json


bp = Blueprint('rooms', __name__)

db = mongo.get_default_database()

rooms_col = db['rooms_collection']

@bp.route('/get-room/<string:room_id>')
@jwt_required()
def getRoom(room_id):
    return jsonify(queryRooms({'_id': room_id})[0]) 

@bp.route('/get-rooms')
def getRooms():
    keys = ['_id', 'name', 'type', 'maxCapacity']
    query = queryFromArgs(keys, request.args)

    rooms = queryRooms(query)
    
    for i,room in enumerate(rooms):
       
        room['users']= getRoomUsers(room['_id'])

        if 'open' in request.args:
            if len(room['users'])==room['maxCapacity']:
                rooms.pop(i)
            
                 
    return jsonify(rooms)
        

def queryRooms(query):
    query = prepQuery(query, ids = ['_id'])
    resp = []
    for val in rooms_col.find(query):
        resp.append(val)
    return bsonifyList(resp)

def updateRooms(query, values_to_update):
    query = prepQuery(query, ids = ['_id'])
    newvals  = {'$set': values_to_update}
    rooms_col.update(query, newvals)

def getRoomUsers(roomId):
    users = queryUsers({'room': roomId})
    return [u['_id'] for u in users]


def initialize():

    rooms = [

        {
            'name': "Main Gate",
            "type": "social", 
            "maxCapacity": 60
        },
        {
            'name': "Jaffet Upper",
            "type": "social", 
            "maxCapacity": 50
        },
        {
            'name':"Jaffet Library",
            "type": "study", 
            "maxCapacity": 50
        },
        {
            'name':"BDH",
            "type": "social", 
            "maxCapacity": 30
        }
        ]

    for room in rooms:
        rooms_col.insert_one(room)

if (rooms_col.find_one({'name': "Jaffet Upper"}) is None):
    initialize()


def leave(userid, socketio):
    user = queryUsers({'_id':userid})[0]
    room = user['room']
    leave_room(room)
    changeUserRoom(userid, 'NONE') 
    socketio.emit('user-left-room', {'user': userid},room = room, include_self=False)



def socketevents(socketio):

    @socketio.on('join')
    @jwt_required()
    def on_join(data):
        userid = get_jwt_identity()
        user = queryUsers({'_id':userid})[0]
        room = data['room']

        users_in_room = queryUsers({'room': room})

        if queryRooms({'_id': room})[0]['maxCapacity'] == len(users_in_room):
            return "Cannot Join: Room Full!"
            
        
        changeUserRoom(userid, room)
        
        
        join_room(room)  
        socketio.emit('user-joined-room', {'user': user}, room = room, include_self=False) 
        return users_in_room

    @socketio.on('join-group')
    @jwt_required()
    def on_join_group(data):
        userid = get_jwt_identity()
        user = queryUsers({'_id':userid})[0]
        join_room(data['group'])
        changeUserGroup(userid, data['group'])
        socketio.emit('user-joined-group', {'user': userid, 'group': data['group']}, room = user['room'], include_self=False) 

    @socketio.on('leave-group')
    @jwt_required()
    def on_leave_group():
        userid = get_jwt_identity()
        user = queryUsers({'_id':userid})[0]
        group = user['group']
        leave_room(group)
        changeUserGroup(userid, "NONE")
        socketio.emit('user-joined-group', {'user': userid, 'group': group}, room = user['room'], include_self=False) 
           
    @socketio.on('leave')
    @jwt_required()
    def on_leave():   
        userid = get_jwt_identity()
        return leave(userid, socketio)
 