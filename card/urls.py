from django.urls import path
from .views import CardListView

urlpatterns = [
    path('cards/', CardListView.as_view(), name='card-list'),
]