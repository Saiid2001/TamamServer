from flask import Blueprint, current_app, request, jsonify
from flask.helpers import make_response
from services import mongo
from bson import json_util
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
import users

bp = Blueprint('relations', __name__)

db = mongo.get_default_database()

relations_col = db['relation_collection']

def getRelationsList(params):
    
    params = prepQuery(params, ['user'])
    keys = ['type', 'status', 'user1', 'user2']
    query = prepQuery(queryFromArgs(keys, params),[ 'user1', 'user2'])

    resp = []

    if 'user' in params:

         
        query1 = dict([('user1', params['user'])]+list(query.items()))
        query2 = dict([('user2', params['user'])]+list(query.items()))

        resp1 = list(relations_col.find(prepQuery(query1, ['user1'])))
        resp2 = list(relations_col.find(prepQuery(query2, ['user2'])))

        resp1 = resp1 if resp1!=None else []
        resp2 = resp2 if resp2!=None else []
        resp = resp1+resp2
        
        return bsonifyList(resp,['user1','user2'])

    else:

        resp = list(relations_col.find(query))

        if not resp:
            resp = []

        return bsonifyList(resp,['user1','user2'])

    

# get relationship between user : uid and user : otherId
def _getRelwU(uid, otherId):
    
    '''
    Returns the relation between two users (uid) and (otherId)

    @param uid: the Id of the first user
    @type uid: ObjectId
    @param otherId: the Id of the first user
    @type uid: ObjectId
    @returns: a dict with keys relationship types [friendships, ...] and values the corresponding links
    @rtype: dict
    '''

    links1 = getRelationsList({'user1': uid, 'user2':otherId})
    links2 = getRelationsList({'user1': otherId, 'user2':uid})

    links = links1 + links2

    resp = {}
 
    for link in links:
        
        key = link['type']

        if key == 'friendship' and link['status'] == 'requested':

            if link['user1'] == uid:
                key = 'request-sent'
            else:
                key = 'request-received'

        resp[key] = link

    return resp


@bp.route('/')
@jwt_required()
def getAllRelations():

    uid = get_jwt_identity()

    links = getRelationsList({'user': uid})

    return jsonify(links)


@bp.route('/<otherId>')
@jwt_required()
def getRelationshipsWithUser(otherId):

    uid = get_jwt_identity()

    if not (len(users.queryUsers({'_id': otherId}))):
        return make_response('User does not exist', 404)

    return jsonify(_getRelwU(uid, otherId))


def _getFriends(user):

    links = getRelationsList({'user': user, 'type': 'friendship', 'status': 'established'})

    friends = []

    for link in links:
        friendId = link['user1'] if link['user1'] != user else link['user2']
        friend = users.queryUsers({'_id': friendId})[0]

        friend['relationship'] = {}
        for key in link:
            if key !='user1' and key != 'user2':
                friend['relationship'][key] = link[key]
        
        friends.append(friend)

    return friends

@bp.route('/friendships')
@jwt_required()
def getFriends():
    uid = get_jwt_identity()
    
    return jsonify(_getFriends(uid))

@bp.route('/friendships/requests/sent')
@jwt_required()
def getSentFriendRequests():
    uid = get_jwt_identity()

    links = getRelationsList({'user1': uid, 'type': 'friendship', 'status': 'requested'})

    friends = []

    for link in links:
        friendId = link['user2']  
        friend = users.queryUsers({'_id': friendId})[0]

        friend['relationship'] = {}
        for key in link:
            if key !='user1' and key != 'user2':
                friend['relationship'][key] = link[key]
        
        friends.append(friend)

    return jsonify(friends)

@bp.route('/friendships/requests/received')
@jwt_required()
def getReceivedFriendRequests():
    uid = get_jwt_identity()

    links = getRelationsList({'user2': uid, 'type': 'friendship', 'status': 'requested'})

    friends = []

    for link in links:
        friendId = link['user1']
        friend = users.queryUsers({'_id': friendId})[0]

        friend['relationship'] = {}
        for key in link:
            if key !='user1' and key != 'user2':
                friend['relationship'][key] = link[key]
        
        friends.append(friend)

    return jsonify(friends)


def socketevents(socketio):

    @bp.route('/friendships/request/<friendId>')
    @jwt_required()
    def requestFriendship(friendId):

        uid = get_jwt_identity()

        if not (len(users.queryUsers({'_id': friendId}))):
            return make_response('User does not exist', 404)

        relationship = _getRelwU(uid, friendId)
        print(relationship)  
        
        if 'friendship' in relationship:
            return make_response('Already friends', 403)
        
        if 'request-sent' in relationship:
            return make_response('Request already sent', 403)
        
        if 'request-received' in relationship:
            return make_response('Other user requested this friendship first and awaiting accept', 403)

        # the requester is always user1 and the destination is user2
        friendship = {
            'user1': uid,
            'user2': friendId,
            'type': 'friendship',
            'status': 'requested', 
        }

        friendship = prepQuery(friendship, ['user1', 'user2'])
        
        relations_col.insert_one(friendship)

        #notify requestee
        socketio.emit('new-friend-request', {'user': uid}, room = friendId)

        return make_response('Friend request sent', 200)


    @bp.route('/friendships/accept/<friendId>')
    @jwt_required()
    def acceptFriendship(friendId):

        uid = get_jwt_identity()

        if not (len(users.queryUsers({'_id': friendId}))):
            return make_response('User does not exist', 404)

        relationship = _getRelwU(uid,friendId)
        
        if 'friendship' in relationship:
            return make_response('Already friends', 403)
        
        if not( 'request-received' in relationship ):
            return make_response('Other did not request this friendship to be accepted', 403)
        
        query = prepQuery({'_id': relationship['request-received']["_id"]}, ['_id'])
        relations_col.update_one(
            query, 
            {'$set':{
                'status':'established'
            }}
        )

        #notify requester
        socketio.emit('friend-request-accepted', {'user': uid}, room = friendId)

        return make_response('Friend request accepted', 200)

        

