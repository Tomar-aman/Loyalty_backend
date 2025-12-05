from rest_framework import serializers
from .models import BusinessCategory, Business, BusinessImage, BusinessOffer
from users.models import User

class BusinessCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCategory
        fields = ['id', 'name', 'icon']

# small owner serializer
class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']

# image serializer
class BusinessImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BusinessImage
        fields = ['id', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            try:
                return request.build_absolute_uri(obj.image.url) if request else obj.image.url
            except Exception:
                return None
        return None

# offer serializer
class BusinessOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessOffer
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'is_active']

# summary serializer for lists
class BusinessSerializer(serializers.ModelSerializer):
    category = BusinessCategorySerializer(read_only=True)
    owner = OwnerSerializer(read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = ['id', 'name', 'logo_url', 'category', 'owner', 'is_active', 'is_featured']

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo:
            try:
                return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url
            except Exception:
                return None
        return None

# detailed serializer for single business view
class BusinessDetailSerializer(serializers.ModelSerializer):
    category = BusinessCategorySerializer(read_only=True)
    images = BusinessImageSerializer(source='businessimage_set', many=True, read_only=True)
    offers = BusinessOfferSerializer(source='businessoffer_set', many=True, read_only=True)

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'description', 'address', 'phone_number', 'email', 'website',
            'logo', 'category', 'is_active', 'is_featured',
            'images', 'offers', 'created_at', 'updated_at'
        ]
