from rest_framework import serializers
from .models import NewsArticle
from business.serializers import BusinessCategorySerializer
from users.serializers import CitySerializer

class NewsArticleSerializer(serializers.ModelSerializer):
    category = BusinessCategorySerializer(read_only=True)
    city = CitySerializer(read_only=True)
    
    class Meta:
        model = NewsArticle
        fields = ['id', 'title', 'content', 'icon', 'category', 'city', 'published_at']