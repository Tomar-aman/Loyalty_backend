from google_crc32c import value
from rest_framework import serializers
from .models import ContactUsMessage, FAQ, Support, SubsciberEmail, LandingPageContent

class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Support
        fields = ['id', 'country_code', 'phone_number', 'email']
  
class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer',]

class ContactUsMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUsMessage
        fields = ['id', 'name', 'email', 'subject', 'message',]

class SubscriberEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsciberEmail
        fields = ['id', 'email']
    
    # def validate_email(self, value):
    #     if SubsciberEmail.objects.filter(email=value).exists():
    #         raise serializers.ValidationError("This email is already subscribed.")
    #     return value

class LandingPageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingPageContent
        fields = '__all__'