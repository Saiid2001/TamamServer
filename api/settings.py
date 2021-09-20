from flask import Blueprint, current_app, request, jsonify, make_response
from services import mongo
from bson import json_util
from bson.objectid import ObjectId
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
import users

bp = Blueprint("settings", __name__)

db = mongo.get_default_database()

@bp.route('/set')
@jwt_required()
def setSettings():
    uid = get_jwt_identity()
    settings = ['allow_map', 'collect_interaction_info', 'allow_search', 'show_online_status']
    query = queryFromArgs(settings, request.args)
    for key in query:
        if query[key] == "true":
            query[key] = True
        elif query[key] == "false":
            query[key] = False
        else:
            del query[key]
    users.updateUsers({"_id": uid}, query)

#users.updateUsers({}, { 'privacy': { 'allow_map': True, 'collect_interaction_info': True, 'allow_search': True, 'show_online_status': True }})