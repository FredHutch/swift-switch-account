#!/usr/bin/env python

from sw2srv import server
from sw2srv import config

from flask import request, Response, jsonify
from functools import wraps

import ldap
import logging

logging.debug('starting app')

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    base = config.base
    scope = ldap.SCOPE_SUBTREE

    username = '%s@fhcrc.org' % username

    try:
        conn = ldap.initialize( config.ldap_url )
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
    username = request.authorization.username
    password = request.authorization.password
    logging.debug( 'verifying user %s for account %s', username, acct_name )
    # Authentication assumed good at this point... now lookup 
    # account name/group combination in ad and check membership:
    # format: user_f_grp
    base = config.base
    scope = ldap.SCOPE_SUBTREE
    connect_as = "%s@fhcrc.org" % username
    conn = ldap.initialize( config.ldap_url )
    conn.set_option( ldap.OPT_REFERRALS, 0 )
    conn.simple_bind_s( connect_as, password )

    # get DN for requested group
    group_name = "%s_grp" % acct_name
    filter = "(&(sAMAccountName=%s)(objectCategory=group))" % group_name
    results = conn.search_s( base, scope, filter )
    group_dn = results[0][1]['distinguishedName'][0]

    # check group DN in memberOf for principal
    filter = "(userPrincipalName=%s@fhcrc.org)" % username
    results = conn.search_s( base, scope, filter )
    princ_groups = results[0][1]['memberOf']

    if group_dn in princ_groups:
        creds = {}
        creds['account'] = acct_name
        creds['password'] = '12345'
        creds['key'] = 'abcdefg'

        r = jsonify(creds)
        r.status_code = 200

        return r

    return 'not member of group %s\n' % group_name


