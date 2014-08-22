#!/bin/bash -e

basedir=$(dirname $0)
pep8 --exclude=migrations,build,venv "$basedir"
pep8 "$basedir/stagecraft/apps/datasets/tests"
pep8 "$basedir/stagecraft/apps/organisation/tests"
