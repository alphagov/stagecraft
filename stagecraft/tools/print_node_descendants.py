import sys

import django
django.setup()

from stagecraft.apps.organisation.models import Node
from stagecraft.apps.dashboards.models import Dashboard


def print_paths(slug):
    try:
        node = Node.objects.get(slug=slug)
    except Node.DoesNotExist:
        print('Node not found')
        return None
    dfs(node)


def dfs(node, path=None):
    if path is None:
        path = []
    path.append(node.slug)

    descendants = list(node.get_immediate_descendants())
    if descendants:
        for descendant in descendants:
            dfs(descendant, path[:])
    else:
        dashboards = Dashboard.objects.filter(
            _organisation=Node.objects.get(slug=path[-1]))
        if dashboards:
            for dashboard in dashboards:
                print('%s' % ' -> '.join(map(str, path + [dashboard.slug])))
        else:
            print('%s' % ' -> '.join(map(str, path)))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Please supply an organisation slug')
        sys.exit(1)
    print_paths(sys.argv[1])
