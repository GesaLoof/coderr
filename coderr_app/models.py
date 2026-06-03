from django.db import models
from auth_app.models import Profile
from django.utils import timezone


class CoderrProfile(models.Model):
    """Extended profile data, filled in after registration."""

    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="coderr_profile"
    )
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    file = models.FileField(upload_to="uploads/", null=True, blank=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=100, default="")
    tel = models.CharField(max_length=100, default="")
    description = models.TextField(default="")
    working_hours = models.CharField(max_length=100, default="")

    def __str__(self):
        return self.profile.user.username

    def save(self, *args, **kwargs):
        """Update uploaded_at when the avatar file changes."""
        if self.file:
            try:
                old = CoderrProfile.objects.get(pk=self.pk)
                if old.file != self.file:
                    # file has changed → update uploaded_at
                    self.uploaded_at = timezone.now()
            except CoderrProfile.DoesNotExist:
                pass  # no file on creation, nothing to do
        super().save(*args, **kwargs)


class Offer(models.Model):
    """Offers created by business profiles."""

    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="offers"
    )
    title = models.CharField(max_length=200)
    image = models.FileField(upload_to="offer_images/", null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.profile.user.username}"


class OfferDetail(models.Model):
    """Details for an offer, such as a specific service or price."""

    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="details"
    )  # ← add this
    title = models.CharField(max_length=100)
    revisions = models.IntegerField(default=0)
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Order(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    offer_detail = models.ForeignKey(OfferDetail, on_delete=models.PROTECT)

    customer_user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="orders"
    )

    business_user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="received_orders"
    )

    title = models.CharField(max_length=100)
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=100)
    STATUS_CHOICES = [
              ("in_progress", "In Progress"),
              ("completed", "Completed"),
              ("cancelled", "Cancelled"),
          ]
    status = models.CharField(
            max_length=20, choices=STATUS_CHOICES, default="in_progress"
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order of {self.offer.title} by {self.customer_user.user.username}"


class Review(models.Model):
    business_user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="received_reviews"
    )
    reviewer = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="reviews"
    )
    description = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reviewer", "business_user"], name="unique_review_per_business"
            )
        ]

    def __str__(self):
        return f"Review for {self.business_user.user.username} by {self.reviewer.user.username}"

