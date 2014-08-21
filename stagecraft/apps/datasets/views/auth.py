from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..models.oauth_user import OAuthUser
from .common.utils import permission_required


@csrf_exempt
@require_POST
@permission_required('user_update_permission')
@never_cache
def reauth(user, request, uid):
    OAuthUser.objects.purge_user(uid)
    return HttpResponse('ok')
