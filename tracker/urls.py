from django.urls import path
from . import views

urlpatterns = [
    path("session/open/",          views.session_open,  name="session_open"),
    path("session/close/<int:session_id>/", views.session_close, name="session_close"),
    path("sessions/",              views.session_list,  name="session_list"),
]
