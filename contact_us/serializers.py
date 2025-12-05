from rest_framework import serializers
from .models import ContactUsMessage, FAQ, Support

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