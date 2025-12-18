from django.urls import path
from .views import BusinessCategoryListView, BusinessListView, BusinessDetailView, PopularDealsAPIView, RedeemedOfferAPIView

urlpatterns = [
    path('categories/', BusinessCategoryListView.as_view(), name='business-category-list'),
    path('businesses/', BusinessListView.as_view(), name='business-list'),
    path('businesses/<int:pk>/', BusinessDetailView.as_view(), name='business-detail'),
    path('popular/', PopularDealsAPIView.as_view(), name='popular-deals'),
    path('redeemed-offers/', RedeemedOfferAPIView.as_view(), name='redeemed-offers'),
]