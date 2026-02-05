from google_crc32c import value
from rest_framework import serializers
from .models import ContactUsMessage, FAQ, Support, SubsciberEmail, LandingPageContent, Address, SocialMediaLink, APPDownloadLink

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country']

class SupportSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()
    class Meta:
        model = Support
        fields = ['id', 'country_code', 'phone_number', 'email', 'address']

    def get_address(self, obj):
        address = Address.objects.first()
        if address:
            return AddressSerializer(address).data
        return None
  
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

class SocialMediaLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMediaLink
        fields = ['instagram', 'facebook', 'twitter', 'linkedin',]

class APPDownloadLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = APPDownloadLink
        fields = ['android_link', 'ios_link']

class LandingPageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingPageContent
        fields = '__all__'