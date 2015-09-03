#!/usr/bin/python

__version__='0.2.0'

import argparse
import logging
import os
import os.path
import sys
import requests
import getpass
import ConfigParser

def _persist( export, rcfile ):
    f = open( rcfile, 'w' )
    logging.debug( "writing to {}".format( rcfile ) )
    f.write( "\n".join( export ) )
    f.close()
    os.chmod( rcfile, 0600 )
    logging.info( "saved Swift credentials" )

def sh(creds, auth_version, savepw=False, persist=False ):
    export = []
    if auth_version == 'v1':
        export.append(
            "unset OS_USERNAME OS_PASSWORD OS_TENANT_NAME OS_AUTH_URL" )
        export.append(
            "unset OS_AUTH_TOKEN OS_STORAGE_URL" )
        export.append( "export ST_USER='{}'".format( creds['account'] ) )
        export.append( "export ST_KEY='{}'".format( creds['password'] ) )
        export.append( "export ST_AUTH='{}'".format( v1AuthUrl ) )
    else:
        export.append(
            "unset ST_USER ST_KEY ST_AUTH" )
        export.append( "export OS_USERNAME='{}'".format( creds['user'] ) )
        export.append(
            "export OS_TENANT_NAME='AUTH_Swift_{}'".format( creds['account'] ) )
        if savepw:
            export.append(
                "export OS_PASSWORD='{}'".format( creds['password'] ) )
        export.append( "export OS_AUTH_URL='{}'".format( v2AuthUrl ) )

    print ";".join( export )

    if persist:
        rcfile = os.environ[ 'HOME' ] + "/.swiftrc"
        logging.debug( "persisting environment variables" )
        _persist( export, rcfile )

def csh(creds, auth_version, savepw=False, persist=False ):
    export = []
    if auth_version == 'v1':
        export.append(
            "unsetenv OS_USERNAME OS_PASSWORD OS_TENANT_NAME OS_AUTH_URL" )
        export.append(
            "unsetenv OS_AUTH_TOKEN OS_STORAGE_URL" )
        export.append( "setenv ST_USER '{}'".format( creds['account'] ) )
        export.append( "setenv ST_KEY '{}'".format( creds['password'] ) )
        export.append( "setenv ST_AUTH '{}'".format( v1AuthUrl ) )
    else:
        export.append(
            "unsetenv ST_USER ST_KEY ST_AUTH" )
        export.append( "setenv OS_USERNAME '{}'".format( creds['user'] ) )
        export.append(
            "setenv OS_TENANT_NAME 'AUTH_Swift_{}'".format( creds['account'] ) )
        if savepw:
            export.append(
                "setenv OS_PASSWORD '{}'".format( creds['password'] ) )
        export.append( "setenv OS_AUTH_URL '{}'".format( v2AuthUrl ) )

    print ";".join( export )

    if persist:
        rcfile = os.environ[ 'HOME' ] + "/.swift.cshrc"
        logging.debug( "persisting environment variables" )
        _persist( export, rcfile )

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
    creds = {}
    # authentication is done using Swiftstack version 2 authentication

    # requires additional "tenant name" in addition to username and password
    creds['account'] = args.account

    # take username password from currently logged in user
    creds['user'] = getpass.getuser()
    if args.savepw:
        logging.warning( "Saving passwords is insecure and not recommended." )
        creds['password'] = getpass.getpass(
            'Enter password for {}: '.format( creds['user'] ) )
    logging.debug(
        "got credentials for account {}".format( creds['account'] )
    )
    if args.savepw:
        logging.debug( 'saving password in rc and environment' )

    shell_output[ args.shell ](
        creds=creds,
        persist=args.persist,
        savepw=args.savepw,
        auth_version=args.auth_version
    )

def add_common_args( aparser ):
    aparser.add_argument(
        'shell',
        help = "format output for shell <shell>",
        choices = shell_output.keys()
    )
    aparser.add_argument(
        'account',
        help = "retrieve credentials for account <account>"
    )
    aparser.add_argument(
        '--config',
        default = "/etc/sw2account.cfg",
        help = "configuration file to use (default=/etc/sw2account.cfg)"
    )
    aparser.add_argument(
        '--stack',
        default = "default",
        help = "stack name to authentication against (see configfile)"
    )
    aparser.add_argument(
        '--save', '--persist',
        dest = 'persist',
        action = 'store_true',
        help = "write credentials to $HOME/.swiftrc"
    )
    aparser.add_argument(
        '--no-save', '--no-persist',
        dest = 'persist',
        action = 'store_false',
        help = "do not write credentials to $HOME/.swiftrc"
    )
    aparser.add_argument(
        '--version', '-v',
        help = "show script version",
        action = 'version',
        version = "sw2account version {}".format( __version__)
    )
    aparser.add_argument(
        '--debug',
        action = "store_true",
        help = "log level for client"
    )

if __name__ == "__main__":

    # Get the config first
    # Need to prime the pump to find defaults
    tparse = argparse.ArgumentParser()
    tparse.add_argument(
        '--config',
        default = "/etc/sw2account.cfg",
        help = "configuration file to use (default=/etc/sw2account.cfg)"
    )
    tparse.add_argument(
        '--stack',
        default = "default",
        help = "stack name to authenticate against (see configfile)"
    )
    args, unknown = tparse.parse_known_args()

    # Read config file with defaults
    if not os.path.isfile( args.config ):
        logging.error( "missing config file %s", args.config )
        sys.exit(1)

    appdefaults = ConfigParser.ConfigParser()
    try:
        appdefaults.read( args.config )
        logging.debug( "reading config from %s", args.config )
    except ConfigParser.ParsingError:
        logging.error(
            "error reading configuration file %s - check format", args.config
        )
        sys.exit(1)

    try:
        v1AuthUrl = appdefaults.get( args.stack, 'v1AuthUrl' )
        v2AuthUrl = appdefaults.get( args.stack, 'v2AuthUrl' )
        auth_version_default = appdefaults.get(
            args.stack, 'auth_version_default' )
    except ConfigParser.NoSectionError:
        logging.error( "Stack '%s' not configured in configfile %s",
                      args.stack, args.config )
        sys.exit(1)
    except ConfigParser.NoOptionError:
        logging.error(
            "Configfile %s does not contain correct entries for stack '%s'",
            args.config, args.stack
        )
        sys.exit(1)


    # Fix argument order so that v1/v2 is first argument
    try:
        if sys.argv[1] not in ['v1','v2'] and (
            '-h' not in sys.argv or '--help' not in sys.argv ):
            if 'v1' in sys.argv:
                logging.debug( "reordering arguments to put v1 arg at head" )
                sys.argv.remove('v1')
                sys.argv.insert(1, 'v1')
            elif 'v2' in sys.argv:
                logging.debug( "reordering arguments to put v2 arg at head" )
                sys.argv.remove('v2')
                sys.argv.insert(1, 'v2')
            else:
                logging.debug( "setting default version" )
                sys.argv.insert(1, auth_version_default)
    except IndexError:
        pass

    #parser = LocalParser()
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(
        dest = "auth_version", help='authentication version to use'
    )

    v1parser = subparser.add_parser('v1', help='use version 1 authentication')
    add_common_args( v1parser )
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
    add_common_args( v2parser )

    v2parser.add_argument(
        '--save-password',
        action = "store_true",
        dest = "savepw",
        help = "save password in rc and environment- not recommended",
    )

    v2parser.add_argument(
        '--no-save-password',
        action = "store_false",
        dest = "savepw",
        help = "(default) do not save password in rc and environment- recommended",
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

    if args.auth_version == 'v1':
        return_v1_auth( args )
    elif args.auth_version == 'v2':
        return_v2_auth( args )


