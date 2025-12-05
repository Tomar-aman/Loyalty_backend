from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import ContactUsMessage, FAQ, Support
from .serializers import SupportSerializer, FAQSerializer, ContactUsMessageSerializer

class SupportListView(GenericAPIView):
    serializer_class = SupportSerializer

    def get(self, request, *args, **kwargs):
        try:
            supports = Support.objects.last()
            serializer = self.get_serializer(supports)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FAQListView(GenericAPIView):
    serializer_class = FAQSerializer

    def get(self, request, *args, **kwargs):
        try:
            faqs = FAQ.objects.filter(is_active=True)
            serializer = self.get_serializer(faqs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
class ContactUsMessageCreateView(GenericAPIView):
    serializer_class = ContactUsMessageSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Contact us message created successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)