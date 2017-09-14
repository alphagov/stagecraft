#!/usr/bin/env bash

set -e

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

# bind services
cf bind-service performance-platform-stagecraft-web gds-performance-platform-pg-service
cf bind-service performance-platform-stagecraft-web redis-poc
cf bind-service performance-platform-stagecraft-celery-worker redis-poc
cf bind-service performance-platform-stagecraft-celery-beat redis-poc
cf bind-service performance-platform-stagecraft-celery-cam redis-poc

# set environmental variables
cf set-env performance-platform-stagecraft-web SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-stagecraft-web FERNET_KEY $APP_FERNET_KEY
cf set-env performance-platform-stagecraft-web ENV_HOSTNAME $PAAS_SPACE.cloudapps.digital
cf set-env performance-platform-stagecraft-web GOVUK_APP_DOMAIN $GOVUK_APP_DOMAIN
cf set-env performance-platform-stagecraft-web GOVUK_WEBSITE_ROOT $GOVUK_WEBSITE_ROOT
cf set-env performance-platform-stagecraft-web REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER

cf set-env performance-platform-stagecraft-celery-worker SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-stagecraft-celery-worker FERNET_KEY $APP_FERNET_KEY
cf set-env performance-platform-stagecraft-celery-worker GOVUK_APP_DOMAIN $GOVUK_APP_DOMAIN
cf set-env performance-platform-stagecraft-celery-worker GOVUK_WEBSITE_ROOT $GOVUK_WEBSITE_ROOT
cf set-env performance-platform-stagecraft-celery-worker REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER

cf set-env performance-platform-stagecraft-celery-beat SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-stagecraft-celery-beat FERNET_KEY $APP_FERNET_KEY
cf set-env performance-platform-stagecraft-celery-beat GOVUK_APP_DOMAIN $GOVUK_APP_DOMAIN
cf set-env performance-platform-stagecraft-celery-beat GOVUK_WEBSITE_ROOT $GOVUK_WEBSITE_ROOT
cf set-env performance-platform-stagecraft-celery-beat REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER

cf set-env performance-platform-stagecraft-celery-cam SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-stagecraft-celery-cam FERNET_KEY $APP_FERNET_KEY
cf set-env performance-platform-stagecraft-celery-cam GOVUK_APP_DOMAIN $GOVUK_APP_DOMAIN
cf set-env performance-platform-stagecraft-celery-cam GOVUK_WEBSITE_ROOT $GOVUK_WEBSITE_ROOT
cf set-env performance-platform-stagecraft-celery-cam REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER

# deploy apps
cf push -f manifest.yml

# create and map routes
cf map-route performance-platform-stagecraft-web cloudapps.digital --hostname stagecraft-$PAAS_SPACE
