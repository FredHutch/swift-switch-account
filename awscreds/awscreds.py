#!/usr/bin/env python3

"""
Command-line client of the RESTful service at
https://toolbox.fhcrc.org/sw2srv/aws/account
Which returns the AWS credentials of the authenticated user.
This script will add those credentials to the user's ~/.aws/config file.
"""

from __future__ import print_function # needed for end="" to work in py2.7

# standard library imports
import sys
import argparse
import os
import getpass

# third-party imports; we assume these are available.
import requests
import six
from six.moves import configparser

def main(): # pylint: disable=too-many-branches, too-many-statements
    'Do all the work.'
    url = "https://toolbox.fhcrc.org/sw2srv/aws/account"


    parser = argparse.ArgumentParser(formatter_class=\
        argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing sections of file.')
    parser.add_argument('--config-file',
                        default=os.path.join(os.getenv('HOME'),
                                             '.aws',
                                             'config'),
                        help='AWS credential file.')
    configparser.DEFAULTSECT = 'default'
    parser.add_argument('--section', default=configparser.DEFAULTSECT,
                        help='Section of credential file.')
    args, unknown = parser.parse_known_args()
    if unknown:
        print("Unknown arguments are present!")
        sys.exit(1)
    if not args.section == 'default':
        args.section = "profile {}".format(args.section)


    username = os.getenv('USER')
    password = getpass.getpass("Enter password for {}: ".format(username))
    req = requests.get(url, auth=requests.auth.HTTPBasicAuth(username,
                                                             password))
    if not req.status_code == 200:
        if req.status_code == 401:
            print("Authentication error.")
        else:
            print("Error connecting to server.")
        sys.exit(1)
    result = req.json()
    access_key = result['access_key']
    secret_key = result['secret_key']

    configdir = os.path.dirname(args.config_file)
    if not os.path.isdir(configdir):
        if os.path.exists(configdir):
            print("{} exists but is not a directory!")
            sys.exit(1)
        os.mkdir(configdir)

    if os.path.isdir(args.config_file):
        print("{} is a directory; should be a file!")
        sys.exit(1)
    config = configparser.ConfigParser()
    if os.path.exists(args.config_file):
        config.read(args.config_file)
    if six.PY2 and args.section == configparser.DEFAULTSECT:
        has_section = bool(config.defaults())
    else:
        has_section = config.has_section(args.section)
    if has_section:
        # TODO better help here....
        print("Config file already has section '{}', ".format(args.section),
              end="")
        if args.force:
            print("overwriting....")
            config.remove_section(args.section)
        else:
            print("exiting.")
            sys.exit(1)
    if six.PY3 or not args.section == configparser.DEFAULTSECT:
        config.add_section(args.section)
    config.set(args.section, 'aws_access_key_id', access_key)
    config.set(args.section, 'aws_secret_access_key', secret_key)
    config.set(args.section, 'region', "us-west-2")

    with open(args.config_file, "w") as filehandle:
        config.write(filehandle)
    os.chmod(args.config_file, 0o600) # python 2/3 compatibility

    print("Configuration written to {}.".format(args.config_file))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Exit !')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0) # pylint: disable=protected-access
