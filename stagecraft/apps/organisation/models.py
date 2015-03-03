from django.core.validators import RegexValidator
from django.db import models
from uuidfield import UUIDField


class NodeManager(models.Manager):

    def ancestors_of(self, node, include_self=True):
        if include_self:
            initial_query = 'VALUES (null::uuid, %s::uuid, 0)'
        else:
            initial_query = '''
            SELECT parents.from_node_id::uuid AS node_from,
                   parents.to_node_id::uuid AS node_to,
                   0 AS depth
            FROM organisation_node_parents parents
            WHERE parents.from_node_id=%s::uuid
            '''

        return self.raw('''
        WITH RECURSIVE node_parents(node_from, node_to, depth) AS (
        ''' + initial_query + '''
          UNION ALL
            SELECT parents.from_node_id::uuid AS node_from,
                   parents.to_node_id::uuid AS node_to,
                   (node_parents.depth+1) AS depth
            FROM organisation_node_parents parents, node_parents
            WHERE parents.from_node_id=node_parents.node_to
        )
        SELECT organisation_node.*
        FROM node_parents
          INNER JOIN organisation_node
          ON organisation_node.id = node_parents.node_to
        ORDER BY node_parents.depth DESC
        ''', [node.id])


class NodeType(models.Model):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    name = models.CharField(max_length=256, unique=True)

    def __str__(self):
        return "{}".format(self.name)


class Node(models.Model):
    objects = NodeManager()

    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    name = models.CharField(max_length=256, unique=True)
    abbreviation = models.CharField(
        max_length=50, unique=True,
        null=True, blank=True)
    slug_validator = RegexValidator(
        '^[-a-z0-9]+$',
        message='Slug can only contain lower case letters, numbers or hyphens'
    )
    slug = models.CharField(
        max_length=90,
        validators=[
            slug_validator
        ],
        default=''
    )
    typeOf = models.ForeignKey(NodeType)
    parents = models.ManyToManyField('self', symmetrical=False)

    def __str__(self):
        return "{}".format(self.name)

    def get_ancestors(self, include_self=True):
        return Node.objects.ancestors_of(self, include_self)

    def spotlightify(self):
        node = {}
        if self.abbreviation is not None:
            node['abbr'] = self.abbreviation
        else:
            node['abbr'] = self.name
        node['title'] = self.name
        return node
