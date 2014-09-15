from stagecraft.apps.dashboards.lib.spotlight_config_migration import (
    spotlight_json, Dashboard
)
import os
import logging
import sys
if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        print('Please specify a path containing the spotlight json files')
        path = os.path.join(
            os.path.dirname(__file__),
            '../spotlight/app/support/stagecraft_stub/responses')
    for filename, json in spotlight_json(path):
        logger.debug('Creating dashboard for {}'.format(filename))
        dashboard = Dashboard(
            'http://stagecraft.development.performance.service.gov.uk')
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
