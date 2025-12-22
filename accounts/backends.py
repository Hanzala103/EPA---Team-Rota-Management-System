from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import CustomUser


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticate against CustomUser using either email (USERNAME_FIELD) or username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or kwargs.get("email") or kwargs.get("identifier") or "").strip()
        if not identifier or not password:
            return None

        user = (
            CustomUser.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier))
            .select_related("role_profile")
            .first()
        )
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
