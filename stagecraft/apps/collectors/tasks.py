from argparse import Namespace
from celery import shared_task
from celery.utils.log import get_task_logger
from performanceplatform.collector.main import _run_collector
from django.conf import settings
from stagecraft.apps.collectors.models import Collector

logger = get_task_logger(__name__)


@shared_task
def log(message):
    logger.info(message)


@shared_task
def run_collector(collector_slug, start=None, end=None):
    def get_config(collector_slug, start_at, end_at):
        collector = Collector.objects.get(slug=collector_slug)
        config = Namespace(
            performanceplatform={
                "backdrop_url": settings.BACKDROP_WRITE_URL + '/data'
            },
            credentials=collector.data_source.credentials,
            query={
                "data-set": {
                    "data-group": collector.data_set.data_group,
                    "data-type": collector.data_set.data_type
                },
                "query": collector.query,
                "options": collector.options
            },
            token={
                "token": collector.type.provider.slug
            },
            dry_run=False,
            start_at=start_at,
            end_at=end_at
        )
        return collector.type.entry_point, config

    entry_point, args = get_config(collector_slug, start, end)
    _run_collector(entry_point, args)
