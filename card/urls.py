from django.urls import path
from .views import CardListView, UserCardView, BuyCardView, CancelSubscriptionView

urlpatterns = [
    path('', CardListView.as_view(), name='card-list'),
    path('buy-card/', BuyCardView.as_view(), name='buy-card'),
    path('user-cards/', UserCardView.as_view(), name='user-cards'),
    path('cancel-subscription/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
]