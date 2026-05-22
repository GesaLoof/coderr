from rest_framework import serializers
from coderr_app.models import CoderrProfile
from auth_app.models import Profile
from django.contrib.auth.models import User
from rest_framework import generics

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
        # instance IS the Profile, so access user directly
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
