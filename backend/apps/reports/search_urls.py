from django.urls import path

from . import search_views

urlpatterns = [
    path("", search_views.global_search),
]
