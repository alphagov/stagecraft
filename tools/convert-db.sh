#!/bin/bash
set -euo pipefail
sudo su postgres <<'EOF'
psql -c 'DROP SCHEMA public CASCADE;' stagecraft
psql -c 'DROP DATABASE stagecraft;'
/usr/lib/postgresql/9.3/bin/createdb --port='5432' --owner='postgres' --template=template0 --encoding 'SQL_ASCII' --locale=en_GB.UTF-8  'stagecraft'
psql -c 'CREATE SCHEMA public;' stagecraft
psql -c 'ALTER SCHEMA public OWNER TO stagecraft;' stagecraft
psql -f '/tmp/stagecraft.prod.sql' stagecraft
psql -c "ALTER USER stagecraft WITH PASSWORD 'securem8'"
EOF
# psql -c 'DROP FUNCTION streaming_slave_check();'
# pg_dump --encoding=SQL_ASCII --oids --clean stagecraft -f '/tmp/stagecraft.utf8.sql'
# psql -c 'drop database stagecraft;'
# /usr/lib/postgresql/9.3/bin/createdb --port='5432' --owner='postgres' --template=template0 --encoding 'SQL_ASCII' --locale=en_GB.UTF-8  'stagecraft'
# psql -f '/tmp/stagecraft.utf8.sql' stagecraft
# psql -c "ALTER USER stagecraft WITH PASSWORD 'securem8'"
