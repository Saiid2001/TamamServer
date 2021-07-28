from flask import Flask, Blueprint, Response,session, redirect, render_template, make_response, request
from utils import _build_auth_code_flow
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

bp = Blueprint('auth', __name__)


def check_user(ms_user_token):
    resp = users.queryUsers({'email':ms_user_token['preferred_username']  })
    if len(resp)>0:
        usr = resp[0]
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
    print(app_config.CLIENT_ID)
    print(session['flow']['auth_uri']) 

    return redirect(session["flow"]["auth_uri"])

@bp.route('/login-dev')
def login_dev():

    return '<form action="/getAToken-dev" method="get"><input type="text" placeholder="email" name="email"/><input type = "submit"/></form>'

@bp.route('/request-signup', methods=['POST'])
def request_signup():
    data = request.json

@bp.route('/finalize-signup')
def finalize_signup():
    pass

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
