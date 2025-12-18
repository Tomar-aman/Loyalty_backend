from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from notification.models import Notification
from notification.serializers import NotificationSerializer

class NotificationListView(GenericAPIView):
    """
    GET /api/notifications/  -> list user notifications
    """
    serializer_class = NotificationSerializer

    def get(self, request, *args, **kwargs):
        try:
            notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
            paginator = PageNumberPagination()
            paginated_notifications = paginator.paginate_queryset(notifications, request)
            serializer = self.get_serializer(paginated_notifications, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class NotificationDetailView(GenericAPIView):
    """
    GET /api/notifications/<int:pk>/  -> retrieve single notification
    """
    serializer_class = NotificationSerializer

    def get(self, request, pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(user=request.user, pk=pk)
            notification.is_read = True
            notification.save()
            serializer = self.get_serializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request, pk, *args, **kwargs):
        """
        PATCH /api/notifications/<int:pk>/  -> mark notification as read
        """
        try:
            notification = Notification.objects.filter(user=request.user, pk=pk).first()
            if not notification:
                return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
            notification.is_read = True
            notification.save()
            serializer = self.get_serializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MarkAllNotificationsReadView(GenericAPIView):
    """
    PATCH /api/notifications/mark-all-read/  -> mark all notifications as read
    """
    serializer_class = NotificationSerializer

    def get(self, request, *args, **kwargs):
        try:
            notifications = Notification.objects.filter(user=request.user, is_read=False)
            notifications.update(is_read=True)
            return Response({"message": "All notifications marked as read."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)