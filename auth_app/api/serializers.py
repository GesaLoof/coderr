from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from auth_app.models import Profile
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    """Serialize user registration, creating User, Profile, and Token."""

    username = serializers.CharField(required=True, allow_blank=False)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = Profile
        fields = ["id", "username", "email", "password", "repeated_password", "type"]

    def validate(self, data):
        """Ensure passwords match and email is not already in use."""
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        return data

    def create(self, validated_data):
        """Create a User, Profile, and Token, then return the User."""
        validated_data.pop("repeated_password")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

        Profile.objects.create(user=user)
        Token.objects.create(user=user)

        return user
