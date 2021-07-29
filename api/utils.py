from flask import session,url_for
import msal
import app_config


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app_config.CLIENT_ID, authority=authority or app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET, token_cache=cache)

def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [],
        redirect_uri=url_for("authorized", _external=True))

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result


def queryFromArgs(keys, params):
    query = {}

    for key in keys:
        if key in params:
            query[key] = params[key]

    return query

def bsonify(data,extra_ids = []):
    
    if '_id' in data:
        data['_id'] = str(data['_id'])

    for id in extra_ids:
        data[id] = str(data[id])
    
    return data 

def bsonifyList(data, extra_ids=[]):
    
    for i, d in enumerate(data):
        data[i] = bsonify(d, extra_ids)
    return data
 
from bson.objectid import ObjectId
def prepQuery(query, ids): 

    for id in ids:
        if id in query:
            query[id] = ObjectId(query[id])

    return query