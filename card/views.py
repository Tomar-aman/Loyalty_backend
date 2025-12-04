from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CardSerializer
from .models import Card

class CardListView(GenericAPIView):
    queryset = Card.objects.all().order_by('price')
    serializer_class = CardSerializer

    def get(self, request, *args, **kwargs):
        cards = self.get_queryset()
        serializer = self.get_serializer(cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
