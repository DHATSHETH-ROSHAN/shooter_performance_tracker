from django.contrib.auth.backends import ModelBackend
from .models import UserProfiles

class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserProfiles.objects.get(email=username)
            if user.check_password(password):
                return user
        except UserProfiles.DoesNotExist:
            return None