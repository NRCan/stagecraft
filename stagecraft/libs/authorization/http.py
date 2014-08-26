import json
import requests

from stagecraft.apps.datasets.models import OAuthUser
from stagecraft.libs.validation.validation import extract_bearer_token
from django.conf import settings
from django.http import (HttpResponseForbidden, HttpResponse)
from statsd.defaults.django import statsd


@statsd.timer('get_user.both')
def _get_user(access_token):
    user = None
    if access_token is not None:

        if settings.USE_DEVELOPMENT_USERS is True:
            try:
                user = settings.DEVELOPMENT_USERS[access_token]
            except KeyError:
                user = None
        else:
            user = _get_user_from_database(access_token)
            if user is None:
                user = _get_user_from_signon(access_token)
                if user is not None:
                    _set_user_to_database(access_token, user)

    return user


@statsd.timer('get_user.signon')
def _get_user_from_signon(access_token):
    response = requests.get(
        '{0}/user.json'.format(settings.SIGNON_URL),
        headers={'Authorization': 'Bearer {0}'.format(access_token)}
    )
    if response.status_code == 200:
        return response.json()['user']


@statsd.timer('get_user.postgres')
def _get_user_from_database(access_token):
    oauth_user = OAuthUser.objects.get_by_access_token(access_token)
    if oauth_user:
        return oauth_user.serialize()


def _set_user_to_database(access_token, user):
    OAuthUser.objects.cache_user(access_token, user)


def check_permission(access_token, permission_requested):
    user = _get_user(access_token)
    has_permission = user is not None and \
        permission_requested in user['permissions']
    return (user, has_permission)


def unauthorized(message):
    response = HttpResponse(to_json({
        'status': 'error',
        'message': 'Unauthorizd: {}'.format(message),
    }), status=401)
    response['WWW-Authenticate'] = 'Bearer'
    return response


def forbidden(message):
    return HttpResponseForbidden(to_json({
        'status': 'error',
        'message': 'Forbidden: {}'.format(message)
    }))


def permission_required(permission):
    def decorator(a_view):
        def _wrapped_view(request, *args, **kwargs):

            access_token = extract_bearer_token(request)
            if access_token is None:
                return unauthorized('no access token given.')

            (user, has_permission) = check_permission(access_token, permission)

            if user is None:
                return unauthorized('invalid access token.')
            elif not has_permission:
                return forbidden('user lacks permission.')
            else:
                return a_view(user, request, *args, **kwargs)
        return _wrapped_view
    return decorator


def to_json(what):
    return json.dumps(what, indent=1)
