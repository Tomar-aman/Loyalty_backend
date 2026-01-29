from rest_framework import serializers
from users.models import User, OTP, Country, City, UserSearchHistory
from django.utils import timezone
import random
from datetime import timedelta
from config.utils import send_mail
import requests
from django.core.files.base import ContentFile
from card.serializers import UserCardSerializer

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'phone_code', 'flag']

class CitySerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    country_code = serializers.CharField(source='country.code', read_only=True)


    class Meta:
        model = City
        fields = [
            'id',
            'name',
            'is_popular',
            'icon',
            'country_name',
            'country_code',
            # 'created_at',
            # 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'country_code',
          
        ]
        extra_kwargs = {
            'email': {'validators': []}, 
        }
    
    # def validate(self, attrs):
    #     # Check if email already exists
    #     if User.objects.filter(email=attrs['email'].lower(), is_temp=False).exists():
    #         raise serializers.ValidationError({
    #             "email": "Email already exists."
    #         })
        
    #     return attrs
    
    def create(self, validated_data):
        email = validated_data.get('email').lower()
        try:
            # Check if inactive user exists with same email or phone number
            user = User.objects.get(email=email)
            # Update user details
            # for attr, value in validated_data.items():
            #     setattr(user, attr, value)
            # user.set_password(validated_data['password'])
            # user.save()
        except User.DoesNotExist:
            user = User.objects.create_user(**validated_data)
            user.is_active = False
            user.save()

        try:
            OTP.objects.filter(user=user).delete()  # Clean up old OTPs
        except OTP.DoesNotExist:
            pass
        # Generate and save OTP
        otp_code = str(random.randint(100000, 999999))
        OTP.objects.update_or_create(
            user=user,
            defaults={
                'otp_code': otp_code,
                'expires_at': timezone.now() + timedelta(minutes=10)
            }
        )

        # Send OTP
        # send_mail(
        #     subject="Your OTP Code",
        #     email_template_name='email/otp_email.html',
        #     context={"user": user, "otp_code": otp_code},
        #     to_email=user.email
        # )

        return otp_code


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    otp_code = serializers.CharField(max_length=6)
    device_token = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        user = self._get_user(attrs)
        otp = self._get_valid_otp(user, attrs['otp_code'])

        attrs['user'] = user
        return attrs

    def _get_user(self, attrs):
        filters = {'email': attrs.get('email').lower()} if attrs.get('email') else {'phone_number': attrs.get('phone_number')}
        user = User.objects.filter(**filters).first()
        if not user:
            raise serializers.ValidationError({
                'email' if 'email' in filters else 'phone_number': "User not found."
            })
        return user

    def _get_valid_otp(self, user, otp_code):
        otp = OTP.objects.filter(user=user, otp_code=otp_code).order_by('-created_at').first()
        if not otp:
            raise serializers.ValidationError({
                'otp_code': "Invalid OTP."
            })
        if otp.is_expired():
            raise serializers.ValidationError({
                'otp_code': "OTP has expired."
            })
        return otp

    def save(self, **kwargs):
        user = self.validated_data['user']
        device_token = self.validated_data.get('device_token')
        user.is_active = True
        if device_token:
            user.device_token = device_token
        user.save()
        OTP.objects.filter(user=user).delete()  # Clean up
        return user
    
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    # phone_number = serializers.CharField(required=False)
    def validate(self, attrs):
        identifier = attrs.get('email')  # or phone_number
        if not identifier:
            raise serializers.ValidationError("Email is required.")
        return attrs
    
    def save(self, **kwargs):
        try:
            user = User.objects.get(email=self.validated_data['email'].lower())
            # otp_code = ''.join(random.choices('0123456789', k=6))
            otp_code = str(random.randint(100000, 999999))
            otp = OTP.objects.create(user=user, otp_code=otp_code, expires_at=timezone.now() + timedelta(minutes=10))
            # send_mail(
            #     subject="Your New OTP Code",
            #     email_template_name="email/resend_otp_email.html",
            #     context={
            #         "user": user,
            #         "otp_code": otp_code
            #     },
            #     to_email=user.email
            # )
            return otp
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
class CompleteSignUpSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    customer_id = serializers.CharField(required=False, allow_blank=True)
    dob = serializers.DateField(required=False, allow_null=True)
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), required=False, allow_null=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user:
            raise serializers.ValidationError("User not found.")
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
      instance = self.context['request'].user
      
      # Update remaining fields
      for key, value in validated_data.items():
          setattr(instance, key, value)

      instance.is_temp = False
      instance.save()

      return instance
    

class UserDetailsSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    country = CountrySerializer(read_only=True)

    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), source='city', write_only=True, required=False, allow_null=True
    )
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source='country', write_only=True, required=False, allow_null=True
    )
    city_name = serializers.CharField(write_only=True, required=False)
    country_name = serializers.CharField(write_only=True, required=False)
    card = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number','profile_picture','customer_id','dob',
            'country',
            'city',
            'city_name',
            'country_name',
            'country_code','is_active','is_temp', 'country_id', 'city_id' , 'card'
        ]
    
    def update(self, instance, validated_data):
        # Update nested fields
        city_name = validated_data.pop('city_name', None)
        country_name = validated_data.pop('country_name', None)
        print(f"Updating user details with city_name: {city_name}, country_name: {country_name}")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if not country_name:
            country_name = instance.country.name if instance.country else None
        city = City.objects.only("id").filter(name__iexact=city_name).first() if city_name else None
        country = Country.objects.only("id").filter(name__iexact=country_name).first() if country_name else None

        if city is not None:
            instance.city = city
        else:
            new_city = City.objects.create(name=city_name.capitalize(), country=country) if city_name else None
            instance.city = new_city
        if country is not None:
            instance.country = country

        instance.save()
        return instance
    
    def get_card(self, obj):
        card = (
            obj.user_cards
            .filter(is_active=True)
            .select_related("card")
            .first()
        )
        return UserCardSerializer(card).data if card else None
    
        

class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()
    device_token = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        token = attrs.get('token')
        if not token:
            raise serializers.ValidationError('Token is required.')

        try:
            # Step 1: Call Google UserInfo API using the access token
            response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise serializers.ValidationError("Invalid Google access token")

            user_info = response.json()
            email = user_info.get("email")
            name = user_info.get("name", "")
            google_id = user_info.get("sub")
            picture_url = user_info.get("picture")

            if not email:
                raise serializers.ValidationError("Email not found in token.")

            first_name = name.split()[0] if name else ""
            last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""

            # Step 2: Create or get the user
            user, created = User.objects.get_or_create(
                email=email,
                # google_id=google_id,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "google_id": google_id,
                }
            )
            # Update profile image
            if picture_url:
                if created or not user.profile_picture:
                    img_response = requests.get(picture_url)
                    if img_response.status_code == 200:
                        file_name = f"{google_id}.jpg"
                        user.profile_picture.save(file_name, ContentFile(img_response.content), save=True)

            # Step 4: Update google_id if it's missing
            if not created and not user.google_id:
                user.google_id = google_id
                user.save()
            
            user.device_token = attrs.get('device_token', '') or user.device_token
            user.save()
            attrs["user"] = user
            attrs["is_new_user"] = created  
            return attrs

        except Exception as e:
            raise serializers.ValidationError(f'Invalid token. {str(e)}',)
        except Exception:
            raise serializers.ValidationError('Authentication failed.')
        
# class FacebookAuthSerializer(serializers.Serializer):
#     token = serializers.CharField()

#     def validate(self, attrs):
#         token = attrs.get("token")
#         if not token:
#             raise serializers.ValidationError("Token is required.")

#         try:
#             # Step 1: Call Facebook Graph API using the access token
#             response = requests.get(
#                 "https://graph.facebook.com/me",
#                 params={
#                     "fields": "id,name,email,picture",
#                     "access_token": token,
#                 },
#             )
#             if response.status_code != 200:
#                 raise serializers.ValidationError("Invalid Facebook access token")


#             user_info = response.json()
#             fb_id = user_info.get("id")
#             email = user_info.get("email")
#             name = user_info.get("name", "")
#             picture_data = user_info.get("picture", {}).get("data", {})
#             picture_url = picture_data.get("url")

#             if not email:
#                 raise serializers.ValidationError("Email not found in token. Please allow email permission.")

#             first_name = name.split()[0] if name else ""
#             last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""

#             # Step 2: Create or get the user
#             user, created = User.objects.get_or_create(
#                 email=email,
#                 defaults={
#                     "first_name": first_name,
#                     "last_name": last_name,
#                     "facebook_id": fb_id,
#                 }
#             )

#             # Step 3: Save profile picture if available
#             if picture_url:
#                 if created or not user.profile_picture:
#                     img_response = requests.get(picture_url)
#                     if img_response.status_code == 200:
#                         file_name = f"{fb_id}.jpg"
#                         user.profile_picture.save(file_name, ContentFile(img_response.content), save=True)

#             # Step 4: Update facebook_id if missing
#             if not created and not user.facebook_id:
#                 user.facebook_id = fb_id
#                 user.save()

#             attrs["user"] = user
#             attrs["is_new_user"] = created
#             return attrs

#         except Exception as e:
#             raise serializers.ValidationError(f"Invalid token. {str(e)}")


# class AppleFirebaseAuthSerializer(serializers.Serializer):
#     token = serializers.CharField()

#     def validate(self, attrs):
#         if not initialize_firebase():
#             raise serializers.ValidationError("Firebase is not configured.")
#         token = attrs.get("token")
#         if not token:
#             raise serializers.ValidationError("Token is required.")

#         try:
#             # Step 1: Verify Firebase ID token (already verified by Firebase backend)
#             decoded = auth.verify_id_token(token)

#             email = decoded.get("email")
#             uid = decoded.get("uid")
#             name = decoded.get("name", "")
#             provider = decoded.get("firebase", {}).get("sign_in_provider")

#             if provider != "apple.com":
#                 raise serializers.ValidationError("Invalid provider for this endpoint.")

#             first_name = name.split()[0] if name else ""
#             last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""

#             # Step 2: Create or get the user
#             user, created = User.objects.get_or_create(
#                 email=email,
#                 defaults={
#                     "first_name": first_name,
#                     "last_name": last_name,
#                     "apple_id": uid,
#                 }
#             )

#             # Step 3: Update Apple ID if missing
#             if not created and not user.apple_id:
#                 user.apple_id = uid
#                 user.save()

#             attrs["user"] = user
#             attrs["is_new_user"] = created
#             return attrs

#         except Exception as e:
#             raise serializers.ValidationError(f"Invalid Firebase token: {str(e)}")

    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    
    def create(self, validated_data):
        user = self.context['request'].user
        if not user.check_password(validated_data['old_password']):
            raise serializers.ValidationError("Incorrect old password.")
        if validated_data['new_password'] != validated_data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        user.set_password(validated_data['new_password'])
        user.is_active = True
        user.save()
        return user
    
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class UserSearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSearchHistory
        fields = ['id', 'search', 'searched_at']