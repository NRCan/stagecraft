#!/bin/bash

set -e

basedir=$(dirname $0)
pep8 --ignore=E201,E202,E241,E251 --exclude=migrations,tests,build,venv "$basedir"
pep8 --ignore=E201,E202,E241,E251,E501 "$basedir/tests"
