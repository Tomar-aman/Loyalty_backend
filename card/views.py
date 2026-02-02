from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CancelSubscriptionSerializer, CardSerializer, UserCardSerializer, BuyCardSerializer
from .models import Card, UserCard, UserCardHistory

class CardListView(GenericAPIView):
    queryset = Card.objects.all().order_by('price')
    serializer_class = CardSerializer

    def get(self, request, *args, **kwargs):
        cards = self.get_queryset()
        serializer = self.get_serializer(cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BuyCardView(GenericAPIView):
    serializer_class = BuyCardSerializer

    def post(self, request):
        serializer = BuyCardSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user_card = serializer.save()

        return Response({
            "message": "Card purchased successfully",
            "card_id": user_card.card.id,
            "start_at": user_card.start_at,
            "end_at": user_card.end_at
        }, status=status.HTTP_201_CREATED)

class UserCardView(GenericAPIView):
    serializer_class = UserCardSerializer
    
    def get(self, request, *args, **kwargs):
        try:
            user_cards = UserCard.objects.get(user=request.user, is_active=True)
            serializer = self.get_serializer(user_cards)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserCard.DoesNotExist:
            return Response({"error": "No active card found for the user."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CancelSubscriptionView(GenericAPIView):
    serializer_class = CancelSubscriptionSerializer
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                card_id = serializer.validated_data['id']
                user_card = UserCard.objects.get(id=card_id, user=request.user, is_active=True)
                user_card.is_active = False
                user_card.save()
                # Log history
                UserCardHistory.objects.create(
                    user=user_card.user,
                    card=user_card.card,
                    action="cancel",
                    start_at=user_card.start_at,
                    end_at=user_card.end_at
                )
                return Response({"message": "Subscription cancelled successfully."}, status=status.HTTP_200_OK)
        except UserCard.DoesNotExist:
            return Response({"error": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)