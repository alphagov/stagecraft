#!/bin/bash -e

set -o pipefail

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

# cleanup output dir
mkdir -p "$outdir"
rm -f "$outdir/*"
rm -f ".coverage"

if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE="stagecraft.settings.development"
fi

if [ -d "venv" ]; then
    source venv/bin/activate
fi

# clean up stray python bytecode
find $basedir/stagecraft -iname '*.pyc' -exec rm {} \+
find $basedir/stagecraft -iname '__pycache__' -exec rmdir {} \+

# probably going to need to install dependencies
pip install -r requirements/ci.txt

if [ -z "$NO_AUTOPEP8" ]; then
  autopep8 -i -r stagecraft --exclude '00*.py'
fi

# run style check
$basedir/pep-it.sh | tee "$outdir/pep8.out"
display_result $? 3 "Code style check"

# run unit tests
python manage.py test --with-coverage --cover-package=datasets --with-doctest
display_result $? 1 "Unit tests"
