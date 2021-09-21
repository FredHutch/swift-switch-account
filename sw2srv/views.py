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





@server.route( "/swift/account", methods=('GET','POST') )
def auth_helper():
    message = """
This URL has been deprecated. For assistance with your AWS account, please
contact helpdesk@fredhutch.org.
    """
    return message


@server.route("/swift/account/<acct_name>")
@requires_auth
def auth(acct_name):
    message = """
This URL has been deprecated. For assistance with your AWS account, please
contact helpdesk@fredhutch.org.
    """
    return message


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
# @requires_auth
def verify(acct_name, username):
    message = """
This URL has been deprecated. For assistance with your AWS account, please
contact helpdesk@fredhutch.org.
    """
    return message


@server.route("/get_depts", methods=['GET'])
# @support_jsonp
def get_depts():
    message = """
This URL has been deprecated. For assistance with your AWS account, please
contact helpdesk@fredhutch.org.
    """
    return message

