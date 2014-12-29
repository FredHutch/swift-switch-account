#
# swift-switch-server configuration
#
# A basic configuration file.  Write as python.  Changing values here
# requires restarting the flask server when its not run in debug mode.

# KEYFILE

# path to csv file containing key data
keyfile = '/home/mrg/Work/swift-switch-account/keys.csv'

# Order of account, password, and key in file as tuple/list
key_fields = ('account','password','key')

# LDAP CONFIGS

# LDAP search base
base = "dc=fhcrc,dc=org"

# URI for LDAP server
ldap_url = "ldaps://dc.fhcrc.org"

# Run flask in debug mode
debug = True

# SSL CONFIGURATION

# Use flask SSL. Not needed if this is run using Apache or other
# web server with SSL
use_ssl = True

# Certificate and key file for Flask SSL
cert = '/home/mrg/Work/swift-switch-account/certs/test.crt'
key = '/home/mrg/Work/swift-switch-account/certs/test.key'

