from django.urls import path, include
from .views import ProfileDetailView, BusinessProfileListView, CustomerProfileListView, OfferViewSet, \
    OfferDetailView, OrderViewSet, OrderCountView, CompletedOrderCountView, ReviewViewSet, BaseInfoView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offer')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet, basename='review')
urlpatterns = [
    path('', include(router.urls)),
    path('offerdetails/<int:pk>/', OfferDetailView.as_view(), name='offer-detail'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/business/', BusinessProfileListView.as_view(), name='profile-business'),
    path('profiles/customer/', CustomerProfileListView.as_view(), name='profile-customers'),
    path('order-count/<int:pk>/', OrderCountView.as_view(), name='order-count'),
    path('completed-order-count/<int:pk>/', CompletedOrderCountView.as_view(), name='completed-order-count'),
    path('base-info/', BaseInfoView.as_view(), name='base-info'),

]