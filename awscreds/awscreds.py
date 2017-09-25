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

def main(): # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    'Do all the work.'
    url = "https://toolbox.fhcrc.org/sw2srv/aws/account"


    parser = argparse.ArgumentParser(formatter_class=\
        argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing sections of file.')
    parser.add_argument('--config-dir',
                        default=os.path.join(os.getenv('HOME'),
                                             '.aws'),
                        help='Directory to write AWS config/credentials files.')
    configparser.DEFAULTSECT = 'default'
    parser.add_argument('--section', default=configparser.DEFAULTSECT,
                        help='Section of credential file.')
    args, unknown = parser.parse_known_args()
    if unknown:
        print("Unknown arguments are present!")
        sys.exit(1)

    def section(filename):
        """determine section name"""
        if args.section == 'default' or filename.endswith("credentials"):
            return args.section
        return "profile {}".format(args.section)

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

    configdir = args.config_dir
    config_file = os.path.join(configdir, "config")
    credentials_file = os.path.join(configdir, "credentials")


    if not os.path.isdir(configdir):
        if os.path.exists(configdir):
            print("{} exists but is not a directory!")
            sys.exit(1)
        os.makedirs(configdir)

    config = configparser.ConfigParser()
    credentials = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
    if os.path.exists(credentials_file):
        credentials.read(credentials_file)

    def create_section(parser, filename):
        """does file have section?"""
        if six.PY2 and args.section == configparser.DEFAULTSECT:
            has_section = bool(parser.defaults())
        else:
            has_section = parser.has_section(section(filename))
        if has_section:
            print("File {} already has section '{}', ".format(filename,
                                                              section(filename)),
                  end="")
            if args.force:
                print("overwriting....")
                parser.remove_section(section(filename))
            else:
                print("exiting.\nUse --force to overwrite.")
                sys.exit(1)


    create_section(config, config_file)
    create_section(credentials, credentials_file)

    if six.PY3 or not section(config_file) == configparser.DEFAULTSECT:
        config.add_section(section(config_file))
    if six.PY3 or not section(credentials_file) == configparser.DEFAULTSECT:
        credentials.add_section(section(credentials_file))
    credentials.set(section(credentials_file), 'aws_access_key_id', access_key)
    credentials.set(section(credentials_file), 'aws_secret_access_key', secret_key)
    config.set(section(config_file), 'region', "us-west-2")
    s3conf = """
max_concurrent_requests = 100
max_queue_size = 10000
multipart_threshold = 64MB
multipart_chunksize = 16MB
"""
    config.set(section(config_file), "s3", s3conf)

    with open(config_file, "w") as filehandle:
        config.write(filehandle)
    with open(credentials_file, "w") as filehandle:
        credentials.write(filehandle)
    os.chmod(credentials_file, 0o600) # python 2/3 compatibility
    os.chmod(config_file, 0o600) # python 2/3 compatibility

    print("Configuration written to {}.".format(config_file))
    print("Credentials written to {}.".format(credentials_file))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Exit !')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0) # pylint: disable=protected-access
