#!/usr/bin/env python

from flask import Flask
import logging

server = Flask(__name__)

import sw2srv.views

