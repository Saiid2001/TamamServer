from flask import Blueprint, current_app, request, jsonify
from flask.helpers import make_response
from services import mongo
from bson import json_util
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery, objectId
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
import users
from datetime import datetime as dt

MAX_NUM_ROOM_LOGGED = 50


bp = Blueprint('history', __name__)

db = mongo.get_default_database()

room_visits_collection = db['room_visits_collection']

def reset():
    room_visits_collection.delete_many({})

def logRoomVisit(userId,roomId):

    prev_visits = list(room_visits_collection.find(prepQuery({'user':userId}, ['user'])))
    today = dt.now()

    if len(prev_visits) == 0:
        prev_user_visit = {'user': objectId(userId), 'rooms':{roomId: {'entered': today.isoformat(), 'count':1}}}
        return room_visits_collection.insert_one(prev_user_visit)
    else:
        prev_user_visit = prev_visits[0] 
        
        if roomId not in prev_user_visit['rooms']:
            count = 0
            if len(prev_user_visit['rooms']) == MAX_NUM_ROOM_LOGGED:

                room_visits_list = prev_user_visit['rooms'].items()
                sorted_by_count = sorted(room_visits_list, key= lambda x: x[1]['count'])
                rarest_room_visits = [x for x in sorted_by_count if x[1]['count'] == sorted_by_count[0][1]['count']]
                date_to_remove = min(rarest_room_visits, key= lambda x: dt.fromisoformat(x[1]['entered']))
                del prev_user_visit['rooms'][date_to_remove[0]]
        else:
            count = prev_user_visit['rooms'][roomId]['count']

        prev_user_visit['rooms'][roomId] = {'entered': today.isoformat(),'count': count+1}
        del prev_user_visit['user']

        return room_visits_collection.update_many({'user':objectId(userId)}, { '$set': {'rooms': prev_user_visit['rooms']} })
    
@bp.route('/rooms')
@jwt_required()
def getRoomVisits():

    user_id = get_jwt_identity()
    prev_visits = list(room_visits_collection.find(prepQuery({'user':user_id}, ['user'])))

    if len(prev_visits):

        output = []
        sorted_visits = sorted(prev_visits[0]['rooms'].items(), key= lambda x: dt.fromisoformat(x[1]['entered']))
        for room_id, data in sorted_visits:
            output.append({'room': room_id, 'last_entered':data['entered'], 'visit_count':data['count']})
        return jsonify(output)
    else:
        return jsonify([])
