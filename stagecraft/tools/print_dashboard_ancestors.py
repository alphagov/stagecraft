import sys

import django
django.setup()

from stagecraft.apps.dashboards.models import Dashboard


def print_ancestors(slug):
    try:
        dashboard = Dashboard.objects.get(slug=slug)
    except Dashboard.DoesNotExist:
        print('Dashboard not found')
        return None
    ancestor_slugs = map(lambda x: x.slug,
                         dashboard.organisation.get_ancestors())
    print('%s' % ' -> '.join(map(str, ancestor_slugs + [slug])))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Please supply an dashboard slug')
        sys.exit(1)
    print_ancestors(sys.argv[1])
