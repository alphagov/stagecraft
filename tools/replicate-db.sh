#!/bin/bash

set -euo pipefail

#
# Replicate stagecraft postgresql db from a source host to a target host.
# Useful to import data from the preview environment to the development
# one.
#

if [ "$(hostname)" == "development-1" ]; then
    echo "This script should be run on the host machine, not your virtual machine!"
    exit 1
fi

if [ "$(basename $(pwd))" != 'tools' ]; then
    cd $(dirname $0)
fi


if [ $# -lt 1 ]; then
    echo "The script requires at least one argument."
    echo
    echo "Replicate backdrop data from a source host to a target host."
    echo
    echo "Usage:"
    echo "  $(basename $0) <user@source_host> [<target_host>]"
    echo
    echo "Example:"
    echo "  $(basename $0) youruser@postgresql dev.machine"
    echo "    This will run restore on the host machine against the specified target host"
    echo "  $(basename $0) youruser@postgresql"
    echo "    This will run restore from within the development VM"
    echo

    exit 2
fi


set +u
SOURCE_HOST=$1
DESTINATION_HOST=$2
set -u

DATE=$(date +'%Y%m%d-%H%M%S')
FILENAME="stagecraft-$DATE.tar.gz"

set -x

ssh -t $SOURCE_HOST "sudo su postgres -c \"cd && pg_dumpall --database=stagecraft --clean --oids | gzip > /tmp/${FILENAME}\""
scp $SOURCE_HOST:/tmp/$FILENAME .
ssh $SOURCE_HOST "sudo su postgres -c \"rm /tmp/${FILENAME}\""

if [ -z "$DESTINATION_HOST" ]
then
    pushd ../../pp-puppet
    vagrant ssh development-1 -c "cd /var/apps/stagecraft/tools && sudo service collectd stop"
    vagrant ssh development-1 -c "sudo su postgres -c \"psql -c \\\"DROP DATABASE stagecraft;\\\"\" -- -t"
    vagrant ssh development-1 -c "cd /var/apps/stagecraft/tools && sudo su postgres -c \"gunzip -c ${FILENAME} | psql\" -- -t"
    vagrant ssh development-1 -c "cd /var/apps/stagecraft/tools && sudo service collectd start"
    vagrant ssh development-1 -c "sudo su postgres -c \"psql -c \\\"ALTER ROLE stagecraft WITH PASSWORD 'securem8'\\\"\" -- -t"
    vagrant ssh development-1 -c "sudo su postgres -c \"psql -c \\\"ALTER ROLE stagecraft WITH SUPERUSER\\\"\" -- -t"
    popd
elif [ "$2" = 'govuk_dev' ]; then
    pushd ../../govuk-puppet/development
    vagrant ssh -c "sudo su postgres -c \"psql -c \\\"DROP DATABASE IF EXISTS stagecraft;\\\"\" -- -t"
    vagrant ssh -c "cd /var/govuk/stagecraft/tools && sudo su postgres -c \"gunzip -c ${FILENAME} | psql\" -- -t"
    vagrant ssh -c "sudo su postgres -c \"psql -c \\\"ALTER ROLE stagecraft WITH PASSWORD 'securem8'\\\"\" -- -t"
    vagrant ssh -c "sudo su postgres -c \"psql -c \\\"ALTER ROLE stagecraft WITH SUPERUSER\\\"\" -- -t"
    popd
else
    echo "Remote restore has not been implemented yet."
fi

# rm $FILENAME
