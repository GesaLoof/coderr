from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, CustomLoginSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken


class RegisterView(APIView):
    """Register a new user and return an auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Handle POST to create a new user and return token data."""
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.get(user=user)
            return Response(
                {
                    "token": token.key,
                    "fullname": user.profile.fullname,
                    "email": user.email,
                    "user_id": user.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(ObtainAuthToken):
    """Login a user and return an auth token."""

    permission_classes = [AllowAny]
    serializer_class = CustomLoginSerializer

    def post(self, request):
        """Handle POST to authenticate and return token data."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "fullname": user.profile.fullname,
                    "email": user.email,
                    "user_id": user.id,
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Delete the authenticated user's token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle POST to delete the user's token."""
        request.user.auth_token.delete()
        return Response(
            {"detail": "Logout succesful. Token deleted."}, status=status.HTTP_200_OK
        )
