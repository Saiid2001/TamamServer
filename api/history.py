from flask import Blueprint, current_app, request, jsonify
from flask.helpers import make_response
from services import mongo
from bson import json_util
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery, objectId
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
import users
from datetime import datetime as dt

MAX_NUM_ROOM_LOGGED = 5

bp = Blueprint('history', __name__)

db = mongo.get_default_database()

room_visits_collection = db['room_visits_collection']

def logRoomVisit(userId,roomId):

    prev_visits = list(room_visits_collection.find(prepQuery({'user':userId}, ['user'])))
    today = dt.now()

    if len(prev_visits) == 0:
        prev_user_visit = {'user': objectId(userId), 'rooms':{roomId: today.isoformat()}}
        return room_visits_collection.insert_one(prev_user_visit)
    else:
        prev_user_visit = prev_visits[0]
        

        if roomId not in prev_user_visit['rooms']:
            if len(prev_user_visit['rooms']) == MAX_NUM_ROOM_LOGGED:

                room_visits_list = prev_user_visit['rooms'].items()
                oldest_room_visit = min(room_visits_list, key= lambda x: dt.fromisoformat(x[1]))
                del prev_user_visit['rooms'][oldest_room_visit[0]]

        prev_user_visit['rooms'][roomId] = today.isoformat()
        del prev_user_visit['user']

        return room_visits_collection.update_many({'user':objectId(userId)}, { '$set': {'rooms': prev_user_visit['rooms']} })
    
@bp.route('/rooms/<user_id>')
def getRoomVisits(user_id):

    prev_visits = list(room_visits_collection.find(prepQuery({'user':user_id}, ['user'])))

    if len(prev_visits):

        output = []
        sorted_visits = sorted(prev_visits[0]['rooms'].items(), key= lambda x: dt.fromisoformat(x[1]))
        for room_id, time in sorted_visits:
            output.append({'room': room_id, 'last_access_time':time})
        return jsonify(output)
    else:
        return jsonify([])