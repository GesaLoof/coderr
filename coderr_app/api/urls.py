from django.urls import path, include
from .views import ProfileDetailView, BusinessProfileListView, CustomerProfileListView
from rest_framework.routers import DefaultRouter


urlpatterns = [
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/business/', BusinessProfileListView.as_view(), name='profile-business'),
    path('profiles/customers/', CustomerProfileListView.as_view(), name='profile-customers'),
]