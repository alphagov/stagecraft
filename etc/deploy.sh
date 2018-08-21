#!/usr/bin/env bash

set -e

function cycle_app() {
    local app_name=$1

    # ensure we don't get caught out by caching problems
    # caused by the same app code having been pushed under a different
    # app name in the same space (for testing purposes, perhaps).
    cf delete -f ${app_name}
    cf push ${app_name} --no-start
}
if [ -z "$1" ]; then
    echo "Missing PAAS space argument"
    echo "  deploy.sh staging|production"
    exit 1
fi

PAAS_SPACE=$1
wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
echo "deb http://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list
sudo apt-get update && sudo apt-get install cf-cli

cf login -u $PAAS_USER -p $PAAS_PASSWORD -a https://api.cloud.service.gov.uk -o gds-performance-platform -s $PAAS_SPACE

cycle_app performance-platform-stagecraft-web
# set environmental variables
cf set-env performance-platform-stagecraft-web SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-stagecraft-web FERNET_KEY $APP_FERNET_KEY
cf set-env performance-platform-stagecraft-web SIGNON_CLIENT_ID $SIGNON_CLIENT_ID
cf set-env performance-platform-stagecraft-web ENV_HOSTNAME $PAAS_SPACE.cloudapps.digital
cf set-env performance-platform-stagecraft-web GOVUK_APP_DOMAIN $GOVUK_APP_DOMAIN
cf set-env performance-platform-stagecraft-web GOVUK_WEBSITE_ROOT $GOVUK_WEBSITE_ROOT
cf set-env performance-platform-stagecraft-web BACKDROP_PUBLIC_DOMAIN $BACKDROP_PUBLIC_DOMAIN
cf set-env performance-platform-stagecraft-web REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER
cf set-env performance-platform-stagecraft-web STAGECRAFT_COLLECTION_ENDPOINT_TOKEN $STAGECRAFT_COLLECTION_ENDPOINT_TOKEN
cf set-env performance-platform-stagecraft-web TRANSFORMED_DATA_SET_TOKEN $TRANSFORMED_DATA_SET_TOKEN
cf set-env performance-platform-stagecraft-web MIGRATION_SIGNON_TOKEN $MIGRATION_SIGNON_TOKEN
cf set-env performance-platform-stagecraft-web DJANGO_SETTINGS_MODULE "stagecraft.settings.$PAAS_SPACE"
# now rerun with the environment variables
cf push performance-platform-stagecraft-web

cycle_app performance-platform-stagecraft-celery-worker
cf set-env performance-platform-stagecraft-celery-worker SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-stagecraft-celery-worker FERNET_KEY $APP_FERNET_KEY
cf set-env performance-platform-stagecraft-celery-worker SIGNON_CLIENT_ID $SIGNON_CLIENT_ID
cf set-env performance-platform-stagecraft-celery-worker GOVUK_APP_DOMAIN $GOVUK_APP_DOMAIN
cf set-env performance-platform-stagecraft-celery-worker GOVUK_WEBSITE_ROOT $GOVUK_WEBSITE_ROOT
cf set-env performance-platform-stagecraft-celery-worker BACKDROP_PUBLIC_DOMAIN $BACKDROP_PUBLIC_DOMAIN
cf set-env performance-platform-stagecraft-celery-worker REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER
cf set-env performance-platform-stagecraft-celery-worker DJANGO_SETTINGS_MODULE "stagecraft.settings.$PAAS_SPACE"
cf push performance-platform-stagecraft-celery-worker

cycle_app performance-platform-stagecraft-celery-beat
cf set-env performance-platform-stagecraft-celery-beat SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-stagecraft-celery-beat FERNET_KEY $APP_FERNET_KEY
cf set-env performance-platform-stagecraft-celery-beat SIGNON_CLIENT_ID $SIGNON_CLIENT_ID
cf set-env performance-platform-stagecraft-celery-beat GOVUK_APP_DOMAIN $GOVUK_APP_DOMAIN
cf set-env performance-platform-stagecraft-celery-beat GOVUK_WEBSITE_ROOT $GOVUK_WEBSITE_ROOT
cf set-env performance-platform-stagecraft-celery-beat BACKDROP_PUBLIC_DOMAIN $BACKDROP_PUBLIC_DOMAIN
cf set-env performance-platform-stagecraft-celery-beat REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER
cf set-env performance-platform-stagecraft-celery-beat DJANGO_SETTINGS_MODULE "stagecraft.settings.$PAAS_SPACE"
cf push performance-platform-stagecraft-celery-beat

cycle_app performance-platform-stagecraft-celery-cam
cf set-env performance-platform-stagecraft-celery-cam SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-stagecraft-celery-cam FERNET_KEY $APP_FERNET_KEY
cf set-env performance-platform-stagecraft-celery-cam SIGNON_CLIENT_ID $SIGNON_CLIENT_ID
cf set-env performance-platform-stagecraft-celery-cam GOVUK_APP_DOMAIN $GOVUK_APP_DOMAIN
cf set-env performance-platform-stagecraft-celery-cam GOVUK_WEBSITE_ROOT $GOVUK_WEBSITE_ROOT
cf set-env performance-platform-stagecraft-celery-cam BACKDROP_PUBLIC_DOMAIN $BACKDROP_PUBLIC_DOMAIN
cf set-env performance-platform-stagecraft-celery-cam REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER
cf set-env performance-platform-stagecraft-celery-cam DJANGO_SETTINGS_MODULE "stagecraft.settings.$PAAS_SPACE"
cf push performance-platform-stagecraft-celery-cam

cycle_app performance-platform-stagecraft-flower
cf set-env performance-platform-stagecraft-flower REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER
cf set-env performance-platform-stagecraft-flower FLOWER_BASIC_AUTH $FLOWER_BASIC_AUTH
cf set-env performance-platform-stagecraft-flower CELERY_CONFIG_MODULE "stagecraft.settings.rediss"
cf push performance-platform-stagecraft-flower

# create and map routes
cf map-route performance-platform-stagecraft-web cloudapps.digital --hostname performance-platform-stagecraft-$PAAS_SPACE
cf map-route performance-platform-stagecraft-flower cloudapps.digital --hostname performance-platform-stagecraft-flower-$PAAS_SPACE
