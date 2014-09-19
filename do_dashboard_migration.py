from stagecraft.apps.dashboards.lib.spotlight_config_migration import (
    spotlight_json, Dashboard
)
import os
import logging
import sys
import argparse
from django.conf import settings

SPOTLIGHT_CONFIG_JSON_DEFAULT = (
    '../spotlight/app/support/stagecraft_stub/responses'
)

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--path",
        help="Path to spotlight json files. Defaults to {}".format(
            SPOTLIGHT_CONFIG_JSON_DEFAULT))
    parser.add_argument("-t", "--token", help="Auth token for stagecraft")
    args = parser.parse_args()
    if args.path:
        path = args.path
    else:
        path = os.path.join(os.path.dirname(__file__),
                            SPOTLIGHT_CONFIG_JSON_DEFAULT)
    for filename, json in spotlight_json(path):
        logger.debug('Creating dashboard for {}'.format(filename))
        dashboard = Dashboard(
            'http://stagecraft{}'.format(settings.ENV_HOSTNAME),
            args.token
        )
        if not isinstance(json, dict):
            logger.warning(
                'skipping dashboard {} as it is not a valid dictionary'.format(
                    filename))
        elif json.get('published', None) is None:
            logger.warning(
                'skipping dashboard {} as it does not have a published '
                'attribute'.format(filename))
        elif filename == 'housing.json':
            logger.warning(
                'skipping housing dashboard as it references unknown datasets')
        elif 'department' not in json and 'agency' in json:
            logger.warning(
                'skipping dashboard {} that only specifies agency and not'
                'department'.format(dashboard))
        else:
            dashboard.set_data(**json)
            dashboard.send()

    print('All migrated')
