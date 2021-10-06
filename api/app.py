from flask.json import jsonify
from gevent import monkey
monkey.patch_all()

import uuid
import logging
import config
import requests
import os
import datetime 
import json
import msal
import app_config
from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session  # https://pythonhosted.org/Flask-Session
from flask_jwt_extended import JWTManager, verify_jwt_in_request,jwt_required, get_jwt_identity
from flask_socketio import SocketIO, send, join_room, leave_room,ConnectionRefusedError
from werkzeug.middleware.proxy_fix import ProxyFix
from pymongo import MongoClient
from services import mongo 
from flask_mail import Mail,Message

app = Flask(__name__)

#logging 
logging.basicConfig(level=logging.DEBUG, 
                    format='[%(asctime)s]: {} %(levelname)s %(message)s'.format(os.getpid()),
                    datefmt="%Y-%m-%d %H:%M:%S",
                    handlers=[logging.StreamHandler()])

logger = logging.getLogger()

#config
app.config.from_object(app_config)
app.config['JWT_SECRET_KEY']='thisisunbelievablydumbtohardcodepassword'
app.config['SECRET_KEY'] = "thisisanotherdumbhardcodedpassword"
app.config['MONGO_URI'] = 'mongodb://'+os.environ['MONGODB_USERNAME']+':'+os.environ["MONGODB_PASSWORD"]+'@'+os.environ['MONGODB_HOSTNAME']+':27017/'+os.environ['MONGODB_DATABASE']
app.config['JWT_ACCESS_TOKEN_EXPIRES']=datetime.timedelta(days=7)
app.config['JWT_REFRESH_TOKEN_EXPIRES']=datetime.timedelta(days=100)

#services
Session(app)
jwt = JWTManager(app)
socketio = SocketIO(app)
mongo.__init__(app.config['MONGO_URI'])
 
#blueprints 
import auth
import sockets
import users
import rooms  
import relations
import history
import courses
from utils import _load_cache, _build_msal_app, _save_cache
app.register_blueprint(auth.bp, url_prefix='/authenticate')
app.register_blueprint(sockets.bp, url_prefix='/')
app.register_blueprint(users.bp, url_prefix='/users')
app.register_blueprint(rooms.bp, url_prefix='/rooms')
app.register_blueprint(relations.bp, url_prefix='/relations')
app.register_blueprint(history.bp, url_prefix = '/history')
app.register_blueprint(courses.bp, url_prefix = '/courses')

@app.route('/')  
def home():
    return "Tamam Server running..." 
    ##return json.dumps(dir(mongo))


@app.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            return result
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return auth.check_user(session['user'])

@app.route("/getAToken-dev")  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized_dev():

    return auth.check_user({'preferred_username': request.args['email']})

@socketio.on('connect')
def connect():
    #to authenticate the user before connecting the socket 
    try:
        token = verify_jwt_in_request()
        userid = get_jwt_identity()
        join_room(userid)
        if len(users.queryUsers({'_id': userid})) > 0:
            users.changeOnlineStatus(userid, 'online')
    except Exception as exp:
        print(exp)   
        raise ConnectionRefusedError('unauthorized!')

@socketio.on('disconnect')
@jwt_required()
def disconnect():
    userid = get_jwt_identity()
    rooms.leave(userid, socketio)
    if len(users.queryUsers({'_id': userid})) > 0:
        print("bravo 6 going dark")
        users.changeOnlineStatus(userid, 'offline')
      

rooms.socketevents(socketio)
relations.socketevents(socketio)


#import kms
def emptyCallback(*args):
    pass

#kms.getClient(emptyCallback) 
#kms.socketEvents(socketio)
  

import webRTCTurn   

webRTCTurn.socketEvents(socketio)

def run_app(_app):
    socketio.run(_app, host='0.0.0.0', port=5000, debug=True)
if __name__=="__main__":    
    logger.info(f'Starting app in {config.APP_ENV} environment')
    run_app(app)

    
       


    
     
           
       
            