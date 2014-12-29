#!/usr/bin/env python

from sw2srv import server
from flask import request, Response
from functools import wraps

import ldap

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    base = "dc=fhcrc,dc=org"
    scope = ldap.SCOPE_SUBTREE

    username = '%s@fhcrc.org' % username

    try:
        conn = ldap.initialize( "ldap://dc.fhcrc.org" )
        conn.set_option( ldap.OPT_REFERRALS, 0 )
        conn.simple_bind_s( username, password )
    except ldap.INVALID_CREDENTIALS:
        print "invalid credentials"
        return False

    return True

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@server.route("/")
def ping():
    return 'alive'

@server.route("/auth")
@requires_auth
def auth():
    return 'authenticated'
