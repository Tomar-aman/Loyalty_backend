from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import APPDownloadLink, ContactUsMessage, FAQ, LandingPageContent, SocialMediaLink, Support, SubsciberEmail
from .serializers import SupportSerializer, FAQSerializer, ContactUsMessageSerializer, SubscriberEmailSerializer, LandingPageContentSerializer, SocialMediaLinkSerializer, APPDownloadLinkSerializer
from rest_framework.permissions import AllowAny

class SupportListView(GenericAPIView):
    serializer_class = SupportSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            # Use get_object_or_404 or filter().first() to avoid caching
            support = Support.objects.filter().last()
            if not support:
                return Response({"error": "No support contact found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(support)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FAQListView(GenericAPIView):
    serializer_class = FAQSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            faqs = FAQ.objects.filter(is_active=True)
            serializer = self.get_serializer(faqs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
class ContactUsMessageCreateView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ContactUsMessageSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Contact us message created successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
class SubscriberEmailCreateView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SubscriberEmailSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():   
                serializer.save()
                return Response({"message": "Thanks for subscribing!"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)  
        

class SocialMediaLinkView(GenericAPIView):
    serializer_class = SocialMediaLinkSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            # Always query the database fresh, no caching
            social_link = SocialMediaLink.objects.last()
            if not social_link:
                return Response({"error": "No social media links found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(social_link)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class APPDownloadLinkView(GenericAPIView):
    serializer_class = APPDownloadLinkSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            # Always query the database fresh, no caching
            app_link = APPDownloadLink.objects.last()
            if not app_link:
                return Response({"error": "No app download links found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(app_link)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class LandingPageContentView(GenericAPIView):
    serializer_class = LandingPageContentSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            # Always query the database fresh, no caching
            landing_content = LandingPageContent.objects.filter().last()
            if not landing_content:
                return Response({"error": "No landing page content found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(landing_content, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)