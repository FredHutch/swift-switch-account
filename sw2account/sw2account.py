#!/usr/bin/python

import argparse
import logging
import os
import os.path
import sys
import requests
import getpass

def sh( creds, persist ):
    export = (
        "ST_USER={} ; export ST_USER ;".format( creds['account'] )
    )
    export = (
        export + "ST_KEY={} ; export ST_KEY".format( creds['password'] )
    )
    print export
    if persist:
        rcfile = os.environ[ 'HOME' ] + "/.swiftrc"
        logging.debug( "writing to {}".format( rcfile ) )
        logging.error( "writing to .swiftrc not implemented yet!" )

def csh( creds, persist ):
    export = (
        "setenv ST_USER {} ; ".format( creds['account'] )
    )
    export = (
        export + "setenv ST_KEY {} ;".format( creds['password'] )
    )
    print export
    if persist:
        rcfile = os.environ[ 'HOME' ] + "/.swift.cshrc"
        logging.debug( "writing to {}".format( rcfile ) )
        logging.error( "writing to .swift.cshrc not implemented yet!" )

shell_output = {
    'sh': sh,
    'ksh': sh,
    'bash': sh,
    'zsh': sh,
    'csh': csh,
    'tcsh': csh
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'shell',
        help = "format output for shell <shell>",
        choices = shell_output.keys()
    )
    parser.add_argument(
        'account',
        help = "retrieve credentials for account <account>"
    )
    parser.add_argument(
        '--server-url',
        help = "URL of server with account data"
    )
    parser.add_argument(
        '--save', '--persist',
        dest = 'persist',
        action = 'store_true',
        help = "write credentials to $HOME/.swiftrc"
    )
    parser.add_argument(
        '--no-save', '--no-persist',
        dest = 'persist',
        action = 'store_false',
        help = "do not write credentials to $HOME/.swiftrc"
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

    if args.shell in [ 'bash', 'ksh', 'sh', 'zsh' ]:
        rcfile = os.environ[ 'HOME' ] + "/.swiftrc"
    elif args.shell in [ 'tcsh', 'csh' ]:
        rcfile = os.environ[ 'HOME' ] + "/.swift.cshrc"

    logging.debug( 'checking for rcfile: {}'.format(rcfile))
    if not os.path.isfile( rcfile ):
        parser.set_defaults( persist=True )
        logging.debug( "no rcfile: set persist default to true" )
    else:
        parser.set_defaults( persist=False )
        logging.debug( "found rcfile: set persist default to false" )

    args = parser.parse_args()
    logging.debug( "persist is set to {} after second wash".format(
        args.persist
    ))

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
        shell_output[ args.shell ](creds,args.persist)

    elif r.status_code == 401:
        logging.error(
            "invalid username/password supplied to server"
        )
    elif r.status_code == 403:
        logging.error(
            "user {} is not permitted to use {} ({})".format(
                user, account, r.status_code
            )
        )
    else:
        logging.error(
            "error {} retrieving credentials from server".format(
                r.status_code
            )
        )



