from flask import Blueprint, current_app, request, jsonify
from flask.helpers import make_response
from history import MAX_NUM_ROOM_RECOMMENDED
from services import mongo
from bson import json_util
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery,objectId
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
import users
from datetime import datetime as dt
import random

bp = Blueprint('relations', __name__)

db = mongo.get_default_database()

relations_col = db['relation_collection']
MAX_NUM_INTERACTIONS_LOGGED = 100
MIN_DURATION = 30

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
def _getRelwU(uid, otherId, relType = None):
    
    '''
    Returns the relation between two users (uid) and (otherId)

    @param uid: the Id of the first user
    @type uid: ObjectId
    @param otherId: the Id of the first user
    @type uid: ObjectId
    @returns: a dict with keys relationship types [friendships, ...] and values the corresponding links
    @rtype: dict
    '''
    if relType:
        links1 = getRelationsList({'user1': uid, 'user2':otherId, 'type': relType})
        links2 = getRelationsList({'user1': otherId, 'user2':uid, 'type': relType})
    else:
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


def _getFriends(user, query):

    links = getRelationsList({'user': user, 'type': 'friendship', 'status': 'established'})

    friends = []

    checkRoom = 'room' in query
    checkOnline = 'onlineStatus' in query
    for link in links:
        friendId = link['user1'] if link['user1'] != user else link['user2']
        friend = users.queryUsers({'_id': friendId})[0]

        friend['relationship'] = {}
        for key in link:
            if key !='user1' and key != 'user2':
                friend['relationship'][key] = link[key]

        if not checkRoom or friend['room'] == query['room']:
            if not checkOnline or friend['onlineStatus']=='online':
                friends.append(friend)

    return friends

def _getMutuals(user1, user2):

    f1 = _getFriends(user1,{})
    f2 = _getFriends(user2,{})

    m1 = { f['_id']: f for f in f1}
    m2 = { f['_id']: f for f in f2}

    s1 = set(m1.keys()) 
    s2 = set(m2.keys())
    
    intersect = s1.intersection(s2)

    mutuals = [] 
    for fid in intersect:
        mutuals.append(m1[fid])
    
    return mutuals

@bp.route('/friendships')
@jwt_required()
def getFriends():
    uid = get_jwt_identity()
    
    return jsonify(_getFriends(uid, request.args))

@bp.route('/friendships/mutuals/<other_user>')
#@jwt_required()
def getMutuals(other_user):

    #uid = get_jwt_identity()
    uid = "6123dc348c515f345f4b88d6"

    return jsonify(bsonifyList(_getMutuals(uid, other_user)))


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

@bp.route('/friendships/recommended')
@jwt_required()
def recommendFriends():
    user = get_jwt_identity()
    candidates = users.queryUsers({'status':'complete'})
    candidates = [c for c in candidates if str(c['_id']) != user]
    chosen = random.sample(candidates, k= min(len(candidates), 9))

    output = []

    for f in chosen:
        output.append(
            {'user':bsonify(f),'from':'recommended'}
        )

    return jsonify(output)

def socketevents(socketio):

    @bp.route('/friendships/request/<friendId>')
    @jwt_required()
    def requestFriendship(friendId):

        uid = get_jwt_identity()

        if not (len(users.queryUsers({'_id': friendId}))):
            return make_response('User does not exist', 404)

        relationship = _getRelwU(uid, friendId)
        
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



def _logInteraction(user1, user2,group,room, duration):

    relations = _getRelwU(user1,user2, 'interaction')
    
    today = dt.now()
    interaction_entry = {'start': today.isoformat(), 'duration':duration, 'group': group, 'room': room}

    if 'interaction' not in relations:
        prev_interaction = {'user1': objectId(user1), 'user2': objectId(user2), 'type':'interaction', 'isOngoing': duration == -1, 'log':[interaction_entry]}
        return relations_col.insert_one(prev_interaction)
    else:
        prev_interaction = relations['interaction']
        
        if len(prev_interaction['log']) == MAX_NUM_INTERACTIONS_LOGGED:
            prev_interaction['log'].pop(0)

        if prev_interaction['isOngoing']:
            prev_interaction['log'][-1]['duration'] = duration
        else:
            prev_interaction['log'].append(interaction_entry)

        return relations_col.update_one({'_id':objectId(prev_interaction['_id'])}, { '$set': {'log': prev_interaction['log'], 'isOngoing': duration==-1} })

def _removeLastInteraction(user1, user2):

    relations = _getRelwU(user1,user2, 'interaction')

    if 'interaction' in relations:

        prev_interaction = relations['interaction']
        prev_interaction['log'].pop()
        prev_interaction['isOngoing'] = False

        return relations_col.update_one({'_id':objectId(prev_interaction['_id'])}, { '$set': {'log': prev_interaction['log'], 'isOngoing': prev_interaction['isOngoing']} })


def logInteractionStart(user1, user2,group, room):
    _logInteraction(user1, user2,group,room, -1)
    print('interaction started: [', user1,"] + [" ,user2,"] @ ",group ) 

def logInteractionEnd(user):
    today = dt.now()

    links = list(getRelationsList({'user': user, 'type': 'interaction', 'isOngoing':True}))

    if len(links):
         
        for link in links:
            duration = (today-dt.fromisoformat(link['log'][-1]['start'])).total_seconds()
            user2 = link['user1'] if link['user2'] == user else link['user2']
            if duration>= MIN_DURATION: 
                _logInteraction(user, user2, link['log'][-1]['group'],link['log'][-1]['room'], duration)
            else:
                _removeLastInteraction(user,user2)
 
def _getAllInteractions(user):

    links = getRelationsList({'user': user, 'type': 'interaction'}) 

    interactions = {}

    for link in links:
        otherId = link['user1'] if link['user1'] != user else link['user2']
        
        interactions[str(otherId)] = bsonifyList(link['log'],['group'])
    
    return interactions

@bp.route('/interactions')
@jwt_required()
def getAllInteractions():  
    user = get_jwt_identity()
    return jsonify(_getAllInteractions(user))

def _getInteractions(user1, user2):
    prev_interactions = _getRelwU(user1,user2, 'interaction')
    if 'interaction' not in prev_interactions: return []

    prev_interactions = prev_interactions['interaction']

    if len(prev_interactions): 
        
        output = prev_interactions['log']
        return output
    else:
        return []

@bp.route('/interactions/<other_user>')
@jwt_required() 
def getInteractions(other_user):
    
    userId = get_jwt_identity()
    return jsonify(_getInteractions(userId,other_user))

from rooms import queryRooms
@bp.route('/interactions/last/<other_user>')
@jwt_required() 
def getLastInteraction(other_user):
    userId = get_jwt_identity()
    interactions = _getInteractions(userId, other_user)
    if len(interactions) == 0:
        return jsonify({})
    
    interDate, interDuration, interGroup, interRoom = interactions[-1].values()

    response = {}
    response['date'] = interDate
    response['duration'] = interDuration
    response['secondsSinceToday'] = (dt.now()-dt.fromisoformat(interDate)).seconds
    response['room'] = bsonifyList(queryRooms({'_id': interRoom}))[0]

    return jsonify(response) 

@bp.route('/interactions/recommendation')
@jwt_required()
def getInteractionsRecommendations():

    user = get_jwt_identity()

    interactions = _getAllInteractions(user)

    def key_recent(interaction_tupple):
        user, interaction = interaction_tupple
        return dt.fromisoformat(interaction[-1]['start'])
    
    def key_frequent(interaction_tupple):
        user, interaction = interaction_tupple
        return len(interaction)

    sorted_interactions = sorted(interactions.items(), key= lambda x: (key_frequent(x), key_recent(x)))

    max_num_recommendations = 5

    recommended_users = []

    for i in range(min(len(sorted_interactions), max_num_recommendations)):

        recommended_users.append(users.queryUsers({'_id': sorted_interactions[i][0]})[0])


    return jsonify(recommended_users)


@bp.route('/groups/recommended')
@jwt_required()
def recommendGroups():

    user = get_jwt_identity()

    user_data = users.queryUsers({'_id': user})[0]
    #simplistic grouping based on courses
    # seeking friends groups
    friends = _getFriends(user,{'onlineStatus': 'online'})
    friends_in_rooms = {}

    for friend in friends:

        friends_in_rooms[friend['room']] = friends_in_rooms.get(friend['room'], [])
        friends_in_rooms[friend['room']].append(bsonify(friend))

    friends_in_rooms = sorted(friends_in_rooms.items(), key = lambda x: len(x[1]), reverse=True)

    friend_group_recommendation = [{'type': 'friends', 'name':'Friends Group' , 'room': f[0], 'users': f[1]} for f in friends_in_rooms]

    
    #course based grouping
    from courses import _getCourseSections, _getCourseByCRN
    sections = user_data['classes']

    sections_data = {x:_getCourseByCRN(x) for x in sections}



    section_peers_in_rooms = {}

    def getMaxInSection(section):

            section_peer_recommendations =  {}
            peers = users.queryUsers({"classes":{"$in": [section]}, 'onlineStatus':'online'})
            if user_data in peers:
                peers.remove(user_data)

            for peer in peers:
                section_peer_recommendations[peer['room']] = section_peer_recommendations.get(peer['room'], [])
                section_peer_recommendations[peer['room']].append(bsonify(peer))

            return section_peer_recommendations
            
            

    for section in sections:

        section_peers_in_rooms[section] = getMaxInSection(section)

        if len(section_peers_in_rooms[section]):
            section_peers_in_rooms[section] = max(section_peers_in_rooms[section].items(), key= lambda x: len(x[1]))
            section_peers_in_rooms[section] = {
                    'type':'section', 
                    'name': sections_data[section]['SUBJECT']+sections_data[section]['CODE']+"-"+sections_data[section]['CRN'], 
                    'room': section_peers_in_rooms[section][0], 
                    'users':section_peers_in_rooms[section][1] 
                }
        else:
            section_peers_in_rooms[section] = {}

    #section_group_recommendation = max(list(section_peers_in_rooms.values()), key= lambda x: len(x['users']) if 'users' in x else -100)

    section_group_recommendation = list(section_peers_in_rooms.values())


    # subject based recommendation

    courses = {x['SUBJECT']+x['CODE']: _getCourseSections(x["SUBJECT"], x['CODE']) for i, x in sections_data.items()}

    course_group_recommendation = []

    for subject in courses:

        max_in_course = {}

        for section in courses[subject]:

            max_in_section = getMaxInSection(section)

            # group under course and by room

            for room in max_in_section:

                max_in_course[room] = max_in_course.get(room, [])
                max_in_course[room].extend(max_in_section[room])

        if len(max_in_course):
            max_in_course = max(max_in_course.items(), key= lambda x: len(x[1]))

            course_group_recommendation.append(
                {
                    'type': 'course',
                    'name': subject,
                    'room': max_in_course[0],
                    'users': max_in_course[1]
                }
            )


        recommendations = []
        
        if len(friend_group_recommendation) and 'room' in friend_group_recommendation[0]:
            recommendations += friend_group_recommendation
        if len(course_group_recommendation) and 'room' in course_group_recommendation[0]:
            recommendations += course_group_recommendation
        if len(section_group_recommendation) and 'room' in section_group_recommendation[0]:
            recommendations += section_group_recommendation

        # make sure recommendation is not empty 
        # fill in at least some rooms

        if(len(recommendations)<MAX_NUM_ROOM_RECOMMENDED):
            rooms_to_add = MAX_NUM_ROOM_RECOMMENDED - len(recommendations)
            candidate_rooms = queryRooms({})



            candidate_rooms = sorted(candidate_rooms, key = lambda x: len(x['users']), reverse=True)

            candidate_rooms = [c for c in candidate_rooms if c['name']!='Main Gate']
            
            for i in range(len(candidate_rooms)):

                candidate_rooms += [candidate_rooms[i]]*(len(candidate_rooms)//(i+1)-1)

            import random

            candidate_room1 = candidate_rooms[random.randint(0, len(candidate_rooms)-1)]

            candidate_rooms = [c for c in candidate_rooms if c['_id']!=candidate_room1['_id']]

            candidate_room2 = candidate_rooms[random.randint(0, len(candidate_rooms)-1)]

            candidate_rooms = [c for c in candidate_rooms if c['_id']!=candidate_room2['_id']]

            candidate_room3 = candidate_rooms[random.randint(0, len(candidate_rooms)-1)]

            candidate_rooms = [c for c in candidate_rooms if c['_id']!=candidate_room3['_id']]

            candidate_rooms = [candidate_room1, candidate_room2, candidate_room3]

            for i in range(rooms_to_add):
                recommendations.append({
                    'type':'filler', 
                    'name': 'Meet new people',
                    'room': str(candidate_rooms[i]['_id']),
                    'users': candidate_rooms[i]['users']
                })
        
        recommendations = sorted(recommendations, key= lambda x: len(x['users']) if 'users' in x else -100, reverse=True)


    return jsonify(recommendations[:MAX_NUM_ROOM_RECOMMENDED])
    


#testing

#logInteraction('aaaaaaaaaaaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbbbbbbbbbbb','000000000000000000000001',5000)
#logInteraction('aaaaaaaaaaaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbbbbbbbbbbb','000000000000000000000001',3000)
#logInteraction('aaaaaaaaaaaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbbbbbbbbbbb','000000000000000000000001',5000)
#logInteraction('aaaaaaaaaaaaaaaaaaaaaaaa', 'bbbbbbbbbbbbbbbbbbbbbbbb','000000000000000000000001',2000) 
#relations_col.delete_many({'type':"interaction"})  
