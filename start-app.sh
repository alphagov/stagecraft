#!/bin/bash -e

# Usage: start-app.py [listen port]
#
# - create and activate a virtualenv
# - install the requirements
# - run app in development mode

VENV_DIR=~/.virtualenvs/stagecraft

if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    mkdir -p ${VENV_DIR}
    virtualenv --no-site-packages "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

pip install -r requirements/development.txt

exec ./run_development.sh $*
