#!/usr/bin/env python

import os
import sys

try:
    username = os.environ['GOOGLE_USERNAME']
    password = os.environ['GOOGLE_PASSWORD']
except KeyError:
    print("Please supply username (GOOGLE_USERNAME)"
          "and password (GOOGLE_PASSWORD) as environment variables")
    sys.exit(1)

from spreadsheets import load

print load(username, password)
