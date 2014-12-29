#!/usr/bin/env python

from sw2srv import server
from flask import request, Response
from functools import wraps

import ldap
import logging

logging.debug('starting app')

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
        logging.debug( 'successful login from %s', username )
    except ldap.INVALID_CREDENTIALS:
        logging.error( 'failed login from %s', username )
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

@server.route("/swift/account/<acct_name>")
@requires_auth
def auth(acct_name):
    server.logger.setLevel(logging.DEBUG)
    logging.debug( 'verifying user %s for account %s', request.authorization.username, acct_name )
    return 'acct_name: %s' % acct_name
