from flask.helpers import make_response
import requests
import re
from flask import Blueprint, current_app, request, jsonify
from services import mongo
from bson import json_util
from utils import queryFromArgs, bsonify, bsonifyList, prepQuery
import json
import users
from flask_jwt_extended import jwt_required, get_jwt_identity

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

            s2_start = row[22]
            classData['S2_START'] =(int(s2_start[:2]),int(s2_start[2:])) if len(s2_start)==4 else (-1,-1)
            s2_end = row[23]
            classData['S2_END'] =(int(s2_end[:2]),int(s2_end[2:])) if len(s2_end)==4 else (-1,-1)

            classData['S2_DAYS'] = [ d != '.' for d in row[26:33]]
            classData['LOC'] = row[13]
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

    classes = getClasses(url, schedByLetters)
    print("LOADED COURSES FROM AUB")
    #courses_col.delete_many({})
    for cl in classes:
        courses_col.insert_one(cl)


def _getCourseByCRN(CRN):
    return courses_col.find_one({'CRN': CRN})

@bp.route('/byCRN/<CRN>')
@jwt_required()
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

    print(data)
    ls = [] 
    for course in data['classes']:
        if  re.fullmatch('[0-9]{5}',course):
            ls.append(course)
        else:
            return make_response('WRONG CRNS',400)
 
    users.updateUsers({'_id':userID}, {'classes':ls})

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@bp.route('')
@jwt_required() 
def getUserCourses():

    user = users.queryUsers({'_id': get_jwt_identity()})[0]

    if 'classes' not in user:
        return jsonify([])
    else: 
        classes = []
        for crn in user['classes']: 
            cl = _getCourseByCRN(crn)

            if cl:
                classes.append(cl)
            else:
                return make_response('ERROR IN USER CRNS',400)

        return jsonify(bsonifyList(classes))



#query classes from AUB on restart of server
#initCoursesDB() 
   