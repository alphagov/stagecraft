# Stagecraft

[![Build Status](https://travis-ci.org/alphagov/stagecraft.png?branch=master)](https://travis-ci.org/alphagov/stagecraft?branch=master)

Application for managing performance platform.

# Installing

You'll need a virtualenv and if you're developing locally you'll want to use
``requirements/development.txt``:

```
mkdir venv
virtualenv venv
source venv/bin/activate
pip install -r requirements/development.txt
```

# Set Django environment

Because we use environment-specific settings, you need to specify which
settings module to use in your environment. You'll need this for all commands
you run through ``manage.py``.

```bash
export DJANGO_SETTINGS_MODULE=stagecraft.settings.development
```

# Initialising database

Before the server is run for the first time the database needs to be synced.

*Note: The first time you `syncdb`, you'll be asked to setup a `superadmin`.*
```
python manage.py syncdb
```

This project uses django-reversion to provide version control functionality.
Whenever a model is added it should be registered with the VersionAdmin class
(for an example, see
[here](https://github.com/alphagov/stagecraft/blob/add-django-reversion/stagecraft/apps/datasets/admin/data_type.py)
), and

```
python manage.py createinitialrevisions
```

should be used to populate the version database with an initial set of model
data. Depending on the number of rows in the database, this command can take a
while to execute.

**Need to setup a new superadmin?**
```
python manage.py createsuperuser --username=<ADMIN_USER_NAME> --email=<YOUR_EMAIL_ADDRESS>
```

**Need to delete all tables and start again?**
```
./tools/drop-tables.sh
```

# Adding a new model

After creating a model, create the initial migration script with:
```
python manage.py schemamigration [app_name] --initial
```

and then after making any changes to the model, create new migration scripts with:
```
python manage.py schemamigration [app_name] --auto
```

Apply migration scripts with:
```
python manage.py migrate [app_name]
```

# Running


To run the development server:

```
python manage.py runserver 0.0.0.0:3204
```

or do it the "bowl" way:

```
./start-app.sh
```

**NOTE** If you're using pp-development, until we do the puppet story you'll
need to add a firewall rule: ``sudo ufw allow in 3204``

You should now be able to access the [admin control panel](http://stagecraft.perfplat.dev:3204/admin/) (note the trailing slash)

# More on reversions

**NOTE: Reversions are not compatible with schema changes. Without special migrations, revisions saved before schema changes will be lost after these changes**

In contexts other than the Admin app there are things you must keep in mind in order to get reversions:

- When the operation is part of a request, the `reversion.middleware.RevisionMiddleware` middleware class will ensure that database modifying operations are accompanied by revisions on **registered models** (e.g. models with reversion.register(ModelName)).
- **NOTE:** When doing a request you will need to test this - this is our current understanding but we could be wrong...

**However**

> 'Warning: Due to changes in the Django 1.6 transaction handling, revision data will be saved in a separate database transaction to the one used to save your models, even if you set ATOMIC_REQUESTS = True. If you need to ensure that your models and revisions are saved in the save transaction, please use the reversion.create_revision() context manager or decorator in combination with transaction.atomic().'

**In Addition**

Outside of requests (e.g. in scripts) you will need to use the following:

- `import reversion`.
- Ensure the model is registered with `reversion.register(DataGroup)` if used in a context where the admin registration has not run.
- Run all database modifying operations in functions with the `@reversion.create_revision()` decorator or in the `reversion.create_revision():` context manager.

See [the docs](http://django-reversion.readthedocs.org/en/latest/api.html) for more info


# Migrating to new data set schemas.

As more schemas are added to describe data types we may find ourselves needing to migrate data sets to these new schemas. This is the purpose of `stagecraft/libs/mass_update/copy_dataset_with_new_mapping.py`.

To use this define a mapping of the format:

```python
mapping = {
    #finds an old data set to copy config and data from.
    'old_data_set': {
        'data_group': "carers-allowance",
        'data_type': "weekly-claims"
    },
    #a new data set with the data group and type here will be created
    #all config will be copied from the old data set 
    #except for anything specified here which will override this config
    #(in this case this is the auto_ids field)
    'new_data_set': {
        'auto_ids': '_timestamp,channel',
        'data_group': "carers-allowance",
        'data_type': "transactions-by-channel"
    },
    'data_mapping': {
        #this specifies a mapping of keys in the old data set data which will be changed
        'key_mapping': {
            "key": "channel",
            "value": "count"
        },
        #this specifies a mapping of values in the old data set data which will be changed
        'value_mapping': {
            "ca_clerical_received": "paper",
            "ca_e_claims_received": "digital"
        }
    }
}
``` 

Run it with:

```python
migrate_data_set(mapping['old_data_set'],
                 mapping['new_data_set'],
                 mapping["data_mapping"])

```

This will not delete the old data set. This should be done later when you are happy with the result.

Tests which further specify the behaviour of this can be found in `test_copy_dataset_with_new_mapping.py`.
