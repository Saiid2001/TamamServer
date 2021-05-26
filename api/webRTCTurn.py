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

rooms = {}

def socketEvents(socketio):

    @socketio.on('join_call')
    def onJoin(data):

        uid, roomId = data['user'], data['room']

        if roomId in rooms:
            # if the room exists
            rooms[roomId].append(uid)
            emit('call_room_joined', {'room': roomId})
        else:
            # create new room
            rooms[roomId] = [uid]
            join_room(roomId)
            emit('call_room_created', {'room': roomId})



#  // These events are emitted to all the sockets connected to the same room except the sender.
#  socket.on('start_call', (roomId) => {
#    console.log(`Broadcasting start_call event to peers in room ${roomId}`)
#    socket.broadcast.to(roomId).emit('start_call')
#  })
    @socketio.on('start_call')
    def onStartCall(data):
        socketio.emit('start_call', room = data['room'], include_self=False)

#  socket.on('webrtc_offer', (event) => {
#    console.log(`Broadcasting webrtc_offer event to peers in room ${event.roomId}`)
#    socket.broadcast.to(event.roomId).emit('webrtc_offer', event.sdp)
#  })
    @socketio.on('webrtc_offer')
    def onStartCall(data):
        socketio.emit('webrtc_offer',{'sdp': data['sdp']}, room = data['room'], include_self=False)

#  socket.on('webrtc_answer', (event) => {
#    console.log(`Broadcasting webrtc_answer event to peers in room ${event.roomId}`)
#    socket.broadcast.to(event.roomId).emit('webrtc_answer', event.sdp)
#  })
    @socketio.on('webrtc_answer')
    def onStartCall(data):
        socketio.emit('webrtc_answer',{'sdp': data['sdp']}, room = data['room'], include_self=False)

#  socket.on('webrtc_ice_candidate', (event) => {
#    console.log(`Broadcasting webrtc_ice_candidate event to peers in room ${event.roomId}`)
#    socket.broadcast.to(event.roomId).emit('webrtc_ice_candidate', event)
#  })

    @socketio.on('webrtc_ice_candidate')
    def onStartCall(data):
        socketio.emit('webrtc_ice_candidate',data, room = data['room'], include_self=False)

#})