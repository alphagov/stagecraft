from __future__ import unicode_literals

import json
import reversion

from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from stagecraft.apps.datasets.models import BackdropUser
from stagecraft.libs.backdrop_client import backdrop_connection_disabled


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--without-backdrop',
            action='store_true',
            dest='without_backdrop',
            default=False,
            help="Move user management out of backdrop"),)

    args = '<backdrop_users.json>'
    help = ("Imports a backdrop JSON dump of the ``users`` collection.")

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError(
                "No data_sets.json file specified, see --help")

        for filename in args:
            self.stdout.write("Opening {}".format(filename))

            if options['without_backdrop']:
                self.stdout.write("Disabling Backdrop")
                with backdrop_connection_disabled():
                    self.load_data_sets_from_data_sets_json(filename)
            else:
                self.stdout.write("Not disabling Backdrop")
                self.load_data_sets_from_data_sets_json(filename)

            self.stdout.write('Finished')

    def load_users_from_backdrop_users_json_file(self, filename):
        with open(filename, 'r') as f:
            users = json.loads(f.read())
            for user in users:
                self.save_backdrop_user(user)

    def save_backdrop_user(self, user):
        email = user['email']
        if BackdropUser.objects.filter(email=email).exists():
            self.stdout.write("SKIPPING {} - already exists".format(email))
            return

        with reversion.create_revision():
            BackdropUser.objects.create(
                email=email,
                data_sets=user['data_sets']
            )

            self.stdout.write("Created {}".format(email))
