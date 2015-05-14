from __future__ import unicode_literals

import json
import reversion

from django.core.management.base import BaseCommand, CommandError

from stagecraft.apps.users.models import User
from stagecraft.apps.datasets.models import DataSet


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
        if User.objects.filter(email=email).exists():
            self.stdout.write("SKIPPING {} - already exists".format(email))
            return

        with reversion.create_revision():
            user = User.objects.create(
                email=email,
            )
            for data_set in data_sets:
                user.dataset_set.add(data_set)
                self.stdout.write(
                    "Added access to {0} for user {1}".format(data_set, email)
                )

            self.stdout.write("Created {}".format(email))

    def get_data_sets_by_names(self, data_set_names):
        found_data_sets = []
        for name in data_set_names:
            data_set = DataSet.objects.filter(name=name).first()
            if data_set:
                found_data_sets.append(data_set)
            else:
                self.stdout.write(
                    "Couldn't find data-set with the name {}".format(name)
                )
        return found_data_sets
