from django.urls import path
from .views import RegisterView, LogoutView, CustomLoginView

urlpatterns = [
    path("registration/", RegisterView.as_view(), name="registration"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
