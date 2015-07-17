import factory

from stagecraft.apps.users.models import User


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User

    email = factory.Sequence(lambda n: 'user-{}@gov.uk'.format(n))
