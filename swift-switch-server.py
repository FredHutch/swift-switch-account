#!/usr/bin/env python

from sw2srv import server
from sw2srv import config

if config.use_ssl:
    server.run(
        debug = config.debug,
        host = config.host,
        port = config.port,
        ssl_context = ( config.cert, config.key )
    )
else:
    server.run(
        debug = config.debug,
        host = config.host,
        port = config.port,
    )

