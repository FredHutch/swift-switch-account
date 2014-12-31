#!/usr/bin/env python

from flask import Flask
from os.path import isfile
import logging
from logging.handlers import SysLogHandler
import sw2srv.config as config

server = Flask(__name__)

syslog = logging.handlers.SysLogHandler( address='/dev/log' )
syslog.setFormatter(
    logging.Formatter( 'sw2srv: %(levelname)s %(message)s')
)
syslog.setLevel(logging.DEBUG)
server.logger.addHandler(syslog)
server.logger.setLevel(logging.DEBUG)

if not isfile( config.keyfile ):
    server.logger.error( "no keyfile found at {}".format(config.keyfile ) )
    raise IOError( "no keyfile found at {}".format(config.keyfile ) )

import sw2srv.views

