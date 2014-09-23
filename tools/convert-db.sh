#!/bin/bash

red='\e[0;31m'
NC='\e[0m' # No Color

if [[ -z "$1" ]];
  then
    echo -e "${red}Error:${NC} Please pass in path to postgres dump"
    exit 1
fi

set -euo pipefail
# Stop collectd to avoid `database "stagecraft" is being accessed by other users`
sudo service collectd stop
sudo su postgres <<EOF
psql -c 'DROP SCHEMA public CASCADE;' stagecraft
psql -c 'DROP DATABASE stagecraft;'
/usr/lib/postgresql/9.3/bin/createdb --port='5432' --owner='postgres' --template=template0 --encoding 'SQL_ASCII' --locale=en_GB.UTF-8  'stagecraft'
psql -c 'CREATE SCHEMA public;' stagecraft
psql -c 'ALTER SCHEMA public OWNER TO stagecraft;' stagecraft
gunzip -c $1 | psql stagecraft
psql -c "ALTER USER stagecraft WITH PASSWORD 'securem8'"
psql -c "ALTER USER stagecraft WITH CREATEDB"
EOF
# psql -c 'DROP FUNCTION streaming_slave_check();'
# pg_dump --encoding=SQL_ASCII --oids --clean stagecraft -f '/tmp/stagecraft.utf8.sql'
# psql -c 'drop database stagecraft;'
# /usr/lib/postgresql/9.3/bin/createdb --port='5432' --owner='postgres' --template=template0 --encoding 'SQL_ASCII' --locale=en_GB.UTF-8  'stagecraft'
# psql -f '/tmp/stagecraft.utf8.sql' stagecraft
# psql -c "ALTER USER stagecraft WITH PASSWORD 'securem8'"
