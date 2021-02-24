from flask import Flask, Blueprint, Response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required
)
from flask import jsonify
from flask import request
from flask import url_for
import requests

bp = Blueprint('auth', __name__)

def generate_tokens(user_id):

    access_token = create_access_token(identity=user_id, fresh=True)
    refresh_token = create_refresh_token(user_id)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }

def refresh_token():
    try:
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}
    except Exception:
        return None


def require_login():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            resp = requests.get(
                      current_app.config['API_ENDPOINT'] + 'auth/get-user-session',
                      params={'sid': session.get('sila_session', '').split('|')[0], 'access': access_level},
                      cookies={'sila_session': session.get('sila_session')}
                  )
            if (resp.ok):
                return func(*args, **kwargs)
            else:
                return redirect('/')
        return wrapper
    return decorator


@bp.route('/login')
def login():
    # TODO: add microsoft authentication

    return generate_tokens('test_user')






@bp.route('/protected')
@jwt_required()
def protected():
    current_user=get_jwt_identity()
    return f"<h1>Welcome {current_user}</h1>",200
