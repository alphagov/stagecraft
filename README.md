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

# Running

Because we use environment-specific settings, you need to specify which
settings module to use in your environment. You'll need this for all commands
you run through ``manage.py``.

```
export DJANGO_SETTINGS_MODULE=stagecraft.settings.development
```

The first time you run, you'll need to initialise your local database, which is
called ``database.sqlite3``. You'll get the opportunity to make yourself an
administrator user.

```
python manage.py syncdb
```

Then, to actually run the development server:

```
python manage.py runserver 0.0.0.0:8080
```

**NOTE** If you're using pp-development, until we do the puppet story you'll
need to add a firewall rule: ``sudo ufw allow in 8080``

You should now be able to access the [admin control panel](http://www.perfplat.dev:8080/admin/) (note the trailing slash)
