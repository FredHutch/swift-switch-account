#
# swift-switch-server configuration
#
# A basic configuration file.  Write as python.  Changing values here
# requires restarting the flask server when its not run in debug mode.

# KEYFILE

# path to csv file containing key data
keyfile = '/path/to/keys.csv'
aws_keyfile = '/path/to/aws_keys.csv'
#
# Order of account, password, and key in file as tuple/list
key_fields = ('account','password','key')
aws_keyfields = ('hutchnetid', 'access_key', 'secret_key')


# SERVER CONFIGURATION
#
# Interfaces to listen on when running the flask server.  Passed into
# "run"
host = '0.0.0.0'
port = 5000
debug = True
# Use flask SSL. Not needed if this is run using Apache or other
# web server with SSL
use_ssl = True
cert = '/path/to/certs/test.crt'
key = '/path/to/certs/test.key'

# LDAP CONFIGS

# LDAP search base
base = "dc=base,dc=org"

# URI for LDAP server
ldap_url = "ldaps://ldap.foo.org"
