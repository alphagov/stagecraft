# Running scripts

These scripts should be run from the repository root,
with an activated virtualenv.

You may also need to set the environment variable `DJANGO_SETTINGS_MODULE`
appropriately.

Invoke a script as follows:

```
python -m stagecraft.tools.script arg1 arg2
```

## (import_dashboards.py) Importing data from the Transactions Explorer Google spreadsheet

The application in `backdrop-transactions-explorer-collector` is used to import data
from the Transactions Explorer Google spreadsheet into the Backdrop database every quarter.

As a follow-on step, it is necessary to create or update dashboard and module
configuration data in the Stagecraft database, so that the data imported into
Backdrop can be presented on the Performance Platform.

To do so:

1. Get access to the Google Spreadsheet
2. Set up environment variables needed by the import
3. Run the import

### Get access to the Google spreadsheet

When `import_dashboards.py` is run, its first task is to collect data from the Google spreadsheet.

Access to the Google spreadsheet is via OAuth 2.0 using the Python `oauth2client`. For this,
you will need a Google Service Account, which is an account that belongs to an application
instead of an individual end user.

You can set up a Service Account in the Google Development Console. Simply log in,
create a project and then add Service Account credentials for this project of key
type 'JSON'. Download the JSON credentials files.

Now ask the on-boarding team to grant access to the Google spreadsheet for the client
email address that can be found in JSON credentials file.

### Set up environment variables needed by the import

Two environment variables should be set before running the script:

SUMMARIES_URL - location of service aggregate data in Backdrop

```bash
export SUMMARIES_URL='http://www.performance.service.gov.uk/data/service-aggregates/latest-dataset-values'
```

GOOGLE_APPLICATION_CREDENTIALS - location of the JSON credentials file generated in previous step

```bash
export GOOGLE_APPLICATION_CREDENTIALS='path/to/file'
```

### Run the import in development

```bash
export DJANGO_SETTINGS_MODULE=stagecraft.settings.development
```

```
python -m stagecraft.tools.import_dashboards
```

The script accepts the flags: --update, --commit and --publish.

### Run the import in other environments

```bash
sudo -u deploy DJANGO_SETTINGS_MODULE=stagecraft.settings.production GOOGLE_APPLICATION_CREDENTIALS='path/to/file' SUMMARIES_URL='http://www.performance.service.gov.uk/data/service-aggregates/latest-dataset-values' venv/bin/python -m stagecraft.tools.import_dashboards
```

## (import_organisations.py) Link imported dashboards to an organisation

After `import_dashboards.py` has run, `import_organisations.py` needs to be run to associate a dashboard with an organisation.  These organisations are used in spotlight as service groups to filter services.

`import_organisations.py` uses the same environment variables that were set up for `import_dashboards.py`

`import_organisations.py` reuses the two pickle files (names_values.pickle, tx_values.pickle) created by the `import_dashboards.py` script.


### Run the import in development

```
python -m stagecraft.tools.import_organisations
```

### Run the import in other environments

```bash
sudo -u deploy DJANGO_SETTINGS_MODULE=stagecraft.settings.production GOOGLE_APPLICATION_CREDENTIALS='path/to/file' venv/bin/python -m stagecraft.tools.import_organisations
```
