from django.urls import path, include
from .views import ProfileDetailView, BusinessProfileListView, CustomerProfileListView, OfferViewSet, OfferDetailView, OrderViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offer')
router.register(r'orders', OrderViewSet, basename='order')
urlpatterns = [
    path('', include(router.urls)),
    path('offerdetails/<int:pk>/', OfferDetailView.as_view(), name='offer-detail'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/business/', BusinessProfileListView.as_view(), name='profile-business'),
    path('profiles/customer/', CustomerProfileListView.as_view(), name='profile-customers'),

]