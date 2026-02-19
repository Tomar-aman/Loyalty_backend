from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from users.models import City, Country, UserSearchHistory
from users.serializers import AppleNativeAuthSerializer, CitySerializer, CompleteSignUpSerializer, LogoutSerializer, SignupSerializer, OTPVerificationSerializer, ResendOTPSerializer, UserDetailsSerializer, GoogleAuthSerializer, CountrySerializer, UserSearchHistorySerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework import filters
import json

def bulk_import_countries(json_path: str) -> None:
    """
    Bulk import countries from JSON file.
    Inserts new records and updates existing ones using `code` as unique field.
    """
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    countries = [
        Country(
            name=item["country"],
            code=item["code"].lower(),
            phone_code=item.get("phone_code"),
            flag=item.get("flag"),
        )
        for item in data
        if item.get("code") and item.get("country")
    ]

    Country.objects.bulk_create(
        countries,
        update_conflicts=True,
        unique_fields=["code"],
        update_fields=["name", "phone_code", "flag"],
    )
class SignupView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.save()
            # bulk_import_countries("new_c.json")
            return Response({"message": "User created. OTP sent to your email.", "otp": otp}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ResendOTPView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = ResendOTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.save()
            return Response({"message": "OTP resent to your email.", "otp": otp.otp_code}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerifyView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OTPVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            user_data = UserDetailsSerializer(user).data
            user_data["refresh"] = str(refresh)
            user_data["access"] = str(refresh.access_token)
            if user.is_active and not user.is_temp:
              user_data['message'] = "Login successful. Welcome back!"
            else:
                user_data['message'] = "OTP verified. Now Complete your profile to activate your account."
            
            return Response(user_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteSignUpView(GenericAPIView):
    serializer_class = CompleteSignUpSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.create(serializer.validated_data)
            user_data = UserDetailsSerializer(user, context={'request': request}).data
            user_data["message"] = "Profile completed successfully."

            return Response(user_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GoogleLoginView(GenericAPIView):
    """
    Google Login View
    """
    serializer_class = GoogleAuthSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        is_new_user = serializer.validated_data['is_new_user']  # 🔑 get flag
        refresh = RefreshToken.for_user(user)

        user_data = UserDetailsSerializer(user, context={'request': request}).data
        user_data["refresh"] = str(refresh)
        user_data["access"] = str(refresh.access_token)
        user_data["is_new_user"] = is_new_user  # ✅ add in response
        user_data["message"] = (
            "Signup successful. Welcome!" if is_new_user
            else "Login successful. Welcome back!"
        )

        return Response(user_data, status=status.HTTP_200_OK)


# class FacebookLoginView(GenericAPIView):
#     """
#     Facebook Login View
#     """
#     serializer_class = FacebookAuthSerializer
#     permission_classes = [AllowAny]

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data, context={'request': request})
#         serializer.is_valid(raise_exception=True)

#         user = serializer.validated_data['user']
#         is_new_user = serializer.validated_data['is_new_user']
#         refresh = RefreshToken.for_user(user)

#         user_data = UserDetailsSerializer(user, context={'request': request}).data
#         user_data["refresh"] = str(refresh)
#         user_data["access"] = str(refresh.access_token)
#         user_data["is_new_user"] = is_new_user
#         user_data["message"] = (
#             "Signup successful. Welcome!" if is_new_user
#             else "Login successful. Welcome back!"
#         )

#         return Response(user_data, status=status.HTTP_200_OK)

class AppleNativeLoginView(GenericAPIView):
    """
    Apple Login View using Firebase
    """
    serializer_class = AppleNativeAuthSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        is_new_user = serializer.validated_data['is_new_user']
        refresh = RefreshToken.for_user(user)

        user_data = UserDetailsSerializer(user, context={'request': request}).data
        user_data["refresh"] = str(refresh)
        user_data["access"] = str(refresh.access_token)
        user_data["is_new_user"] = is_new_user
        user_data["message"] = (
            "Signup successful. Welcome!" if is_new_user
            else "Login successful. Welcome back!"
        )

        return Response(user_data, status=status.HTTP_200_OK)


class ProfileView(GenericAPIView):

    serializer_class = UserDetailsSerializer

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LogoutView(GenericAPIView):
    """
    View for logging out the authenticated user.
    """
    serializer_class = LogoutSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            refresh_token = request.data['refresh']

            # Blacklist refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except KeyError:
            return Response({"error": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class DeleteUserView(GenericAPIView):
    
    def delete(self, request, *args, **kwargs):
        try:
            user = request.user
            if user.phone_number:
                user.phone_number += '_del' + str(user.id)
            else:
                user.phone_number = '_del' + str(user.id)  

            if user.email:
                user.email += '_deleted' + str(user.id)
            else:
                user.email = f'deleted_{user.id}@example.com' 
            user.is_active = False
            user.save()
            
            return Response({
                'message': 'Account deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)



class CountryListView(GenericAPIView):
    """
    View to list all countries.
    """
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]

    # enable search and ordering
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code", "phone_code"]
    ordering_fields = ["name", "code"]
    ordering = ["name"]

    def get_queryset(self):
        # base queryset
        return Country.objects.all().order_by("name")

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CityListView(GenericAPIView):
    """
    GET /api/cities/
    - Paginated
    - Search by city name with ?search=
    - Filter by country id or country code with ?country= or ?country_code=
    - Sort with ?ordering=name or ?ordering=-created_at
    """

    serializer_class = CitySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return City.objects.select_related('country').all().order_by('name')

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    filterset_fields = ['country', 'is_popular', 'country__code']  # allow ?country=1 or ?is_popular=true or ?country__c

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', None)
        if search_term and request.user.is_authenticated:
            UserSearchHistory.objects.create(user=request.user, search=search_term)

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PopularCityListView(GenericAPIView):
    """
    View to list popular cities.
    """
    serializer_class = CitySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return City.objects.filter(is_popular=True).select_related('country').order_by('name')

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserSearchHistoryView(GenericAPIView):
    """
    View to list user's search history.
    """
    serializer_class = UserSearchHistorySerializer

    def get_queryset(self):
        return UserSearchHistory.objects.filter(user=self.request.user).order_by('-searched_at')

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)