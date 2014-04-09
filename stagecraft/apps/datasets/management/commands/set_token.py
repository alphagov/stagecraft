from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from stagecraft.libs.mass_update import DataSetMassUpdate


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--data-type-name',
            dest='data_type',
            help=("Specify the data type name to "
                  "match against when updating datasets")),
        make_option(
            '--data-group-name',
            dest='data_group',
            help=("Specify the data group name to "
                  "match against when updating datasets")))
    args = '<bearer_token>'
    help = ("Updates the DataSets matched by the DataType "
            "name (data-type-name), DataGroup name "
            "(date-group-name) or combination thereof with the "
            "specified bearer_token")

    def handle(self, *args, **options):
        self.stdout.write(str(args))
        self.stdout.write(str(options))
