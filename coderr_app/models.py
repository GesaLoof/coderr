from django.db import models
from auth_app.models import Profile

class CoderrProfile(models.Model):
    """Extended profile data, filled in after registration."""
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='coderr_profile')
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    location = models.CharField(max_length=100, default="")
    tel = models.CharField(max_length=100, default="")
    description = models.TextField(default="")
    working_hours = models.CharField(max_length=100, default="")

    def __str__(self):
        return self.profile.user.username