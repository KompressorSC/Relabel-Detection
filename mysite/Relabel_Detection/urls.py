from . import views
from django.urls import path
from django.contrib.auth.views import LogoutView

app_name = "Relabel_Detection"
urlpatterns = [
    path("main/", views.main, name="main"),
    path("settings/", views.settings, name="settings"),
    path("history/", views.history, name="history"),
    path("live/", views.live, name="live"),
    path("video/", views.video, name="video"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.register, name="register"),
    path(
        "logout/",
        LogoutView.as_view(next_page="/Relabel_Detection/main/"),
        name="logout",
    ),
]
