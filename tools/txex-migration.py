#!/usr/bin/env python

import os
import sys

import gspread


try:
    username = os.environ['GOOGLE_USERNAME']
    password = os.environ['GOOGLE_PASSWORD']
except KeyError:
    print "Please supply username (GOOGLE_USERNAME) and password (GOOGLE_PASSWORD) as environment variables"
    sys.exit(1)

gc = gspread.login(username, password)
ws = gc.open_by_key('0AiLXeWvTKFmBdFpxdEdHUWJCYnVMS0lnUHJDelFVc0E').worksheet('TX_Data')

rows = ws.row_values(1)
