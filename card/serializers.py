from rest_framework import serializers
from .models import Card, CardBenefit

class CardBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardBenefit
        fields = ['id', 'title', 'description', 'icon']

class CardSerializer(serializers.ModelSerializer):
    benefits = CardBenefitSerializer(many=True, read_only=True)

    class Meta:
        model = Card
        fields = [
            'id',
            'name',
            'duration',
            'price',
            'short_description',
            'is_active',
            'created_at',
            'updated_at',
            'benefits',
        ]