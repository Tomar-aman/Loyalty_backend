from django.urls import path
from .views import CardListView, UserCardView, BuyCardView

urlpatterns = [
    path('', CardListView.as_view(), name='card-list'),
    path('buy-card/', BuyCardView.as_view(), name='buy-card'),
    path('user-cards/', UserCardView.as_view(), name='user-cards'),
]