#io.on('connection', (socket) => {
#  socket.on('join', (roomId) => {
#    const roomClients = io.sockets.adapter.rooms[roomId] || { length: 0 }
#    const numberOfClients = roomClients.length



#    // These events are emitted only to the sender socket.
#    if (numberOfClients == 0) {
#      console.log(`Creating room ${roomId} and emitting room_created socket event`)
#      socket.join(roomId)
#      socket.emit('room_created', roomId)
#    } else if (numberOfClients == 1) {
#      console.log(`Joining room ${roomId} and emitting room_joined socket event`)
#      socket.join(roomId)
#      socket.emit('room_joined', roomId)
#    } else {
#      console.log(`Can't join room ${roomId}, emitting full_room socket event`)
#      socket.emit('full_room', roomId)
#    }
#  })

from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import jwt_required, get_jwt_identity

rooms = {}

def onLeave(user, room):

    rooms[room].remove(user)
    if len(room[room]) ==0:
        del rooms[room]

def socketEvents(socketio):

    @socketio.on('join-call')
    @jwt_required()
    def onJoin(data):
        uid = get_jwt_identity()
        roomId = data['room']
        join_room(roomId)

        if roomId in rooms:
            # if the room exists 
            rooms[roomId].append(uid)
            emit('call-room-joined', {'room': roomId})
        else:
            # create new room
            rooms[roomId] = [uid] 
            emit('call-room-created', {'room': roomId}) 
 
             

#  // These events are emitted to all the sockets connected to the same room except the sender.
#  socket.on('start_call', (roomId) => {
#    console.log(`Broadcasting start_call event to peers in room ${roomId}`)
#    socket.broadcast.to(roomId).emit('start_call')
#  })
    @socketio.on('start-call')
    @jwt_required() 
    def onStartCall(data):
        socketio.emit('start-call',{'user': data['user']}, room = data['room'], include_self=False) 

#  socket.on('webrtc_offer', (event) => {
#    console.log(`Broadcasting webrtc_offer event to peers in room ${event.roomId}`)
#    socket.broadcast.to(event.roomId).emit('webrtc_offer', event.sdp)
#  })
    @socketio.on('webrtc-offer') 
    @jwt_required()
    def onOffer(data):
        socketio.emit('webrtc-offer',{ 'user':data['user'], 'sdp': data['sdp']}, room = data['room'], include_self=False)

#  socket.on('webrtc_answer', (event) => {
#    console.log(`Broadcasting webrtc_answer event to peers in room ${event.roomId}`)
#    socket.broadcast.to(event.roomId).emit('webrtc_answer', event.sdp)
#  })
    @socketio.on('webrtc-answer')
    @jwt_required() 
    def onAnswer(data):
        socketio.emit('webrtc-answer',{'user':data['user'],'sdp': data['sdp']}, room = data['room'], include_self=False)

#  socket.on('webrtc_ice_candidate', (event) => {
#    console.log(`Broadcasting webrtc_ice_candidate event to peers in room ${event.roomId}`)
#    socket.broadcast.to(event.roomId).emit('webrtc_ice_candidate', event)
#  })

    @socketio.on('webrtc-ice-candidate')
    @jwt_required()
    def onCandidate(data):
        socketio.emit('webrtc-ice-candidate',data, room = data['room'], include_self=False)

    @socketio.on('track-status-changed')
    @jwt_required()
    def statusChanged(data): 
        socketio.emit('track-status-changed',data, room = data['room'], include_self=False)


    @socketio.on('waving-to-group')
    def onWave(data):
        socketio.emit('waving-to-group', {'user':data['user']}, room = data['room'], include_self= False)
    
    @socketio.on('accepted-to-group')
    def onAcceptWave(data):
        socketio.emit('accepted-to-group', {'room':data['room']}, room = data['user'], include_self= False)

    @socketio.on('rejected-from-group')
    def onAcceptWave(data):
        socketio.emit('rejected-from-group', {'room':data['room']}, room = data['user'], include_self= False)

    @socketio.on('canceled-waving')
    def onAcceptWave(data):
        socketio.emit('canceled-waving', {'user':data['user']}, room = data['room'], include_self= False) 
    
#})  