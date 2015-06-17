from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..models.oauth_user import OAuthUser
from stagecraft.libs.authorization.http import permission_required


@csrf_exempt
@require_http_methods(['POST', 'PUT'])
@permission_required(['user_update_permission'])
@never_cache
def invalidate(user, request, uid):
    OAuthUser.objects.purge_user(uid)
    return HttpResponse(status=204)
