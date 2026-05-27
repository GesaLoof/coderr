from django.urls import path, include
from .views import ProfileDetailView, BusinessProfileListView, CustomerProfileListView, OfferViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offer')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/business/', BusinessProfileListView.as_view(), name='profile-business'),
    path('profiles/customer/', CustomerProfileListView.as_view(), name='profile-customers'),

]