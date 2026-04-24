import hashlib

from django.contrib.auth.models import AbstractUser
from django.utils.http import urlencode

from judge.models import Profile
from judge.utils.unicode import utf8bytes
from . import registry


@registry.function
def gravatar(email, size=80, default=None):
    if isinstance(email, Profile):
        if default is None:
            default = email.mute
        email = email.user.email
    elif isinstance(email, AbstractUser):
        email = email.email
    elif hasattr(email, 'user') and isinstance(email.user, AbstractUser):
        # e.g. ContestRankingProfile namedtuple where .user is a Django User
        email = email.user.email

    gravatar_url = 'https://www.gravatar.com/avatar/' + hashlib.md5(utf8bytes(email.strip().lower())).hexdigest() + '?'
    args = {'d': 'identicon', 's': str(size)}
    if default:
        args['f'] = 'y'
    gravatar_url += urlencode(args)
    return gravatar_url
