from stagecraft.apps.dashboards.lib.spotlight_config_migration import (
    spotlight_json, Dashboard
)
import os
import logging
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

# for filename, json in spotlight_json(os.path.join(os.path.dirname(__file__)
# , 'test_import')):
    for filename, json in spotlight_json(
        os.path.join(os.path.dirname(__file__),
                     '../spotlight/app/support/stagecraft_stub/responses')):
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
        else:
            dashboard.set_data(**json)
            dashboard.send()

    print 'All migrated'
