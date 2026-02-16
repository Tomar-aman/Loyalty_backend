from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import NewsArticle
from .serializers import NewsArticleSerializer
from rest_framework.permissions import AllowAny
from django.db import DatabaseError
from django.db.models import Q

class NewsArticleListView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = NewsArticleSerializer

    def get_queryset(self):
        """
        Override get_queryset to apply search filters
        """
        queryset = NewsArticle.objects.all().order_by('-published_at')
        
        # Get search parameter from query params
        search = self.request.query_params.get('search', None)
        
        if search:
            # Search in title and content fields (case-insensitive)
            queryset = queryset.filter(
                Q(title__icontains=search)  #| Q(content__icontains=search)
            )
        
        return queryset

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
