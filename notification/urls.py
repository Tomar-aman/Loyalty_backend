from django.urls import path
from .views import NotificationListView, MarkAllNotificationsReadView, NotificationDetailView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('mark-all-read/', MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
]