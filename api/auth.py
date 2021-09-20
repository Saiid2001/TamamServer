from flask import Flask, Blueprint, Response,session, redirect, render_template, make_response, request
from utils import _build_auth_code_flow,bsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
    jwt_required
)
from flask import jsonify
from flask import request
from flask import url_for
import app_config
import requests
import msal
import users
import mail
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime as dt

bp = Blueprint('auth', __name__)

def check_user(ms_user_token):
    resp = users.queryUsers({'email':ms_user_token['preferred_username']  })
    if len(resp)>0: 
        usr = resp[0]

        if usr['status'] != 'complete':
            users.removeUser(usr['_id'])
            return redirect('http://localhost/callback?request_signup=1&email='+ms_user_token['preferred_username'])

        tokens = generate_tokens(str(usr['_id']))
        #return tokens
        #grequests.get('http://127.0.0.1/callback', params = tokens)
        return redirect('http://localhost/callback?access_token='+tokens['access_token']+"&refresh_token="+tokens['refresh_token']+'request_signup=0')
    else:
        return redirect('http://localhost/callback?request_signup=1&email='+ms_user_token['preferred_username'])

def generate_tokens(user_id):

    access_token = create_access_token(identity=user_id, fresh=True)
    refresh_token = create_refresh_token(user_id)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }

# Email tokens using itsdangerous
# Courtesy of https://realpython.com/handling-email-confirmation-in-flask/
# Generates a token using the itsdangerous algorithm into which the user id is embedded
def generate_confirmation_token(id):
    serializer = URLSafeTimedSerializer(app_config.CONFIRMATION_SECRET_KEY)
    return serializer.dumps(id, salt=app_config.SECURITY_PASSWORD_SALT)

# Checks if token has expired
# If not, regenerates user ID from token and returns it
def confirm_token(token, expiration=180):
    serializer = URLSafeTimedSerializer(app_config.CONFIRMATION_SECRET_KEY)
    try:
        id = serializer.loads(
            token,
            salt=app_config.SECURITY_PASSWORD_SALT,
            max_age=expiration
        )
    except:
        return "None"
    return id

@bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    
    try: 
        verify_jwt_in_request(refresh=True)
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return jsonify({'access_token': new_token}),200
    except Exception:
        return None, 400





@bp.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    return session.get("user")
 
@bp.route("/login")  
def login():
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    
    session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)

    return redirect(session["flow"]["auth_uri"])

@bp.route('/login-dev')
def login_dev():

    return '<form action="/getAToken-dev" method="get" style="text-align:center;position:relative;top:50px"><input type="text" placeholder="email" name="email"/><input type = "submit"/></form>'

@bp.route('/request-signup', methods=['POST'])
def request_signup():
    data = request.form
    #data = {'email': 'nwz05@mail.aub.edu', 'firstname': 'Nader', 'lastname': 'Zantout'}
    checkQuery = users.queryUsers({'email': data['email']})
    today = dt.today()
    if len(checkQuery)>0:
        if checkQuery[0]['status']=='pending':
            date_created= checkQuery[0]['date_created']
            date_created = dt.fromisoformat(date_created)
            time_passed = today-date_created
            if time_passed.total_seconds<200:
                return make_response("Account awaiting verification", 403)
            else:
                users.removeUser(checkQuery[0]['_id'])
        elif checkQuery[0]['status']=='confirmed':
            return make_response("User confirmed, please complete your profile", 403)
        else:
            return make_response("User already in database", 403)
    user = {'email': data['email'],
            'firstName': data['firstname'],
            'lastName': data['lastname'],
            'status': 'pending',
            'onlineStatus': 'offline',
            'date_created': today.isoformat(),
            'privacy': {
                'allow_map': True,
                'collect_interaction_info': True,
                'allow_search': True,
                'show_online_status': True
            }}
    users.addUser(user)
    user = users.queryUsers({'email': data['email']})[0]
    confirmation_token = generate_confirmation_token(user['_id'])
    mail.send_confirmation(user['email'], confirmation_token)

    return bsonify(user)

@bp.route('/confirm-email/<token>')
def confirm_email(token):
    id = confirm_token(token)
    if id=="None":
        return make_response("Token invalid, or has already expired.", 403)

    user = users.queryUsers({'_id': id})[0]
    if user['status'] == 'pending':
        users.updateUsers({"_id": id}, {'status': 'confirmed'})
        return render_template('email-verification.html')
    else:
        return make_response("User already verified", 403)

@bp.route('/test')
def test():
    return render_template('email-verification.html')

@bp.route('/finalize-signup', methods=['POST'])
def finalize_signup():
    #request.form should contain the user ID
    data = request.json
    #if len(users.queryUsers({'email': 'nwz05@mail.aub.edu'})) == 0:
    #    return make_response("User not found. Please create an account.", 403)
    #id = users.queryUsers({'email': 'nwz05@mail.aub.edu'})[0]["_id"]
    # data = {'_id': id, 'major': 'Electrical and Computer Engineering', 'gender': 'Male', 'age': 20, 'avatar': 'stuff'}


    if len(users.queryUsers({'_id': data['_id']}))==0:
        return make_response("User not found. Please create an account.", 403)
    user = users.queryUsers({'_id': data['_id']})[0]
    if user['status'] == 'pending':
        return make_response("Please confirm your account before proceeding.", 403)
    elif user['status'] == 'complete':
        return make_response('You have already completed your profile.', 403)
    id = data['_id'] 
    users.updateUsers({'_id': id}, data['data'])
    users.updateUsers({'_id': id}, {'status':'complete'})
    user = users.queryUsers({'_id': id})[0]
    return bsonify(user) 
  

@bp.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("index", _external=True))

@bp.route("/graphcall") 
def graphcall():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.get(  # Use token to call downstream service
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        ).json()
    return render_template('display.html', result=graph_data)


@bp.route('/protected')
@jwt_required()
def protected():
    current_user=get_jwt_identity()
    return f"<h1>Welcome {current_user}</h1>",200
