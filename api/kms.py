import pyforkurento
import os
from lib import Session, Register
from flask import request
from flask_socketio import join_room, leave_room

kmsClient = None
#kmsClient = client.KurentoClient('ws://tamam-mcu:8888/kurento')
userRegister =  Register()
rooms = {}  

def getClient(callback):
    global kmsClient
    if kmsClient != None: 
        return callback(None, kmsClient)
        
    try:
        kmsClient = pyforkurento.client.KurentoClient('ws://tamam-mcu:8888/kurento')
        print('Created client')
        return callback(None, kmsClient)
    except Exception as e:
        print(e)
        return callback(f'Could not connect to KMS server:{e}', None)
      
     
def getRoom(roomName, callback):

    room = rooms.get(roomName, None)
    print(roomName)
    join_room(roomName)
    if room == None:
        print('Create a new room: ', roomName)
        
        def __atGetClient(err, client):
            if err:
                return callback(err, None)
                
            try:
                pipeline = client.create_media_pipeline()
                room = { 
                    'name': roomName, 
                    'pipeline': pipeline, 
                    'participants':{}, 
                    'kurentoClient': client
                    }

                
                
                rooms[roomName] = room
                callback(None, room)

            except Exception as e: 
                return callback(e, None) 

        getClient(__atGetClient)

    #if there is a room
    else:
        print('get existing room: ', roomName)
        callback(None, room)
    

def join(socket, room, userName, callback):
    
    userSession = Session(socket,  userName, room['name'])

    userRegister.register(userSession);
     
    try:
        outgoingMedia = room['pipeline'].add_endpoint('WebRtcEndpoint')

        userSession.setOutgoingMedia(outgoingMedia)

        iceCandidateQueue = userSession.iceCandidateQueue.get(userSession.name,None)

        if iceCandidateQueue != None:
            while len(iceCandidateQueue):
                message = iceCandidateQueue.pop(0) 
                print('user: ',userSession.name,'collect candidate for outgoing media')
                userSession.outgoingMedia.addIceCandidate(message.candidate)

        def __onIceCandidate(resp):
            candidate = resp['payload']['candidate']
            userSession.sendMessage({
                    'id': 'iceCandidate',
                    'name': userSession.name,
                    'candidate': candidate
                }, broadcast=True) 
        
            
        userSession.outgoingMedia.add_event_listener('OnIceCandidate', __onIceCandidate)

        usersInRoom = room['participants']
        print(usersInRoom.keys())

        for username in usersInRoom:
            user = usersInRoom[username]
            if username != userSession.name:
                user.sendMessage({
                        'id': "newParticipantArrived",
                        'name': userSession.name
                    }, broadcast=True)

        existingUsers = []

        for user in usersInRoom:
            user = usersInRoom[username]
            if username != userSession.name:
                existingUsers.append(username) 

        userSession.sendMessage({
                'id': 'existingParticipants',
                'data': existingUsers,
                'roomName': room['name']
            }, broadcast=True)
         
        room['participants'][userSession.name] = userSession

        callback(None, userSession)

    except Exception as e:
        print('no participant in room')
        if len(room['participants'])==0:
            room['pipeline'].dispose()

        return callback(e, None)


def joinRoom(socket, data, callback):
    def __atGetRoom(error, room):
        if error:
            callback(error, None)
            return

        def __atJoin(error, user):
          
            if error:
                callback(error, None) 
                return 
            

            print('join success: ', user.name)
            callback(None, None)

        join(socket, room, data['name'], __atJoin)

    getRoom(data['roomName'], __atGetRoom )

def receiveVideoFrom(socket, senderName, sdpOffer, callback):
    print('need to recieve video from ', senderName)
    userSession = userRegister.getById(request.sid)
    sender = userRegister.getByName(senderName)

    def __atGetEndpointForUser(error, endpoint):
        if error:
            print(error)
            callback(error,None)
        
        try:
            sdpAnswer = endpoint.process_offer(sdpOffer) 
            data = {
                    'id': 'receiveVideoAnswer', 
                    'name':sender.name,
                    'sdpAnswer': sdpAnswer
                }
            print('got sdp answer on video request from ', sender.name)
            userSession.sendMessage(data, broadcast = True)
            try:
                endpoint.gather_ice_candidates()
                return callback(None, sdpAnswer)

            except Exception as e: 
                return callback(e,None) 

        except Exception as e:
            return callback(e, None)

    getEndpointForUser(userSession, sender, __atGetEndpointForUser)
      
 
def leaveRoom(socket, callback): 
    print('leaving room')
    
    userSession = userRegister.getById(request.sid)

    if userSession == None:
        return

    room = rooms.get(userSession.roomName, None)
     
    if room == None:
        return
    print(room['name'])
    leave_room(room['name'])

    usersInRoom = room['participants']
    del usersInRoom[userSession.name]
    #userSession.outgoingMedia.dispose()
     
    for i in range(len(userSession.incomingMedia)):
        #userSession.incomingMedia[i].dispose()
        del userSession.incomingMedia[i]

    data = {
            'id': "participantLeft", 
            'name': userSession.name
        }

    for username in usersInRoom:
        user = usersInRoom[username]
        #user.incomingMedia[userSession.name].dispose()
        if userSession.name in usersInRoom:
            del user.incomingMedia[userSession.name]
        user.sendMessage(data,  broadcast=True)

    if len(room['participants'])==0:

        room['pipeline'].dispose();
        del rooms[userSession.roomName]

    del userSession.roomName

def addIceCandidate(socket, data, callback): 
    print('adding candidate', data)
    user = userRegister.getById(request.sid)
    if user != None: 
        candidate = data['candidate']
        user.addIceCandidate(data, candidate)
        callback(None, None)

    else:
        callback( Exception('addIceCandidate failed'), None)
         
def getEndpointForUser(userSession, sender, callback): 
    print('getting endpoint of ', sender.name)
    if userSession.name == sender.name:
        return callback(None, userSession.outgoingMedia) 

    incoming = userSession.incomingMedia.get(sender.name, None)

    if incoming == None:
        def __atGetRoom(error, room):
            if error:
                callback(error, None)
                return
            try:
                incoming = room['pipeline'].add_endpoint('WebRtcEndpoint')
                userSession.incomingMedia[sender.name] = incoming

                iceCandidateQueue = userSession.iceCandidateQueue.get(sender.name, None)

                if iceCandidateQueue != None: 
                    while len(iceCandidateQueue):
                        message = iceCandidateQueue.pop(0)  
                        print('ice message') 
                        print(message)

                        incoming.add_ice_candidate(message['data']['candidate'])

                def __onIceCandidate(resp):
                    candidate = resp['payload']['candidate']
                    userSession.sendMessage({
                            'id': 'iceCandidate', 
                            'name': sender.name,
                            'candidate': candidate
                        }, broadcast=True) 

                incoming.add_event_listener('OnIceCandidate', __onIceCandidate)
                
                try:
                    sender.outgoingMedia.connect(incoming)
                    callback(None, incoming)
                except Exception as e:
                    callback(e, None)

            except Exception as e:
                if len(room['participants']) == 0:
                    room['pipeline'].dispose()
                callback(e, None)
                return

        getRoom(userSession.roomName, __atGetRoom)
    else:
        try:
            sender.outgoingMedia.connect(incoming)
        except Exception as e:
            callback(e, None)
             
 
import json
def socketEvents(socket):

     
    def _err(err, red):
        if err:
            raise Exception(err) 
    @socket.on('message')
    def message(data):  
            
        data = json.loads(data)
          
        if data['id'] == 'joinRoom':
            joinRoom(socket, data, _err)
            return   
        if data['id'] =='receiveVideoFrom':
            print('got message receive video from')
            receiveVideoFrom(socket, data['sender'], data['sdpOffer'], _err)
            return
        if data['id'] == 'leaveRoom':
            leaveRoom(socket, _err)
            return
        if data['id'] == 'onIceCandidate':
            addIceCandidate(socket, data, _err)
            return  

        return 

                         