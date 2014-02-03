#!/bin/bash

set -o pipefail

export DJANGO_SETTINGS_MODULE="stagecraft.settings.development"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python manage.py test

function display_result {
    RESULT=$1
    EXIT_STATUS=$2
    TEST=$3

    if [ $RESULT -ne 0 ]; then
      echo
      echo -e "\033[31m$TEST failed\033[0m"
      echo
      exit $EXIT_STATUS
    else
      echo
      echo -e "\033[32m$TEST passed\033[0m"
      echo
    fi
}

basedir=$(dirname $0)
outdir="$basedir/out"

rm -f "$outdir/*"
mkdir -p "$outdir"

# run style check
$basedir/pep-it.sh | tee "$outdir/pep8.out"
display_result $? 3 "Code style check"
