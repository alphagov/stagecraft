# Stagecraft

Application for managing performance platform datasets.

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

# Initialising/adding models

Before the server is run for the first time, and whenever a model is changed,
the local database (called ``database.sqlite3``) needs to be synced.

*Note: The first time you `syncdb`, you'll be asked to setup a `superadmin`.*

```
python manage.py syncdb --migrate
```


In order to generate migrations for a newly added model run:

```
python manage.py schemamigration datasets --auto
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

# Running


To run the development server:

```
python manage.py runserver 0.0.0.0:8080
```

**NOTE** If you're using pp-development, until we do the puppet story you'll
need to add a firewall rule: ``sudo ufw allow in 8080``

You should now be able to access the [admin control panel](http://stagecraft.perfplat.dev:8080/admin/) (note the trailing slash)
