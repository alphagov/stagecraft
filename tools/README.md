## Import production database

**Outside VM**
```
cd ~/govuk/pp-deployment/fabric
# Download production db to local /tmp
fab production backup.dump_postgresql_to_local_file:path/to/shared/folder_on_vagrant_machine/{name_of_db_dump}.sql.gz
```

**Inside VM**
```
# Copy db dump file to /tmp/ on vagrant machine
cp path/to/shared/folder_on_vagrant_machine/{name_of_db_dump}.sql.gz /tmp/
cd /var/apps/stagecraft && workon stagecraft
./tools/convert-db.sh /tmp/{name_of_db_dump}.sql.gz
```
