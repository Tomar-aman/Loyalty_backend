from django.utils import timezone
from rest_framework import serializers
from .models import BusinessCategory, Business, BusinessImage, BusinessOffer, RedeemedOffer
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
        fields = ['id', 'title', 'description', 'coupon_code', 'start_date', 'end_date', 'is_active']

# summary serializer for lists
class BusinessSerializer(serializers.ModelSerializer):
    category = BusinessCategorySerializer(read_only=True)
    offers = BusinessOfferSerializer(many=True, read_only=True)
    class Meta:
        model = Business
        fields = ['id','name', 'description', 'address', 'phone_number', 'email', 'website',
            'latitude', 'longitude','offers',
            'logo', 'category', 'is_featured', 'created_at', 'updated_at']

# detailed serializer for single business view
class BusinessDetailSerializer(serializers.ModelSerializer):
    category = BusinessCategorySerializer(read_only=True)
    images = BusinessImageSerializer(source='gallery_images', many=True, read_only=True)
    offers = BusinessOfferSerializer(many=True, read_only=True)

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'description', 'address', 'phone_number', 'email', 'website',
            'latitude', 'longitude',
            'logo', 'category', 'is_active', 'is_featured',
            'images', 'offers', 'created_at', 'updated_at'
        ]

class PopularOfferSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(read_only=True)

    class Meta:
        model = BusinessOffer
        fields = [
            "id",
            "title",
            "coupon_code",
            "description",
            "start_date",
            "end_date",
            "is_popular",
            "business",
        ]

class RedeemedOfferSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(source='offer.business', read_only=True)

    class Meta:
        model = RedeemedOffer
        fields = ['id','offer' ,'redeemed_at', 'is_used', 'business']
    
    def validate(self, attrs):
        user = self.context['request'].user
        offer = attrs.get('offer')
        now = timezone.now()
        # Check if User have plan to redeem
        if not user.user_cards.filter(is_active=True).exists():
                raise serializers.ValidationError({
                    "error": "You need an active plan to redeem offers."
                })

        if not offer.is_active:
            raise serializers.ValidationError({
                "error": "This offer is not active."
            })

        if not (offer.start_date <= now <= offer.end_date):
            raise serializers.ValidationError({
                "error": "This offer is not valid at this time."
            })

        if RedeemedOffer.objects.filter(user=user, offer=offer).exists():
            raise serializers.ValidationError({
                "error": "You have already redeemed this offer."
            })

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        offer = validated_data['offer']
        redeemed_offer = RedeemedOffer.objects.create(
            user=user,
            offer=offer
        )
        return redeemed_offer