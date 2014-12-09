from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from uuidfield import UUIDField


class NodeType(models.Model):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    name = models.CharField(max_length=256, unique=True)


class Node(MPTTModel):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    name = models.CharField(max_length=256, unique=True)
    abbreviation = models.CharField(
        max_length=50, unique=True,
        null=True, blank=True)
    typeOf = models.ForeignKey(NodeType)
    parent = TreeForeignKey(
        'self', null=True,
        blank=True, related_name='children'
    )

    def spotlightify(self):
        node = {}
        if self.abbreviation is not None:
            node['abbr'] = self.abbreviation
        else:
            node['abbr'] = self.name
        node['title'] = self.name
        return node
