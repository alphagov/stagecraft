#!/bin/bash -e

basedir=$(dirname $0)
pep8 --exclude=migrations,tests,build,venv "$basedir"
pep8 "$basedir/stagecraft/apps/datasets/tests"
