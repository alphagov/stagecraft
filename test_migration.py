from stagecraft.apps.dashboards.lib.spotlight_config_migration import (
    spotlight_json, Dashboard
)
import os
import logging

logging.basicConfig(level=logging.DEBUG)

for json in spotlight_json(os.path.join(os.path.dirname(__file__), 'test_import')):
    dashboard = Dashboard('http://stagecraft.development.performance.service.gov.uk')
    dashboard.set_data(**json)
    dashboard.send()
