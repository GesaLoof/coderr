from rest_framework import permissions, viewsets
from .serializers import (
    ProfileDetailSerializer,
    ProfileUpdateSerializer,
    ProfileListSerializerBusiness,
    ProfileListSerializerCustomer,
    OfferSerializer,
    OfferDetailSerializer,
    OfferCreateSerializer,
    OfferByIdSerializer,
    OrderSerializer,
    OrderCreateSerializer,
    ReviewSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer,
)
from coderr_app.models import Offer, OfferDetail, Order, Review
from auth_app.models import Profile
from rest_framework import generics
from rest_framework.exceptions import NotFound
from coderr_app.permissions import (
    IsOwnerOrReadOnly,
    IsBusinessOwner,
    IsCustomer,
    IsStaffUser,
    IsReviewOwner,
)
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.db import models


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Get or patch a single profile by pk."""

    http_method_names = ["get", "patch", "head", "options"]

    def get_permissions(self):
        """Owner-only on PATCH, authenticated for GET."""
        if self.request.method == "PATCH":
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """Use update serializer on PATCH, detail serializer on GET."""
        if self.request.method == "PATCH":
            return ProfileUpdateSerializer
        return ProfileDetailSerializer

    def get_object(self):
        """Fetch Profile by pk or raise 404."""
        try:
            obj = Profile.objects.get(pk=self.kwargs["pk"])
        except Profile.DoesNotExist:
            raise NotFound("No profile matches the given query.")
        self.check_object_permissions(self.request, obj)
        return obj

    def partial_update(self, request, *args, **kwargs):
        """Save via update serializer, return full detail response."""
        instance = self.get_object()
        serializer = ProfileUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        # use ProfileDetailSerializer for the response
        response_serializer = ProfileDetailSerializer(updated_instance)
        return Response(response_serializer.data)


class BusinessProfileListView(generics.ListAPIView):
    """List all profiles with type 'business'."""

    serializer_class = ProfileListSerializerBusiness
    permission_classes = [permissions.IsAuthenticated]
    queryset = Profile.objects.filter(type="business")
    pagination_class = None

class CustomerProfileListView(generics.ListAPIView):
    """List all profiles with type 'customer'."""

    serializer_class = ProfileListSerializerCustomer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Profile.objects.filter(type="customer")
    pagination_class = None


class LargeResultsPagination(PageNumberPagination):
    """Paginate listings with a large default page size."""

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class OfferViewSet(viewsets.ModelViewSet):
    """ViewSet for managing offers."""

    pagination_class = LargeResultsPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsBusinessOwner()]
        if self.request.method == "PATCH" or self.request.method == "DELETE":
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if (
            self.action == "create"
            or self.action == "update"
            or self.action == "partial_update"
        ):
            return OfferCreateSerializer
        if self.action == "retrieve":
            return OfferByIdSerializer
        return OfferSerializer

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)

    def get_queryset(self):
        queryset = Offer.objects.all()

        offer_type = self.request.query_params.get("offer_type")
        creator_id = self.request.query_params.get("creator_id")
        min_price = self.request.query_params.get("min_price")
        max_delivery_time = self.request.query_params.get("max_delivery_time")
        ordering = self.request.query_params.get("ordering")
        search = self.request.query_params.get("search")  # in title or description

        if offer_type:
            queryset = queryset.filter(details__offer_type=offer_type)
        if creator_id:
            queryset = queryset.filter(profile__id=creator_id)
        if min_price:
            queryset = queryset.filter(details__price__gte=min_price)
        if max_delivery_time:
            queryset = queryset.filter(
                details__delivery_time_in_days__lte=max_delivery_time
            )
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        allowed_ordering = ["min_price", "-min_price", "updated_at", "-updated_at"]
        if ordering in allowed_ordering:
            if ordering == "min_price":
                queryset = queryset.order_by("details__price")
            elif ordering == "-min_price":
                queryset = queryset.order_by("-details__price")
            else:
                queryset = queryset.order_by(ordering)
        return queryset.distinct()


class OfferDetailView(generics.RetrieveAPIView):
    """Get a single offer detail by pk."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing orders."""

    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomer()]
        if self.request.method == "PATCH":
            return [permissions.IsAuthenticated(), IsBusinessOwner()]
        if self.request.method == "DELETE":
            return [IsStaffUser()]
        return [permissions.IsAuthenticated()]


class OrderCountView(generics.RetrieveAPIView):
    """Get the count of orders in progress for a specific business profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile_id = self.kwargs["pk"]
        try:
            profile = Profile.objects.get(pk=profile_id)
        except Profile.DoesNotExist:
            raise NotFound("No profile matches the given query.")

        if profile.type != "business":
            raise NotFound("Profile is not a business profile.")

        order_count = Order.objects.filter(
            business_user=profile, status="in_progress"
        ).count()
        return Response({"order_count": order_count})


class CompletedOrderCountView(generics.RetrieveAPIView):
    """Get the count of completed orders for a specific business profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile_id = self.kwargs["pk"]
        try:
            profile = Profile.objects.get(pk=profile_id)
        except Profile.DoesNotExist:
            raise NotFound("No profile matches the given query.")

        if profile.type != "business":
            raise NotFound("Profile is not a business profile.")

        order_count = Order.objects.filter(
            business_user=profile, status="completed"
        ).count()
        return Response({"order_count": order_count})


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reviews."""

    queryset = Review.objects.all()
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()

        business_user_id = self.request.query_params.get("business_user_id")
        reviewer_id = self.request.query_params.get("reviewer_id")
        ordering = self.request.query_params.get("ordering")

        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)

        allowed_ordering = ["-updated_at", "updated_at", "-rating", "rating"]
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewCreateSerializer

        if self.action in ["update", "partial_update"]:
            return ReviewUpdateSerializer

        return ReviewSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsCustomer()]
        if self.action == "retrieve" or self.action == "list":
            return [permissions.IsAuthenticated()]

        if self.action in ["partial_update", "update", "destroy"]:
            return [permissions.IsAuthenticated(), IsReviewOwner()]

        return [permissions.AllowAny()]

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)

        instance = self.get_object()
        response.data = ReviewSerializer(instance).data

        return response


class BaseInfoView(generics.RetrieveAPIView):
    """Get basic info about the API, such as total counts of profiles, offers, orders, and reviews."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        business_profile_count = Profile.objects.filter(type="business").count()
        offer_count = Offer.objects.count()
        review_count = Review.objects.count()
        average_rating = (
            Review.objects.aggregate(average_rating=models.Avg("rating"))[
                "average_rating"
            ]
            or 0
        )

        return Response(
            {
                "review_count": review_count,
                "average_rating": average_rating,
                "business_profile_count": business_profile_count,
                "offer_count": offer_count,
            }
        )
