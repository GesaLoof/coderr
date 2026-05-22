from rest_framework import permissions, viewsets
from .serializers import ProfileDetailSerializer, ProfileUpdateSerializer
from coderr_app.models import CoderrProfile
from auth_app.models import Profile
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from coderr_app.permissions import IsOwnerOrReadOnly
from rest_framework.response import Response

class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Get or patch a single profile by pk."""
    
    http_method_names = ['get', 'patch', 'head', 'options']  # block put
    
    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return ProfileUpdateSerializer
        return ProfileDetailSerializer

    def get_object(self):
        try:
            obj = Profile.objects.get(pk=self.kwargs['pk'])
        except Profile.DoesNotExist:
            raise NotFound("No profile matches the given query.")
        self.check_object_permissions(self.request, obj)
        return obj
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ProfileUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        # use ProfileDetailSerializer for the response
        response_serializer = ProfileDetailSerializer(updated_instance)
        return Response(response_serializer.data)

class BusinessProfileListView(generics.ListAPIView):
    """List all profiles with type 'business'."""
    
    serializer_class = ProfileDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Profile.objects.filter(type='business')


class CustomerProfileListView(generics.ListAPIView):
    """List all profiles with type 'customer'."""
    
    serializer_class = ProfileDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Profile.objects.filter(type='customer')

