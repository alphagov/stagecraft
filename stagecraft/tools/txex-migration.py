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

column_positions = {
    'names_name': 7,
    'names_slug': 8,
    'names_service_name': 5,
    'names_service_slug': 6,
    'names_tx_id_column': 17
}
from spreadsheets import SpreadsheetMunger

munger = SpreadsheetMunger(column_positions)
print munger.load(username, password)
