from optparse import make_option
# from __future__ import unicode_literals
from django.core.management.base import BaseCommand, CommandError

# from stagecraft.apps.datasets.models import DataSet


class Command(BaseCommand):
    """docstring for Command"""
    option_list = BaseCommand.option_list + (
        make_option(
            '-i',
            '--input-data-set',
            dest='input-data-set',
            help=("The data-set from which data will be pulled")
        ),
        make_option(
            '-o',
            '--output-data-set',
            dest='output-data-set',
            help=("The data-set that data will be copied into")
        ),
        make_option(
            '--mappings-file',
            dest='mappings-file',
            help=("The key:key and property:property mappings json file")
        ),
    )
    args = ''
    help = ("")
    args = ''

    # def handle(self, *args, **options):
    #     pass

    def map_one_to_one_fields(mapping, pairs):
        """
        >>> mapping = {'a': 'b'}
        >>> pairs = {'a': 1}
        >>> map_one_to_one_fields(mapping, pairs)
        {'b': 1}
        >>> mapping = {'a': ['b', 'a']}
        >>> map_one_to_one_fields(mapping, pairs)
        {'a': 1, 'b': 1}
        """
        mapped_pairs = dict()
        for key, value in pairs.items():
            if key in mapping:
                targets = mapping[key]
                if not isinstance(targets, list):
                    targets = list(targets)
                for target in targets:
                    mapped_pairs[target] = value
            else:
                mapped_pairs[key] = value

        return mapped_pairs

    def apply_mapping(mapping, pairs):
        logging.warn("{} -- {}".format(mapping, pairs))
        return dict(map_one_to_one_fields(mapping, pairs).items())
