# encoding: utf-8

from __future__ import unicode_literals

from django.core.validators import RegexValidator

data_set_name_validator = RegexValidator(
    '^[a-z0-9_]+$',
    'Only lowercase alphanumeric characters and underscores are allowed.')

data_group_name_validator = RegexValidator(
    '^[a-z0-9\-]+$',
    'Only lowercase alphanumeric characters and hyphens are allowed.')

data_type_name_validator = data_group_name_validator
