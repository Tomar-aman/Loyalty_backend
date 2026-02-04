from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import NewsArticle
from .serializers import NewsArticleSerializer
from rest_framework.permissions import AllowAny
from django.db import DatabaseError

class NewsArticleListView(GenericAPIView):
    permission_classes = [AllowAny]
    queryset = NewsArticle.objects.all().order_by('-published_at')
    serializer_class = NewsArticleSerializer

    def get(self, request, *args, **kwargs):
        try:
            articles = self.get_queryset()

            # Apply pagination correctly
            page = self.paginate_queryset(articles)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            # No pagination (fallback)
            serializer = self.get_serializer(articles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except DatabaseError as db_err:
            return Response(
                {"error": "Database error occurred", "detail": str(db_err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
