from time import time
from flask.helpers import make_response
import requests
import re
from flask import Blueprint, current_app, request, jsonify
from requests.api import get
from services import mongo
from bson import json_util
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery
import json
import users
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime as dt, tzinfo
from datetime import timedelta 
import pytz

bp = Blueprint('courses', __name__)

db = mongo.get_default_database()

courses_col = db['courses_collection']

# Constants
url= "https://www-banner.aub.edu.lb/catalog/"
schedByLetters = [
    "schd_A.htm", 
    "schd_B.htm", 
    "schd_C.htm", 
    "schd_D.htm", 
    "schd_E.htm", 
    "schd_F.htm", 
    "schd_G.htm", 
    "schd_H.htm", 
    "schd_I.htm", 
    "schd_J.htm", 
    "schd_K.htm", 
    "schd_L.htm", 
    "schd_M.htm", 
    "schd_N.htm", 
    "schd_O.htm", 
    "schd_P.htm", 
    "schd_Q.htm", 
    "schd_R.htm", 
    "schd_S.htm", 
    "schd_T.htm", 
    "schd_U.htm", 
    "schd_V.htm", 
    "schd_W.htm", 
    "schd_X.htm", 
    "schd_Y.htm", 
    "schd_Z.htm", 
]

def _getHTML(base,endpoint):
    response = requests.get(base+endpoint)
    html = str(response.content)
    return html

def _getClassesFromPage(html):
    pattern = "<TD>[^<]*<\/TD>"
    results = re.findall(pattern,html)

    classes = []

    for i in range(0,len(results)-1,37):
        row = results[i:i+37]
        row = [d[4:-5] for d in row ]
        
        classData = {
                'CRN': row[1],
                'SUBJECT': row[2],
                'CODE': row[3],
                'SECTION': row[4],
                'ERROR': False
                }

        try:
            s1_start = row[11]
            classData['S1_START'] =(int(s1_start[:2]),int(s1_start[2:])) if len(s1_start)==4 else (-1,-1)
            s1_end = row[12]

            classData['S1_END'] =(int(s1_end[:2]),int(s1_end[2:])) if len(s1_end)==4 else (-1,-1)

            classData['S1_DAYS'] = [ d != '.' for d in row[15:20]]

            classData['S1_LOC'] = row[13]+"-"+row[14]

            s2_start = row[22]
            classData['S2_START'] =(int(s2_start[:2]),int(s2_start[2:])) if len(s2_start)==4 else (-1,-1)
            s2_end = row[23]
            classData['S2_END'] =(int(s2_end[:2]),int(s2_end[2:])) if len(s2_end)==4 else (-1,-1)

            classData['S2_DAYS'] = [ d != '.' for d in row[26:33]]
            classData['S2_LOC'] = row[24]+"-"+row[25]
        except:
            classData['ERROR'] = True
            print(i//37)


        classes.append(classData)
    
    return classes

def getClasses(url, endpoints):
    classes = []
    for s in schedByLetters:
        html = _getHTML(url,s)
        if s == 'schd_C.htm':
            html = html.replace("30761<\\n/TD>","30761</TD>",1)
            
        classes+=_getClassesFromPage(html)
    return classes
 

def initCoursesDB():

    courses_col.delete_many({})

    classes = getClasses(url, schedByLetters)
    print("LOADED COURSES FROM AUB")
    #courses_col.delete_many({})
    for cl in classes:
        courses_col.insert_one(cl)


def _getCourseByCRN(CRN):
    return courses_col.find_one({'CRN': CRN})

@bp.route('/byCRN/<CRN>')
#@jwt_required()
def getCourseByCRN(CRN):
    course = _getCourseByCRN(CRN)

    if course:
        return jsonify(bsonify(course))
    else:
        return make_response('COURSE NOT FOUND',404)


@bp.route('/setCRNs', methods=['POST'])
@jwt_required()
def setCourses():
    userID = get_jwt_identity()
 
    data = request.json

    ls = [] 
    for course in data['classes']:
        if  re.fullmatch('[0-9]{5}',course):
            ls.append(course)
        else:
            return make_response('WRONG CRNS',400)
 
    users.updateUsers({'_id':userID}, {'classes':ls})

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

def _getCourseMeetingLink(CRN):

    user = users.queryUsers({'_id': get_jwt_identity()})[0]

    if 'link' not in user:
        return None
    else:
        return user['link'].get(CRN, None)

def _setCourseMeetingLink(CRN, link):

    user = users.queryUsers({'_id': get_jwt_identity()})[0]
    links = user.get('link', {})
    links[CRN] = link
    users.updateUsers({'_id': get_jwt_identity()}, {'link': links})



@bp.route('/byCRN/<CRN>/link' , methods=['POST', 'GET'])
@jwt_required()
def processMeetingLink(CRN):

    if request.method == "GET":
        link = _getCourseMeetingLink(CRN)
        if link:
            return jsonify({'link':link})
        else:
            return jsonify({})
    
    else:
        _setCourseMeetingLink(CRN, request.json['link'])
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 


def _getCourseSections(subject, code):

    courses  = courses_col.find({'SUBJECT': subject, "CODE": code})

    return [x['CRN'] for x in courses]

def _getCourses(user):
    user = users.queryUsers({'_id': user})[0]

    if 'classes' not in user:
        return []
    else: 
        classes = []
        for crn in user['classes']: 
            cl = _getCourseByCRN(crn)

            if cl:
                classes.append(cl)

    return classes

@bp.route('')
@jwt_required() 
def getUserCourses():
    return jsonify(bsonifyList(_getCourses(get_jwt_identity())))

def _getCommonCourses(list1, list2):
 
    set1 = set(list1)
    set2 = set(list2)

    commonSections = set1.intersection(set2)
    differentSections1 = set1-commonSections
    differentSections2 = set2-commonSections

    courses1 = []
    courses2 = []

    for sec in differentSections1:
        course = _getCourseByCRN(sec)
        courses1.append(course['SUBJECT']+"-"+course['CODE'])

    for sec in differentSections2:
        course = _getCourseByCRN(sec)
        courses2.append(course['SUBJECT']+"-"+course['CODE'])
    
    courses1 = set(courses1)
    courses2 = set(courses2)

    commonCourses = courses1.intersection(courses2)

    response = []

    for sec in commonSections:
        course = _getCourseByCRN(sec)
        response.append({
            'type':'section',
            'group': sec,
            'name': course['SUBJECT']+"-"+course['CODE']+"-"+course['SECTION']
        }) 
 
    for course in commonCourses:

        response.append(
            {
                'type':'course',
                'group': course,
                'name': course
            }
        )

    return response

@bp.route('/common/<otherID>')
@jwt_required() 
def getCommonCourses(otherID):

    list1 = users.queryUsers({'_id': get_jwt_identity()})[0]['classes']
    try:
        list2 = users.queryUsers({'_id': otherID})[0]['classes']
    except:
        return make_response("USER NOT FOUND", 404)

    return jsonify(_getCommonCourses(list1, list2))


def nextInstanceOfEvent(course, weekday, hour, minute):

    del course['_id']

    location = _getCourseMeetingLink(course['CRN'])

    def datetimeInWeek(weekOffset, weekday, hour, minute):

        now = dt.now()
        d = dt(now.year, now.month, now.day, hour, minute, tzinfo = pytz.timezone('Etc/GMT-3'))

        d += timedelta(days=-now.weekday() + weekOffset*7+weekday)
        return d

    earliest = None

    #check for rest of week
    if weekday<=4:

        next_dates = []

        for i in range(weekday, len(course['S1_DAYS'])):

            if course['S1_DAYS'][i]:
                next_dates.append(datetimeInWeek(0,i, course['S1_START'][0], course['S1_START'][1]))

            if len(next_dates)==2:
                break

        for i in range(weekday, len(course['S2_DAYS'])):

            if course['S2_DAYS'][i]:
                next_dates.append(datetimeInWeek(0,i, course['S2_START'][0], course['S2_START'][1]))

            if len(next_dates)==4:
                break
        
        next_dates = sorted(next_dates)

        now = pytz.utc.localize(dt.now())
        now = now.astimezone(pytz.timezone('Etc/GMT-3'))

        while len(next_dates) and next_dates[-1]<now :
            next_dates.pop()

        if len(next_dates):
            if location:
                earliest =  {'course': course, 'date': next_dates[-1], 'location': location, 'is_online': True}
            else:
                earliest =  {'course': course, 'date': next_dates[-1], 'location': course['S1_LOC'], 'is_online': False}
        

    #check for next week
    
    if weekday > 4 or earliest == None:

        next_dates = []

        for i in range(len(course['S1_DAYS'])):

            if course['S1_DAYS'][i]:
                #next_dates.append(f'weekday={weekday}, i={i}, today={dt.now().isoformat()}, offset={7-weekday +i}, date={datetimeInWeek(1, i, course["S1_START"][0], course["S1_START"][1])}')
                next_dates.append(datetimeInWeek(1, i, course['S1_START'][0], course['S1_START'][1]))

            if len(next_dates)==2:
                break

        for i in range(len(course['S2_DAYS'])):

            if course['S2_DAYS'][i]:
                #next_dates.append(f'weekday={weekday}, i={i}, date={datetimeInWeek(1, i, course["S2_START"][0], course["S2_START"][1])}')
                next_dates.append(datetimeInWeek(1, i, course['S2_START'][0], course['S2_START'][1]))

            if len(next_dates)==4:
                break 
        
        next_dates = sorted(next_dates, reverse=True)

        if location:
            temp =  {'course': course, 'date': next_dates[-1], 'location': location, 'is_online': True}
        else:
            temp =  {'course': course, 'date': next_dates[-1], 'location': course['S1_LOC'], 'is_online': False}

        if earliest == None or temp['date']<earliest['date']:
            earliest = temp
        
    return earliest


@bp.route('/upcoming')
@jwt_required() 
def getUpcomingEvents():

    user = get_jwt_identity()

    courses = _getCourses(user)
    
    today = pytz.utc.localize(dt.today())
    today = today.astimezone(pytz.timezone('Etc/GMT-3'))
    weekday = today.weekday()
    hour = today.time().hour
    minute = today.time().minute

    upcoming = []

    for course in courses:
        upcoming.append(nextInstanceOfEvent(course, weekday, hour, minute))

    upcoming = sorted(upcoming, key= lambda x: x['date'])

    return jsonify(upcoming)

#query classes from AUB on restart of server
#initCoursesDB() 
   