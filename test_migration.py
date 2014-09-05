from stagecraft.apps.dashboards.lib.spotlight_config_migration import (
    spotlight_json, Dashboard
)
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# for json in spotlight_json(os.path.join(os.path.dirname(__file__), 'test_import')):
for filename, json in spotlight_json(os.path.join(os.path.dirname(__file__), '../spotlight/app/support/stagecraft_stub/responses')):
    logger.debug('Creating dashboard for {}'.format(filename))
    dashboard = Dashboard(
        'http://stagecraft.development.performance.service.gov.uk')
    if isinstance(json, dict) and json.get('published', None):
        dashboard.set_data(**json)
        dashboard.send()
    else:
        logger.warning(
            'skipping dashboard {} as it is not a valid dictionary'.format(
                filename))
