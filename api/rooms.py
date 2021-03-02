from flask_socketio import join_room
from flask_jwt_extended import jwt_required, get_jwt_identity
from users import queryUsers, changeUserRoom
import json

def socketevents(socketio):

    @socketio.on('join')
    @jwt_required()
    def on_join(data):
        userid = get_jwt_identity()
        print(userid)
        print(queryUsers({}))
        user = queryUsers({'_id':userid})[0]
        room = data['room']
        users_in_room = queryUsers({'room': room})
        changeUserRoom(userid, room)
        join_room(room)  
        socketio.emit('user-joined-room', {'user': user}, room = room, include_self=False) 
        return users_in_room
          