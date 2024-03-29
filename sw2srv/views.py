#!/usr/bin/env python

from sw2srv import server
from sw2srv import config
from sw2srv import forms

from flask import request, Response, jsonify
from flask import render_template, redirect
from functools import wraps

import json
import ldap
import logging
import csv



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


def principal_in_group( conn, princ, group ):
    # Is principal (DN) in group?
    base = princ
    filter = "(memberOf:1.2.840.113556.1.4.1941:={})".format( group )
    scope = ldap.SCOPE_BASE
    results = conn.search_s( base, scope, filter )
    if len(results) == 1:
        return True
    else:
        return False


def validate( username, acct_name, binddn, bindpw, grp_suffix):
    logging.debug( 'verifying user %s for account %s', username, acct_name )
    # Authentication assumed good at this point... now lookup
    # account name/group combination in ad and check membership:
    # format: user_f_grp
    # grp_suffix is either _swift_grp or _grp
    base = config.base
    scope = ldap.SCOPE_SUBTREE
    connect_as = "%s@fhcrc.org" % binddn
    conn = ldap.initialize( config.ldap_url )
    conn.set_option( ldap.OPT_REFERRALS, 0 )
    try:
        conn.simple_bind_s( connect_as, bindpw )
    except:
        server.logger.error(
            'error connecting to ldap server {}'.format(config.ldap_url)
        )
        message = 'Server Error: unable to contact ldap'
        status_code = 500
        return False, message, status_code

    # get principal's DN
    filter = "(sAMAccountName={})".format( username )
    results = conn.search_s( base, scope, filter )
    if results[0][0] is not None:
        princ_dn = results[0][1]['distinguishedName'][0]
    else:
        message = "Could not locate DN for user"
        status_code = 500
        return False, message, status_code
    server.logger.debug( "located DN for principal" )

    # get DN for requested group
    group_name = acct_name + grp_suffix
    filter = "(&(sAMAccountName=%s)(objectCategory=group))" % group_name
    results = conn.search_s( base, scope, filter )
    if len(results) == 2:
        group_dn = results[0][1]['distinguishedName'][0]
        try:
            group_managed_by = results[0][1]['managedBy'][0]
        except KeyError as e:
            if 'managedBy' in e.args:
                server.logger.debug( "group missing managedBy attribute- soldiering on" )
                group_managed_by = False
            else:
                raise e
    else:
        message = 'No directory group for account {}'.format(acct_name)
        status_code = 404
        return False, message, status_code

    # check if principal has memberOf for the group
    server.logger.debug("checking %s vs %s", username, group_dn )
    if principal_in_group( conn, princ_dn, group_dn ):
        server.logger.debug("Allowing access based on membership in group")
        message = 'User is group member'
        status_code = 200
        return True, message, status_code
    else:
        server.logger.debug( "Principal not in group via chain" )

    # check if principal is in managedBy for group
    if group_managed_by:
        server.logger.debug("checking %s vs %s", princ_dn, group_managed_by )
        if principal_in_group( conn, princ_dn, group_managed_by ):
            server.logger.debug(
                "Allowing access based on membership in managing group"
            )
            message = 'User is group manager'
            status_code = 200
            return True, message, status_code
        else:
            server.logger.debug( "Principal not in manager group" )
    else:
        server.logger.debug( "no managedBy- skipping check" )

    message = 'User is not allowed access'
    status_code = 403
    return False, message, status_code

@server.route( "/swift/account", methods=('GET','POST') )
def auth_helper():
    form = forms.AuthHelper()
    if form.validate_on_submit():
        return redirect( 'swift/account/{}'.format(form.acct_name.data) )
    return render_template( 'auth_helper.html', form = form )

@server.route("/swift/account/<acct_name>")
@requires_auth
def auth(acct_name):
    server.logger.setLevel(logging.DEBUG)
    binddn = request.authorization.username
    bindpw = request.authorization.password
    username = binddn
    # first see if there is a specific swift group that controls access
    is_ok, message, status_code = validate(
        username, acct_name, binddn, bindpw, '_swift_grp')
    # but if _swift_grp is not found use the default group ending _grp
    if message.startswith('No directory group for account'):
        is_ok, message, status_code = validate(
            username, acct_name, binddn, bindpw, '_grp')

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
                r = jsonify(
                    message='Account {} not found on server'.format( acct_name ) )
                r.status_code = 404
                return r
    else:
        server.logger.debug( "no access for user" )
        r = jsonify( message = message )
        r.status_code = status_code
        return r


@server.route("/aws/get_hutchnet_id")
# @requires_aws_auth
def get_hutchnet_id_from_aws_creds():
    "once user is logged in, give them hutchnet id associated w/their login creds"
    message = """
This URL has been deprecated. For assistance with your AWS account, please
contact helpdesk@fredhutch.org.
    """
    return message

@server.route("/aws/account")
# @requires_auth
def get_aws_creds():
    message = """
This URL has been deprecated. For assistance with your AWS account, please
contact helpdesk@fredhutch.org.
    """
    return message


@server.route("/swift/account/access/<acct_name>/<username>")
@requires_auth
def verify(acct_name, username):
    server.logger.setLevel(logging.DEBUG)
    binddn = request.authorization.username
    bindpw = request.authorization.password

    # first see if there is a specific swift group that controls access
    is_ok, message, status_code = validate(
        username, acct_name, binddn, bindpw, '_swift_grp')
    # but if _swift_grp is not found use the default group ending _grp
    if message.startswith('No directory group for account'):
        is_ok, message, status_code = validate(
            username, acct_name, binddn, bindpw, '_grp')

    if is_ok:
        server.logger.debug("returning credential")
        r = ""
        with open( config.keyfile, 'rb' ) as keyfile:
            creds = csv.DictReader(keyfile, fieldnames = config.key_fields )
            for cred in creds:
                if cred['account'] == 'Swift_{}'.format(acct_name):
                    r = jsonify(
                        message = "User {} has access to {}".format(
                        username, acct_name )
                    )
                    r.status_code = 200
                    return r
            if r == "":
                r = jsonify( message='Credentials for account not found' )
                r.status_code = 404
                return r

    else:
        server.logger.debug( "no access for user" )
        r = jsonify( message = message )
        r.status_code = status_code
        return r



@server.route("/get_depts", methods=['GET'])
# @support_jsonp
def get_depts():
    with open(config.depts_file) as depts_file:
        obj = json.load(depts_file)
    keys = obj.keys()
    depts = []
    for key in keys:
        key = key.replace("_grp", "")
        segs = key.split("_")
        if len(segs) < 5:
            depts.append(key)
    depts.sort()
    ret = "callback(" + json.dumps(depts) + ")"
    return Response(ret, mimetype="application/json")
