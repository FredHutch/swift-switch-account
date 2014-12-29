#!/usr/bin/env python

from sw2srv import server

server.run(
    debug = True,
    ssl_context = (
        '/home/mrg/Work/swift-switch-account/certs/test.crt',
        '/home/mrg/Work/swift-switch-account/certs/test.key'
    )

)
