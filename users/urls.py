from django.urls import path
from users.views import ProfileView, SignupView, OTPVerifyView, ResendOTPView, CompleteSignUpView, LogoutView, GoogleLoginView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify-otp/', OTPVerifyView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('complete-signup/', CompleteSignUpView.as_view(), name='complete_signup'),
    path('google-auth/', GoogleLoginView.as_view(), name='google_auth'),
    # path('facebook-auth/', FacebookLoginView.as_view(), name='facebook_auth'),
    # path('apple-auth/', AppleFirebaseLoginView.as_view(), name='apple_firebase_auth'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]