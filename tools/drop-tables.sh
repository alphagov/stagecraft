#!/bin/bash

sudo su postgres <<'EOF'
psql -c 'DROP SCHEMA public CASCADE;' stagecraft
psql -c 'CREATE SCHEMA public;' stagecraft
psql -c 'ALTER SCHEMA public OWNER TO stagecraft;' stagecraft
EOF
