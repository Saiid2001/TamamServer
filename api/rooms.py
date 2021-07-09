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
            "maxCapacity": 60,
            'mapInfo': {
                'pos': {
                    'x': 1120,
                    'y': 915
                },
                'layer': 0
            }
        },
        {
            'name': "Jaffet Upper",
            "type": "social", 
            "maxCapacity": 50,
            'layout': {
                'background':{
                    'type': 'tile',
                    'id': 'tile_white_1'
                },

                'objects': {

                    'tables': [
                        { "id": 0, "capacity": 6, "position": { "x": 400, "y": 100 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 1, "capacity": 6, "position": { "x": 400, "y": 500 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 2, "capacity": 6, "position": { "x": 400, "y": 900 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 3, "capacity": 6, "position": { "x": 900, "y": 100 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 4, "capacity": 6, "position": { "x": 900, "y": 500 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 5, "capacity": 6, "position": { "x": 900, "y": 900 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 6, "capacity": 6, "position": { "x": 2000, "y": 100 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 7, "capacity": 6, "position": { "x": 2000, "y": 500 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 8, "capacity": 6, "position": { "x": 2000, "y": 900 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 9, "capacity": 6, "position": { "x": 2500, "y": 100 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 10, "capacity": 6, "position": { "x": 2500, "y": 500 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 11, "capacity": 6, "position": { "x": 2500, "y": 900 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}
                    ],
                    'desks': [
                        
                    ]
                }
            },
            'thumbnail':{
                'isLocal': True,
                'id': 'jaffet_upper'
            },
            'mapInfo': {
                'pos': {
                    'x': 1142,
                    'y': 740
                },
                'layer': 1
            }
        },
        {
            'name':"Jaffet Library",
            "type": "study", 
            "maxCapacity": 50,
            'layout': {
                'background':{
                    'type': 'tile',
                    'id': 'tile_white_1',

                },

                'objects': {

                    'tables': [
                        
                    ],
                    'desks': [
                        { "id": 0, "capacity": 1, "position": { "x": 400, "y": 100 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 1, "capacity": 1, "position": { "x": 400, "y": 310 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  }, 
                        { "id": 2, "capacity": 1, "position": { "x": 400, "y": 520 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  }, 
                        { "id": 3, "capacity": 1, "position": { "x": 400, "y": 770 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },
                        { "id": 4, "capacity": 1, "position": { "x": 400, "y": 980 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },  
                        { "id": 5, "capacity": 1, "position": { "x": 400, "y": 1190 , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} } },  

                        { "id": 7, "capacity": 1, "position": { "x": 800, "y": 100 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  }, 
                        { "id": 8, "capacity": 1, "position": { "x": 800, "y": 310 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  }, 
                        { "id": 9, "capacity": 1, "position": { "x": 800, "y": 520 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  }, 
                        { "id": 10, "capacity": 1, "position": { "x": 800, "y": 770 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} },
                        { "id": 11, "capacity": 1, "position": { "x": 800, "y": 980 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },  
                        { "id": 12, "capacity": 1, "position": { "x": 800, "y": 1190 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },  

                        { "id": 13, "capacity": 1, "position": { "x": 1200, "y": 100 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  }, 
                        { "id": 14, "capacity": 1, "position": { "x": 1200, "y": 310 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 15, "capacity": 1, "position": { "x": 1200, "y": 520 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 16, "capacity": 1, "position": { "x": 1200, "y": 770 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },
                        { "id": 17, "capacity": 1, "position": { "x": 1200, "y": 980 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },  
                        { "id": 18, "capacity": 1, "position": { "x": 1200, "y": 1190 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },  

                        { "id": 19, "capacity": 1, "position": { "x": 1600, "y": 100 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 20, "capacity": 1, "position": { "x": 1600, "y": 310 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 21, "capacity": 1, "position": { "x": 1600, "y": 520 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 22, "capacity": 1, "position": { "x": 1600, "y": 770 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} },
                        { "id": 23, "capacity": 1, "position": { "x": 1600, "y": 980 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },  
                        { "id": 24, "capacity": 1, "position": { "x": 1600, "y": 1190 }, 'style':{'isLocal': True, 'id': 'desk_jafet_right'}  },  

                        { "id": 25, "capacity": 1, "position": { "x": 2000, "y": 100 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 26, "capacity": 1, "position": { "x": 2000, "y": 310 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 27, "capacity": 1, "position": { "x": 2000, "y": 520 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 28, "capacity": 1, "position": { "x": 2000, "y": 770 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} },
                        { "id": 29, "capacity": 1, "position": { "x": 2000, "y": 980 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} },  
                        { "id": 30, "capacity": 1, "position": { "x": 2000, "y": 1190 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} },  

                        { "id": 31, "capacity": 1, "position": { "x": 2400, "y": 100 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 32, "capacity": 1, "position": { "x": 2400, "y": 310 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 33, "capacity": 1, "position": { "x": 2400, "y": 520 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} }, 
                        { "id": 34, "capacity": 1, "position": { "x": 2400, "y": 770 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} },
                        { "id": 35, "capacity": 1, "position": { "x": 2400, "y": 980 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} },  
                        { "id": 36, "capacity": 1, "position": { "x": 2400, "y": 1190 } , 'style':{'isLocal': True, 'id': 'desk_jafet_right'} },
                    ]
                }
            },
            'thumbnail':{
                'isLocal': True,
                'id': 'jaffet_library'
            },
            'mapInfo': {
                'pos': {
                    'x': 1149,
                    'y': 763
                },
                'layer': 0
            }
        },
        {
            'name':"BDH",
            "type": "social", 
            "maxCapacity": 30,
            'layout': {
                'background':{
                    'type': 'tile',
                    'id': 'tile_black_1'
                },
                'objects':{
                    'tables':[
                        { "id": 0, "capacity": 6, "position": { "x": 400, "y": 100 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 1, "capacity": 6, "position": { "x": 400, "y": 400 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 2, "capacity": 6, "position": { "x": 400, "y": 700 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        
                        { "id": 3, "capacity": 6, "position": { "x": 800, "y": 100 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 4, "capacity": 6, "position": { "x": 800, "y": 400 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 5, "capacity": 6, "position": { "x": 800, "y": 700 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 

                        { "id": 6, "capacity": 6, "position": { "x": 1200, "y": 100 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 7, "capacity": 6, "position": { "x": 1200, "y": 400 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 8, "capacity": 6, "position": { "x": 1200, "y": 700 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        
                        { "id": 9, "capacity": 6, "position": { "x": 1600, "y": 100 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 10, "capacity": 6, "position": { "x": 1600, "y": 400 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                        { "id": 11, "capacity": 6, "position": { "x": 1600, "y": 700 } ,'style':{'isLocal': True, 'id': 'table_jafet_right'}}, 
                    ],
                    'static':[
                        { "id": 0, "position": { "x": 400, "y": 300 } ,'style':{'isLocal': True, 'id': 'bush_1'}},
                        { "id": 1, "position": { "x": 400, "y": 600 } ,'style':{'isLocal': True, 'id': 'bush_1'}},

                        { "id": 2, "position": { "x": 800, "y": 300 } ,'style':{'isLocal': True, 'id': 'bush_1'}},
                        { "id": 3, "position": { "x": 800, "y": 600 } ,'style':{'isLocal': True, 'id': 'bush_1'}},

                        { "id": 4, "position": { "x": 1200, "y": 300 } ,'style':{'isLocal': True, 'id': 'bush_1'}},
                        { "id": 5, "position": { "x": 1200, "y": 600 } ,'style':{'isLocal': True, 'id': 'bush_1'}},

                        { "id": 6, "position": { "x": 1600, "y": 300 } ,'style':{'isLocal': True, 'id': 'bush_1'}},
                        { "id": 7, "position": { "x": 1600, "y": 600 } ,'style':{'isLocal': True, 'id': 'bush_1'}},
                    ]
                }
            },
            'thumbnail':{
                'isLocal': True,
                'id': 'bdh'
            },
            'mapInfo': {
                'pos': {
                    'x': 1130,
                    'y': 583
                },
                'layer': 0
            }
        }
        ]
    #rooms_col.delete_many({})
    for room in rooms:

        room_obj = rooms_col.find_one({'name': room['name']})
        if (room_obj is None):
            rooms_col.insert_one(room)
        else:
            if room_obj['name'] == "None":
                rooms_col.update({'_id': room_obj['_id']}, {'$set': {'layout': room['layout'], 'thumbnail': room['thumbnail']}}) 


initialize()


def leave(userid, socketio):

    user = queryUsers({'_id':userid})[0]
    room = user['room']
    group = user['group']
    leave_room(group)
    rtc.onLeave(user,room+"-"+group)
    leave_room(room+"-"+group) 
    leave_room(room)
    changeUserRoom(userid, 'NONE') 
    socketio.emit('user-left-room', {'user': userid},room = room, include_self=True)
    if room != "map":
        socketio.emit('user-left-room-to-map', {'user': user, 'room': room}, room = "map", include_self = False)


import webRTCTurn as rtc

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
        socketio.emit('user-joined-room-to-map', {'user': user, 'room': room}, room = "map", include_self=False)

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
        room = user['room']
        leave_room(group)
        rtc.onLeave(user,room+"-"+group)
        leave_room(room+"-"+group)
        changeUserGroup(userid, "NONE")
        socketio.emit('user-left-group', {'user': userid, 'group': group}, room = user['room'], include_self=False) 
           
    @socketio.on('leave')
    @jwt_required()
    def on_leave():   
        userid = get_jwt_identity()
        return leave(userid, socketio)


    @socketio.on('enter-map')
    @jwt_required()
    def on_enter_map():
        userid = get_jwt_identity()
        user = queryUsers({'_id': userid})[0]
        room = "map"

        changeUserRoom(userid, room)

        join_room(room)
        socketio.emit('user-joined-room', {'user': user}, room=room, include_self=False)
