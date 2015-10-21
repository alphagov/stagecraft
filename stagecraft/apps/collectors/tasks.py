from __future__ import absolute_import
from argparse import Namespace
from celery import shared_task, group
from celery.utils.log import get_task_logger
from performanceplatform.collector.main import _run_collector
from django.conf import settings
from stagecraft.apps.collectors.libs.ga import CredentialStorage
from stagecraft.apps.collectors.models import Collector, CollectorType
import json

logger = get_task_logger(__name__)


@shared_task
def log(message):
    logger.info(message)


@shared_task
def run_collectors_by_type(*args):
    for slug in args:
        collector_type = CollectorType.objects\
            .prefetch_related('collectors').get(slug=slug)
        slugs = [c.slug for c in collector_type.collectors.all()]
        group(run_collector.s(slug) for slug in slugs)()


@shared_task
def run_collector(collector_slug, start_at=None, end_at=None, dry_run=False):
    def get_config(collector_slug, start, end):
        collector = Collector.objects.get(slug=collector_slug)

        credentials = json.loads(collector.data_source.credentials)
        if ("CLIENT_SECRETS" in credentials and
                "OAUTH2_CREDENTIALS" in credentials):
            data_source = collector.data_source
            storage_object = CredentialStorage(data_source)
            credentials['OAUTH2_CREDENTIALS'] = storage_object

        config = Namespace(
            performanceplatform={
                "backdrop_url": settings.BACKDROP_WRITE_URL + '/data'
            },
            credentials=credentials,
            query={
                "data-set": {
                    "data-group": str(collector.data_set.data_group),
                    "data-type": str(collector.data_set.data_type)
                },
                "query": collector.query,
                "options": collector.options
            },
            token={
                "token": collector.data_set.bearer_token
            },
            dry_run=dry_run,
            start_at=start,
            end_at=end
        )
        return collector.type.entry_point, config

    entry_point, args = get_config(collector_slug, start_at, end_at)
    if settings.DISABLE_COLLECTORS:
        return 'Collectors Disabled'
    else:
        _run_collector(entry_point, args)
