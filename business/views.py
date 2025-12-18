from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    GenericAPIView
)
from rest_framework.response import Response
from rest_framework import status

from business.models import (
    BusinessCategory,
    Business, BusinessOffer, RedeemedOffer
)
from business.serializers import (
    BusinessCategorySerializer,
    BusinessSerializer,
    BusinessDetailSerializer,
    PopularOfferSerializer,
    RedeemedOfferSerializer
)
from django.utils import timezone

class BusinessCategoryListView(GenericAPIView):
    serializer_class = BusinessCategorySerializer

    def get(self, request, *args, **kwargs):
        try:
            categories = BusinessCategory.objects.filter(is_active=True)
            serializer = self.get_serializer(categories, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BusinessListView(GenericAPIView):
    """
    GET /api/businesses/  -> list active businesses (summary)
    """
    serializer_class = BusinessSerializer
    queryset = Business.objects.filter(is_active=True).select_related('category')

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.GET.get('category')
        search = self.request.GET.get('search')
        is_featured = self.request.GET.get('is_featured')
        if is_featured:
            qs = qs.filter(is_featured=is_featured)
        if category:
            qs = qs.filter(category_id=category)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs
    
    def get(self, request, *args, **kwargs):
        try:
            businesses = self.get_queryset()
            page = self.paginate_queryset(businesses)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(businesses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BusinessDetailView(RetrieveAPIView):
    """
    GET /api/businesses/<pk>/ -> detailed business info
    """
    serializer_class = BusinessDetailSerializer
    queryset = Business.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class PopularDealsAPIView(ListAPIView):
    """
    Returns all active popular deals with their business details.
    """
    serializer_class = PopularOfferSerializer

    def get_queryset(self):
        now = timezone.now()
        return (
            BusinessOffer.objects
            .select_related("business", "business__category")  # avoids N+1
            .filter(
                is_popular=True,
                is_active=True,
                business__is_active=True,
                start_date__lte=now,
                end_date__gte=now,
            )
            .order_by("-created_at")
        )

class RedeemedOfferAPIView(GenericAPIView):
    """
    Returns all redeemed offers for the authenticated user.
    """
    serializer_class = RedeemedOfferSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, context ={'request': request})
            serializer.is_valid(raise_exception=True)  
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)