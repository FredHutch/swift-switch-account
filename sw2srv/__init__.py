#!/usr/bin/env python

from flask import Flask
import logging
import logging.handlers

server = Flask(__name__)

#syslog = logging.handlers.SysLogHandler( address='/dev/log' )
#syslog.setLevel(logging.WARNING)
#server.logger.addHandler(syslog)

server.logger.setLevel(logging.DEBUG)

import sw2srv.views

