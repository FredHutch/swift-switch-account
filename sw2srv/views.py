#!/usr/bin/env python

from sw2srv import server
from sw2srv import config

from flask import request, Response, jsonify
from functools import wraps

import ldap
import logging
import csv

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
    except ldap.SERVER_DOWN:
        server.logger.error(
            'error connecting to ldap server {}'.format(config.ldap_url)
        )
        r = jsonify( message = 'Server Error: unable to contact ldap' )
        r.status_code = 500
        return r

    except ldap.INVALID_CREDENTIALS:
        return False

    return True

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        '', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

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

@server.route("/test")
def test(acct_name='test_a'):
    cred = {
        'account': 'Swift_test_a',
        'key': 'gobbledegook',
        'password': 'isasecret'
    }

    r = jsonify( cred )
    return r


@server.route("/swift/account/<acct_name>")
@requires_auth
def auth(acct_name):
    server.logger.setLevel(logging.DEBUG)
    username = request.authorization.username
    password = request.authorization.password
    is_ok = False

    logging.debug( 'verifying user %s for account %s', username, acct_name )
    # Authentication assumed good at this point... now lookup 
    # account name/group combination in ad and check membership:
    # format: user_f_grp
    base = config.base
    scope = ldap.SCOPE_SUBTREE
    connect_as = "%s@fhcrc.org" % username
    conn = ldap.initialize( config.ldap_url )
    conn.set_option( ldap.OPT_REFERRALS, 0 )
    try:
        conn.simple_bind_s( connect_as, password )
    except:
        server.logger.error(
            'error connecting to ldap server {}'.format(config.ldap_url)
        )
        r = jsonify( message = 'Server Error: unable to contact ldap' )
        r.status_code = 500
        return r


    # get DN for requested group
    group_name = "%s_grp" % acct_name
    filter = "(&(sAMAccountName=%s)(objectCategory=group))" % group_name
    results = conn.search_s( base, scope, filter )
    if len(results) == 2:
        group_dn = results[0][1]['distinguishedName'][0]
        group_managed_by = results[0][1]['managedBy']
    else:
        r = jsonify( message = 'No group for account' )
        r.status_code = 404
        return r

    # check if principal has memberOf for the group
    server.logger.debug("checking %s vs %s", username, group_dn )
    filter = "(&(userPrincipalName={}@fhcrc.org)(memberOf={}))".format(
        username, group_dn ) 
    server.logger.debug("%s", filter )
    results = conn.search_s( base, scope, filter )
    if len(results) == 2:
        is_ok = True
        server.logger.debug("Allowing access based on membership in group")

    # get group managedBy entity
    server.logger.debug("checking %s vs %s", username, group_managed_by )
    filter = "(&(userPrincipalName={}@fhcrc.org)(memberOf={}))".format(
        username, group_managed_by )
    server.logger.debug("%s", filter )
    results = conn.search_s( base, scope, filter )
    if len(results) == 2:
        is_ok = True
        server.logger.debug("Allowing access based on membership in managing group")

    if is_ok:
        server.logger.debug("returning credential")
        r = ""
        with open( config.keyfile, 'rb' ) as keyfile:
            creds = csv.DictReader(keyfile, fieldnames = config.key_fields )
            for cred in creds:
                if cred['account'] == 'Swift_{}'.format(acct_name):
                    r = jsonify(cred)
                    r.status_code = 200
                    return r
            if r == "":
                r = jsonify( message='Credentials for account not found' )
                r.status_code = 404
                return r

    return Response( '', 403, '' )


