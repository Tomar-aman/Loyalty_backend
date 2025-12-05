from django.urls import path
from .views import BusinessCategoryListView, BusinessListView, BusinessDetailView

urlpatterns = [
    path('categories/', BusinessCategoryListView.as_view(), name='business-category-list'),
    path('businesses/', BusinessListView.as_view(), name='business-list'),
    path('businesses/<int:pk>/', BusinessDetailView.as_view(), name='business-detail'),
]