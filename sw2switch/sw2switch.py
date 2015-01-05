#!/usr/bin/python

import argparse
import logging
import os
import os.path
import sys
import requests
import getpass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'account',
        help = "retrieve credentials for account <account>"
    )
    parser.add_argument(
        '--server-url',
        help = "URL of server with account data"
    )
    parser.add_argument(
        '--persist',
        default = False,
        help = "write credentials to $HOME/.swiftrc"
    )
    parser.add_argument(
        '--debug',
        action = "store_true",
        help = "log level for client"
    )
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig( level=logging.DEBUG )
    logging.debug( 'arguments: %s', args )

    # If server URL is unspecified, look for "SW2_URL" in current environment

    account = args.account
    server_url = args.server_url

    logging.debug(
        'asking {} for credentials for {}'.format( server_url, account )
    )

    if not server_url:
        try:
            server_url = os.environ[ 'SW2_URL' ]
        except KeyError:
            logging.error( "Server URL is unset (not in arguments or SW2_URL)" )
            sys.exit(1)

    # Add account name to URL
    server_url = '/'.join( [ server_url, account ] )
    logging.debug( 'final url is {}'.format( server_url ) )

    # Get user authentication credentials
    user = getpass.getuser()
    passwd = getpass.getpass( 'Enter password for {}: '.format(user) )

    # Get account credentials from server_url
    r = requests.get( server_url, verify = True, auth=( user, passwd ) )
    if r.status_code == 200:
        creds = r.json()
        logging.debug(
            "got credentials for account {}".format( creds['account'] )
        )

        creds['url'] = 'https://tin/some/crap'

        export = "ST_AUTH={} ; export ST_AUTH ;".format( creds['url'] )
        export = (
            export + "ST_USER={} ; export ST_USER ;".format( creds['account'] )
        )
        export = (
            export + "ST_KEY={} ; export ST_KEY".format( creds['password'] )
        )
        print export
        
        

    elif r.status_code == 401:
        logging.error(
            "invalid username/password supplied to server"
        )
    else:
        logging.error(
            "error retrieving credentials ({}) from server".format( r.status_code )
        )



