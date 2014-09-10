from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from uuidfield import UUIDField


class NodeType(models.Model):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    name = models.CharField(max_length=256, unique=True)

    def serialize(self):
        return {
            'id': str(self.id),
            'name': self.name
        }


class Node(MPTTModel):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    name = models.CharField(max_length=256, unique=True)
    abbreviation = models.CharField(max_length=50, unique=True, null=True)
    typeOf = models.ForeignKey(NodeType)
    parent = TreeForeignKey(
        'self', null=True,
        blank=True, related_name='children'
    )

    def serialize(self, resolve_parent=True):
        node = {
            'id': str(self.id),
            'type': self.typeOf.serialize(),
            'name': self.name,
        }

        if self.abbreviation is not None:
            node['abbreviation'] = self.abbreviation
        else:
            node['abbreviation'] = ''

        if resolve_parent:
            if self.parent is not None:
                node['parent'] = self.parent.serialize(resolve_parent=False)
            else:
                node['parent'] = None

        return node

    def spotlightify(self):
        node = {}
        if self.abbreviation is not None:
            node['abbr'] = self.abbreviation
        else:
            node['abbr'] = ''
        node['title'] = self.name
        return node
