from rest_framework import serializers
from .models import Card, CardBenefit, UserCard, UserCardHistory

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

class UserCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCard
        fields = [
            'id',
            'user',
            'card',
            'start_at',
            'end_at',
            'is_active',
            'created_at',
            'updated_at',
        ]
   
# class BuyCardSerializer(serializers.Serializer):
#     card = serializers.IntegerField()

#     def validate_card(self, value):
#         try:
#             card = Card.objects.get(id=value)
#         except Card.DoesNotExist:
#             raise serializers.ValidationError("Card with this ID does not exist.")
#         return value

#     def create(self, validated_data):
#         from datetime import timedelta, timezone
#         today = timezone.now()
#         user = self.context['request'].user
#         card = Card.objects.get(id=validated_data['card_id'])
#         if card.duration == '1_month':
#             end_at = today + timedelta(days=30)
#         elif card.duration == '1_week':
#             end_at = today + timedelta(days=7)
#         elif card.duration == '1_day':
#             end_at = today + timedelta(days=1)
#         user_card = UserCard.objects.create(
#             user=user,
#             card=card,
#             start_at=today,
#             end_at=end_at,
#             is_active=True
#         )
#         return user_card

class BuyCardSerializer(serializers.Serializer):
    card = serializers.IntegerField()

    def validate_card(self, value):
        if not Card.objects.filter(id=value).exists():
            raise serializers.ValidationError("Card with this ID does not exist.")
        return value

    def create(self, validated_data):
        from django.utils import timezone
        from datetime import timedelta

        user = self.context['request'].user
        card = Card.objects.get(id=validated_data['card'])
        now = timezone.now()

        # ----------------------------------------------
        # 1️⃣ Auto-expire cards that should be expired
        # ----------------------------------------------
        UserCard.objects.filter(
            user=user,
            is_active=True,
            end_at__lt=now
        ).update(is_active=False)

        # ----------------------------------------------
        # 2️⃣ Check if UserCard for this card exists
        #    (active or inactive)
        # ----------------------------------------------
        existing_user_card = UserCard.objects.filter(
            user=user,
            card=card
        ).first()

        # ----------------------------------------------
        # If user has active card of another type → block
        # ----------------------------------------------
        active_other_card = UserCard.objects.filter(
            user=user,
            is_active=True
        ).exclude(card=card).first()

        if active_other_card:
            raise serializers.ValidationError(
                "You already have an active card. Please wait until it expires."
            )

        # ----------------------------------------------
        # 3️⃣ Calculate duration
        # ----------------------------------------------
        days = self.get_duration_days(card.duration)
        new_end_date = now + timedelta(days=days)

        # ----------------------------------------------
        # 4️⃣ If same card exists (inactive or active) → UPDATE
        # ----------------------------------------------
        if existing_user_card:
            # Two behaviors possible:

            # A) Renew logic (extend existing end_at)
            if existing_user_card.is_active:
                existing_user_card.end_at += timedelta(days=days)
            else:
                # B) Reactivate logic (reset new cycle)
                existing_user_card.start_at = now
                existing_user_card.end_at = new_end_date
                existing_user_card.is_active = True

            existing_user_card.save()

            # Log history
            UserCardHistory.objects.create(
                user=user,
                card=card,
                action="renew" if existing_user_card.is_active else "purchase",
                start_at=existing_user_card.start_at,
                end_at=existing_user_card.end_at
            )

            return existing_user_card

        # ----------------------------------------------
        # 5️⃣ No record exists → create new one
        # ----------------------------------------------
        user_card = UserCard.objects.create(
            user=user,
            card=card,
            start_at=now,
            end_at=new_end_date,
            is_active=True
        )

        UserCardHistory.objects.create(
            user=user,
            card=card,
            action="purchase",
            start_at=now,
            end_at=new_end_date
        )

        return user_card

    def get_duration_days(self, duration):
        duration_map = {
            '1_month': 30,
            '1_week': 7,
            '1_day': 1,
        }
        if duration not in duration_map:
            raise serializers.ValidationError("Invalid card duration.")
        return duration_map[duration]


class CancelSubscriptionSerializer(serializers.Serializer):
    id = serializers.IntegerField()