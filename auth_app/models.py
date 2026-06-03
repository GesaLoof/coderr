from django.db import models

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """Extend the built-in User with user type."""

    TYPE_CHOICES = [
        ("customer", "Customer"),
        ("business", "Business"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="customer")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the profile's username."""
        return self.user.username
