from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from auth_app.models import Profile
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    """Serialize user registration, creating User, Profile, and Token."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = Profile
        fields = ["id", "fullname", "email", "password", "repeated_password"]

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
        fullname = validated_data.pop("fullname")

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

        Profile.objects.create(user=user, fullname=fullname)
        Token.objects.create(user=user)

        return user


class CustomLoginSerializer(serializers.Serializer):
    """Authenticate a user by email and password, returning the User object."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Look up user by email, authenticate password, and attach user to data."""
        email = data.get("email")
        password = data.get("password")

        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data["user"] = user
        return data
