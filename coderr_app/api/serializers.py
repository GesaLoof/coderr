from rest_framework import serializers
from coderr_app.models import CoderrProfile, Offer, OfferDetail, Order, Review
from auth_app.models import Profile
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied


class CoderrProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoderrProfile
        fields = ['first_name', 'last_name', 'file', 'location', 'tel', 'description', 'working_hours']


class ProfileDetailSerializer(serializers.ModelSerializer):
    # fields from User
    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    # fields from CoderrProfile (default to " " if no CoderrProfile exists yet)
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    tel = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    working_hours = serializers.SerializerMethodField()
    uploaded_at = serializers.SerializerMethodField()


    class Meta:
        model = Profile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours',
            'type', 'email', 'created_at'
        ]

    def _get_coderr_field(self, obj, field, default=" "):
        """Helper to safely get a field from the related CoderrProfile."""
        try:
            return getattr(obj.coderr_profile, field) or default
        except CoderrProfile.DoesNotExist:
            return default

    def get_first_name(self, obj):
        return self._get_coderr_field(obj, 'first_name')

    def get_last_name(self, obj):
        return self._get_coderr_field(obj, 'last_name')

    def get_file(self, obj):
        return self._get_coderr_field(obj, 'file', default=None)

    def get_location(self, obj):
        return self._get_coderr_field(obj, 'location')

    def get_tel(self, obj):
        return self._get_coderr_field(obj, 'tel')

    def get_description(self, obj):
        return self._get_coderr_field(obj, 'description')

    def get_working_hours(self, obj):
        return self._get_coderr_field(obj, 'working_hours')
    
    def get_uploaded_at(self, obj):
        return self._get_coderr_field(obj, 'uploaded_at', default=None)


class ProfileListSerializerBusiness(ProfileDetailSerializer):
    """Serializer for listing business profiles — excludes email and created_at."""

    class Meta(ProfileDetailSerializer.Meta):
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours', 'type',
        ]

class ProfileListSerializerCustomer(ProfileDetailSerializer):
    """Serializer for listing customer profiles — excludes email and created_at."""

    class Meta(ProfileDetailSerializer.Meta):
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file', 'uploaded_at', 'type',
        ]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    # fields from User
    email = serializers.EmailField(source='user.email', required=False)
    # fields from Profile
    type = serializers.CharField(source='profile.type', required=False)
    # fields from CoderrProfile directly
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    tel = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    working_hours = serializers.CharField(required=False)

    class Meta:
        model = CoderrProfile
        fields = ['first_name', 'last_name', 'location', 'tel', 
                  'description', 'working_hours', 'email', 'type']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            instance.user.email = user_data.get('email', instance.user.email)
            instance.user.save()

        # update Profile fields directly on instance
        profile_data = validated_data.pop('profile', {})
        if profile_data:
            instance.type = profile_data.get('type', instance.type)
            instance.save()

        # get or create the related CoderrProfile and update it
        coderr_profile, created = CoderrProfile.objects.get_or_create(profile=instance)
        for attr, value in validated_data.items():
            setattr(coderr_profile, attr, value)
        coderr_profile.save()

        return instance


class OfferDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = OfferDetail
        fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features', 'offer_type']


class StrictModelSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        unknown_fields = set(data.keys()) - set(self.fields.keys())

        if unknown_fields:
            raise serializers.ValidationError(
                {
                    field: ["Unknown field."]
                    for field in unknown_fields
                }
            )

        return super().to_internal_value(data)


class OfferCreateSerializer(StrictModelSerializer):
    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        for detail in details_data:
            OfferDetail.objects.create(offer=offer, **detail)
        return offer
        
    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', [])
        
        # update Offer fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # delete old details and recreate them
        instance.details.all().delete()
        for detail in details_data:
            OfferDetail.objects.create(offer=instance, **detail)
        
        return instance
    

class OfferDetailMinimalSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferSerializer(serializers.ModelSerializer):
    details = OfferDetailMinimalSerializer(many=True, read_only=True)
    user = serializers.IntegerField(source='profile.user.id', read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description',
            'created_at', 'updated_at', 'details',
            'min_price', 'min_delivery_time', 'user_details'
        ]

    def get_min_price(self, obj):
        prices = obj.details.values_list('price', flat=True)
        return min(prices) if prices else None

    def get_min_delivery_time(self, obj):
        times = obj.details.values_list('delivery_time_in_days', flat=True)
        return min(times) if times else None

    def get_user_details(self, obj):
        user = obj.profile.user
        return {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
        }
    
class OfferByIdSerializer(serializers.ModelSerializer):
    details = OfferDetailMinimalSerializer(many=True, read_only=True)
    user = serializers.IntegerField(source='profile.user.id', read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description',
            'created_at', 'updated_at', 'details',
            'min_price', 'min_delivery_time'
        ]

    def get_min_price(self, obj):
        prices = obj.details.values_list('price', flat=True)
        return min(prices) if prices else None

    def get_min_delivery_time(self, obj):
        times = obj.details.values_list('delivery_time_in_days', flat=True)
        return min(times) if times else None
    


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    offer_detail_id = serializers.PrimaryKeyRelatedField(
        queryset=OfferDetail.objects.select_related('offer__profile'),
        source='offer_detail',
        write_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id',
            'offer_detail_id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'customer_user',
            'business_user',
            'title',
            'revisions',
            'delivery_time_in_days',
            'price',
            'features',
            'offer_type',
            'status',
            'created_at',
            'updated_at',
        ]

    def create(self, validated_data):
        offer_detail = validated_data.pop('offer_detail')
        customer = self.context['request'].user.profile

        return Order.objects.create(
            offer=offer_detail.offer,
            offer_detail=offer_detail,

            customer_user=customer,
            business_user=offer_detail.offer.profile,

            title=offer_detail.title,
            revisions=offer_detail.revisions,
            delivery_time_in_days=offer_detail.delivery_time_in_days,
            price=offer_detail.price,
            features=offer_detail.features,
            offer_type=offer_detail.offer_type,

            status='in_progress',
        )
    
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description','created_at', 'updated_at']    


class ReviewCreateSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description','created_at', 'updated_at']

    def validate_business_user(self, business_user):
        reviewer = self.context['request'].user.profile

        has_ordered = Order.objects.filter(
            customer_user=reviewer,
            business_user=business_user
        ).exists()

        if not has_ordered:
            raise serializers.ValidationError(
                "You can only review businesses you have ordered from."
            )

        if Review.objects.filter(
            reviewer=reviewer,
            business_user=business_user
        ).exists():
            raise PermissionDenied(
                "You have already reviewed this business."
            )

        return business_user

    def create(self, validated_data):
        return Review.objects.create(
            reviewer=self.context['request'].user.profile,
            **validated_data
        )
    

class ReviewUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ['rating', 'description']

    def validate(self, attrs):
        allowed_fields = {'rating', 'description'}

        received_fields = set(self.initial_data.keys())
        unknown_fields = received_fields - allowed_fields

        if unknown_fields:
            raise serializers.ValidationError(
                {
                    field: "This field is not allowed."
                    for field in unknown_fields
                }
            )

        return attrs