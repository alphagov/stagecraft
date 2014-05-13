from __future__ import unicode_literals

import json
import reversion

from django.core.management.base import BaseCommand, CommandError

from stagecraft.apps.datasets.models import BackdropUser


class Command(BaseCommand):
    option_list = BaseCommand.option_list
    args = '<backdrop_users.json>'
    help = ("Imports a backdrop JSON dump of the ``users`` collection.")

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError(
                "No backdrop_users.json file specified, see --help")

        for filename in args:
            self.stdout.write("Opening {}".format(filename))
            self.load_users_from_backdrop_users_json_file(filename)
            self.stdout.write('Finished')

    def load_users_from_backdrop_users_json_file(self, filename):
        with open(filename, 'r') as f:
            users = json.loads(f.read())
            for user in users:
                self.save_backdrop_user(user)

    def save_backdrop_user(self, user):
        email = user['email']
        data_sets = self.get_data_sets_by_names(user['data_sets'])
        if BackdropUser.objects.filter(email=email).exists():
            self.stdout.write("SKIPPING {} - already exists".format(email))
            return

        with reversion.create_revision():
            BackdropUser.objects.create(
                email=email,
                data_sets=data_sets
            )

            self.stdout.write("Created {}".format(email))

    def get_data_sets_by_names(self, data_set_names):
        return []
