#!/usr/bin/python

__version__='0.1.2'

import argparse
import logging
import os
import os.path
import sys
import requests
import getpass

#FIXME: crappy hardcoded thing
v1AuthUrl = 'https://tin.fhcrc.org/auth/v1.0'
v2AuthUrl = 'https://tin.fhcrc.org/auth/v2.0'

def sh(creds, auth_version, persist=False):
    export = []
    if auth_version == 'v1':
        export.append(
            "unsetenv OS_USERNAME OS_PASSWORD OS_TENANT_NAME OS_AUTH_URL" )
        export.append( "setenv ST_USER {}".format( creds['account'] ) )
        export.append( "setenv ST_KEY {}".format( creds['password'] ) )
        export.append( "setenv ST_AUTH {}".format( v1AuthUrl ) )
    else:
        export.append(
            "unsetenv ST_USER ST_KEY ST_AUTH" )
        export.append( "setenv OS_USERNAME {}".format( creds['user'] ) )
        export.append( "setenv OS_TENANT_NAME {}".format( creds['account'] ) )
        export.append( "setenv OS_PASSWORD {}".format( creds['password'] ) )
        export.append( "setenv OS_AUTH_URL {}".format( v2AuthUrl ) )

    print ";".join( export )

    if persist:
        rcfile = os.environ[ 'HOME' ] + "/.swiftrc"
        logging.debug( "writing to {}".format( rcfile ) )
        f = open( rcfile, 'w' )
        f.write( "\n".join( export ) )
        f.close()
        os.chmod( rcfile, 0600 )
        logging.info( "saved Swift credentials" )

def csh(creds, auth_version, persist=False):
    export = []
    if auth_version == 'v1':
        export.append(
            "unsetenv OS_USERNAME OS_PASSWORD OS_TENANT_NAME OS_AUTH_URL" )
        export.append( "setenv ST_USER {}".format( creds['account'] ) )
        export.append( "setenv ST_KEY {}".format( creds['password'] ) )
        export.append( "setenv ST_AUTH {}".format( v1AuthUrl ) )
    else:
        export.append(
            "unsetenv ST_USER ST_KEY ST_AUTH" )
        export.append( "setenv OS_USERNAME {}".format( creds['user'] ) )
        export.append( "setenv OS_TENANT_NAME {}".format( creds['account'] ) )
        export.append( "setenv OS_PASSWORD {}".format( creds['password'] ) )
        export.append( "setenv OS_AUTH_URL {}".format( v2AuthUrl ) )

    print ";".join( export )

    if persist:
        rcfile = os.environ[ 'HOME' ] + "/.swift.cshrc"
        logging.debug( "writing to {}".format( rcfile ) )
        f = open( rcfile, 'w' )
        f.write( "\n".join( export ) )
        f.close()
        os.chmod( rcfile, 0600 )
        logging.info( "saved Swift credentials" )

shell_output = {
    'sh': sh,
    'ksh': sh,
    'bash': sh,
    'zsh': sh,
    'csh': csh,
    'tcsh': csh
}


class LocalParser( argparse.ArgumentParser ):
    def error( self, message ):
        sys.stderr.write( "Error: too few arguments\n" )
        sys.stderr.write( "usage: sw2account lastname_f\n" )
        sys.stderr.write(
           "use \"sw2account --help\" for full help information\n" )
        sys.exit(1)

    def print_help( self ):
        self._print_message( self.format_help(), sys.stderr )
        sys.exit(0)

def return_v1_auth( args ):
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
    r = requests.get( server_url, verify = args.verify_ssl, auth=( user, passwd ) )
    if r.status_code == 200:
        creds = r.json()
        logging.debug(
            "got credentials for account {}".format( creds['account'] )
        )

        creds['url'] = 'https://tin/some/crap'
        shell_output[ args.shell ](
            creds=creds,
            persist=args.persist,
            auth_version=args.auth_version
        )

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
    elif r.status_code == 404:
        try:
            message = r.json()['message']
        except KeyError:
            logging.error( "404 returned from server with no message" )
            sys.exit(1)
        logging.error("{} (HTTP{})".format(
                 message, r.status_code
            )
        )
    else:
        logging.error(
            "error {} retrieving credentials from server".format(
                r.status_code
            )
        )

def return_v2_auth( args ):
    # authentication is done using Swiftstack version 2 authentication

    # requires additional "tenant name" in addition to username and password
    tenant = args.account

    # take username password from currently logged in user
    user = getpass.getuser()
    passwd = getpass.getpass( 'Enter password for {}: '.format(user) )




if __name__ == "__main__":
    #parser = LocalParser()
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(
        dest = "auth_version", help='authentication version to use'
    )

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
        '--version', '-v',
        help = "show script version",
        action = 'version',
        version = "sw2account version {}".format( __version__)
    )
    parser.add_argument(
        '--debug',
        action = "store_true",
        help = "log level for client"
    )

    v1parser = subparser.add_parser('v1', help='use version 1 authentication')
    v1parser.add_argument(
        '--server-url',
        help = "URL of server with account data"
    )
    v1parser.add_argument(
        '--no-verify-ssl',
        action = "store_false",
        dest = "verify_ssl",
        help = "verify ssl certification",
    )
    v1parser.add_argument(
        '--verify-ssl',
        action = "store_true",
        dest = "verify_ssl",
        help = "verify ssl certification",
    )

    v2parser = subparser.add_parser('v2', help='use version 2 authentication')

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

    if args.auth_version == 'v1':
        return_v1_auth( args )


