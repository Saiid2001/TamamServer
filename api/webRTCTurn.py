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

def socketEvents(socketio):

    @socketio.on('join-call')
    @jwt_required()
    def onJoin(data):
        uid = get_jwt_identity()
        roomId = data['room']

        if roomId in rooms:
            # if the room exists 
            rooms[roomId].append(uid)
            emit('call-room-joined', {'room': roomId})
        else:
            # create new room
            rooms[roomId] = [uid] 
            join_room(roomId)
            emit('call-room-created', {'room': roomId}) 



#  // These events are emitted to all the sockets connected to the same room except the sender.
#  socket.on('start_call', (roomId) => {
#    console.log(`Broadcasting start_call event to peers in room ${roomId}`)
#    socket.broadcast.to(roomId).emit('start_call')
#  })
    @socketio.on('start-call')
    @jwt_required()
    def onStartCall(data):
        socketio.emit('start-call', room = data['room'], include_self=False)

#  socket.on('webrtc_offer', (event) => {
#    console.log(`Broadcasting webrtc_offer event to peers in room ${event.roomId}`)
#    socket.broadcast.to(event.roomId).emit('webrtc_offer', event.sdp)
#  })
    @socketio.on('webrtc-offer')
    @jwt_required()
    def onOffer(data):
        socketio.emit('webrtc-offer',{ 'sdp': data['sdp']}, room = data['room'], include_self=False)

#  socket.on('webrtc_answer', (event) => {
#    console.log(`Broadcasting webrtc_answer event to peers in room ${event.roomId}`)
#    socket.broadcast.to(event.roomId).emit('webrtc_answer', event.sdp)
#  })
    @socketio.on('webrtc-answer')
    @jwt_required()
    def onAnswer(data):
        socketio.emit('webrtc-answer',{'sdp': data['sdp']}, room = data['room'], include_self=False)

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
    def onCandidate(data): 
        socketio.emit('track-status-changed',data, room = data['room'], include_self=False)

#}) 