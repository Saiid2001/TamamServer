import uuid
import requests
import os
import msal
import app_config
from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session  # https://pythonhosted.org/Flask-Session
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO, send, join_room, leave_room, rooms
from flask_pymongo import PyMongo
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__)

#config
app.config.from_object(app_config)
app.config['JWT_SECRET_KEY']='thisisunbelievablydumbtohardcodepassword'
app.config['SECRET_KEY'] = "thisisanotherdumbhardcodedpassword"
app.config['MONGO_URI'] = 'mongodb://'+os.environ['MONGODB_USERNAME']+':'+os.environ["MONGODB_PASSWORD"]+'@'+os.environ['MONGODB_HOSTNAME']+':27017/'+os.environ['MONGODB_DATABASE']

#services
Session(app)
jwt = JWTManager(app)
socketio = SocketIO(app)
mongo = PyMongo(app)
db = mongo.db
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

#blueprints 
import auth
import sockets
app.register_blueprint(auth.bp, url_prefix='/authenticate')
app.register_blueprint(sockets.bp, url_prefix='/')

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
     
           
       
        