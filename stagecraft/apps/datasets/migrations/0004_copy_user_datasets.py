# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def copy_user_datasets(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User.objects.all():
        for ds in user.data_sets.all():
            ds.owners.add(user)

class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0003_dataset_owners'),
    ]

    operations = [
        migrations.RunPython(copy_user_datasets),
    ]
