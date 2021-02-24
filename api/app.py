from flask import Flask
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, send, join_room, leave_room, rooms
import os
from mongo import mongo


app = Flask(__name__)

#config
app.config['JWT_SECRET_KEY']='thisisunbelievablydumbtohardcodepassword'
app.config['SECRET_KEY'] = "thisisanotherdumbhardcodedpassword"
app.config['MONGO_URI'] = 'mongodb://'+os.environ['MONGODB_USERNAME']+':'+os.environ["MONGODB_PASSWORD"]+'@'+os.environ['MONGODB_HOSTNAME']+':27017/'+os.environ['MONGODB_DATABASE']

#services
jwt = JWTManager(app)
socketio = SocketIO(app)
mongo.init_app(app)


#blueprints 
import auth
import sockets
import users
app.register_blueprint(auth.bp, url_prefix='/authenticate')
app.register_blueprint(sockets.bp, url_prefix='/')
app.register_blueprint(users.bp, url_prefix='/users')

@app.route('/')
def home():
    return "Tamam Server running..."

@socketio.on('message')
def handle_message(msg): 
     print(msg)
     socketio.send(msg) 


@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room) 
    print(rooms) 
    socketio.emit('user-joined-room', data, room = room)

if __name__=="__main__":
    socketio.run(app, host='0.0.0.0', port=4000, debug=True)
     
           
       
        