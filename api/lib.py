from flask import request


class Session:

    def __init__(self, socket, userName, roomName):
        self.id = request.sid
        self.socket = socket
        self.name = userName
        self.roomName = roomName
        self.outgoingMedia = None
        self.incomingMedia = {}
        self.iceCandidateQueue = {}

    def addIceCandidate(self, data, candidate):
        
        if data['name'] == self.name:

            if self.outgoingMedia != None:

                self.outgoingMedia.add_ice_candidate(candidate)
            else:
                self.iceCandidateQueue[data['name']].append({
                        data: data,
                        candidate: candidate
                    })
        else:
            webRtc = self.incomingMedia.get(data['name'], None)

            if webRtc != None:
                webRtc.add_ice_candidate(candidate)
            else:
                self.iceCandidateQueue[data['name']] = self.iceCandidateQueue.get(data['name'], [])
                self.iceCandidateQueue[data['name']].append({'data': data, 'candiate': candidate})
      
                
    def sendMessage(self,data, broadcast=False):
        if self.socket: 
            print(data)
            self.socket.emit('message', data, room=self.roomName, broadcast=broadcast) 
        else: 
            raise Exception('socket is null')

    def setOutgoingMedia(self,outgoingMedia):
        self.outgoingMedia = outgoingMedia

    def setRoomName(self,roomName):
        self.roomName = roomName
         
    def setUserName(self,userName): 
        self.name = userName


class Register:

    def __init__(self):
        self.usersByName = {}
        self.userSessionIds = {}

    def register(self,user):
        self.usersByName[user.name] = user
        self.userSessionIds[user.id]= user

    def unregister(self,name):
        user = self.getByName(name)

        if user:
            del self.usersByName[user.name]
            del self.userSessionIds[user.id]

    def removeByName(self,name):
        user = self.getByName(name)
        if user:
            del self.usersByName[user.name]
            del self.userSessionIds[user.id]

    def getByName(self,name):
        return self.usersByName[name]

    def getById(self,id): 
        return self.userSessionIds[id]