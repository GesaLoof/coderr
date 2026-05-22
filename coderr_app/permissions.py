from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import CoderrProfile

class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of a profile to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the profile.
        return obj == request.user.profile