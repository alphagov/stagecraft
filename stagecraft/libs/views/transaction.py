from functools import wraps
from django.db import transaction


class NonOverlappingError(Exception):
    pass


def atomic_view(a_view):
    """Atomic transaction decorator for views

    If the response status is in the error range then roll back the transaction
    """
    @wraps(a_view)
    def _wrapped_view(*args, **kwargs):
        try:
            with transaction.atomic():
                response = a_view(*args, **kwargs)
                if response.status_code >= 400:
                    raise NonOverlappingError()
        except NonOverlappingError:
            pass
        return response

    return _wrapped_view
