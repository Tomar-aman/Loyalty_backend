from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.CustomAdminLoginView.as_view(), name='login'),
    path('dashboard/', views.CustomAdminDashboardView.as_view(), name='dashboard'),
    path('logout/', views.CustomAdminLogoutView.as_view(), name='logout'),
    path('profile/', views.AdminProfileView.as_view(), name='profile'),
    path('reset-password/<str:uidb64>/<str:token>/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('update-smtp-settings/', views.UpdateSMTPSettingsView.as_view(), name='update_smtp'),
    
    # Notifications Management
    path('notifications/', views.ManageNotificationsView.as_view(), name='manage_notifications'),
    
    # API Settings Management
    path('api-settings/', views.ManageAPISettingsView.as_view(), name='manage_api_settings'),
    # path('chatgpt-settings/<int:api_id>/edit/', views.UpdateChatGPTSettingsView.as_view(), name='update_chatgpt'),
    # path('chatgpt-settings/<int:api_id>/toggle/', views.ToggleChatGPTStatusView.as_view(), name='toggle_chatgpt'),
    path('stripe-settings/<int:stripe_id>/edit/', views.UpdateStripeSettingsView.as_view(), name='update_stripe'),
    path('google-maps-settings/<int:maps_id>/edit/', views.UpdateGoogleMapsSettingsView.as_view(), name='update_google_maps'),
    path('firebase-settings/<int:notification_id>/edit/', views.UpdateFirebaseSettingsView.as_view(), name='update_firebase'),
    
    # User Management Routes
    path('users/', views.UserListView.as_view(), name='manage_users'),
    path('users/<int:user_id>/toggle/', views.UserToggleStatusView.as_view(), name='user_toggle'),
    path('users/<int:user_id>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/edit/', views.UserEditView.as_view(), name='user_edit'),
    
    # Admin Management Routes
    path('admins/', views.AdminListView.as_view(), name='manage_admins'),
    path('admins/add/', views.AdminAddView.as_view(), name='admin_add'),
    path('admins/<int:admin_id>/edit/', views.AdminEditView.as_view(), name='admin_edit'),
    path('admins/<int:admin_id>/delete/', views.AdminDeleteView.as_view(), name='admin_delete'),
    path('admins/<int:admin_id>/reset-password/', views.AdminPasswordReset.as_view(), name='admin_reset_password'),
    path('admins/<int:admin_id>/toggle/', views.AdminToggleStatusView.as_view(), name='admin_toggle'),

    # Cities management
    path('cities/', views.CityListView.as_view(), name='manage_cities'),
    path('cities/add/', views.CityAddView.as_view(), name='city_add'),
    path('cities/<int:city_id>/edit/', views.CityEditView.as_view(), name='city_edit'),
    path('cities/<int:city_id>/delete/', views.CityDeleteView.as_view(), name='city_delete'),
        
    # Card Management Routes
    path('cards/', views.CardListView.as_view(), name='manage_cards'),
    path('cards/add/', views.CardAddView.as_view(), name='card_add'),
    path('cards/<int:card_id>/edit/', views.CardEditView.as_view(), name='card_edit'),
    path('cards/<int:card_id>/delete/', views.CardDeleteView.as_view(), name='card_delete'),
    path('cards/<int:card_id>/toggle/', views.CardToggleStatusView.as_view(), name='card_toggle'),
    
    # News Management Routes
    path('news/', views.NewsListView.as_view(), name='manage_news'),
    path('news/add/', views.NewsAddView.as_view(), name='news_add'),
    path('news/<int:news_id>/edit/', views.NewsEditView.as_view(), name='news_edit'),
    path('news/<int:news_id>/delete/', views.NewsDeleteView.as_view(), name='news_delete'),
    
    # Business Category Routes
    path('categories/', views.CategoryListView.as_view(), name='manage_categories'),
    path('categories/add/', views.CategoryAddView.as_view(), name='category_add'),
    path('categories/<int:category_id>/edit/', views.CategoryEditView.as_view(), name='category_edit'),
    path('categories/<int:category_id>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/<int:category_id>/toggle/', views.CategoryToggleStatusView.as_view(), name='category_toggle'),

     # Business Management Routes
    path('businesses/', views.BusinessListView.as_view(), name='manage_businesses'),
    path('businesses/add/', views.BusinessAddView.as_view(), name='business_add'),
    path('businesses/<int:business_id>/edit/', views.BusinessEditView.as_view(), name='business_edit'),
    path('businesses/<int:business_id>/delete/', views.BusinessDeleteView.as_view(), name='business_delete'),
    path('businesses/<int:business_id>/toggle/', views.BusinessToggleStatusView.as_view(), name='business_toggle'),

    # Business Offer Management Routes
    path('offers/', views.OfferListView.as_view(), name='manage_offers'),
    path('offers/add/', views.OfferAddView.as_view(), name='offer_add'),
    path('offers/<int:offer_id>/edit/', views.OfferEditView.as_view(), name='offer_edit'),
    path('offers/<int:offer_id>/delete/', views.OfferDeleteView.as_view(), name='offer_delete'),
    path('offers/<int:offer_id>/toggle/', views.OfferToggleStatusView.as_view(), name='offer_toggle'),

    # User Card Management
    path('user-cards/', views.UserCardAdminListView.as_view(), name='manage_user_cards'),
    path('user-cards/add/', views.UserCardAdminAddView.as_view(), name='user_card_add'),
    path('user-cards/<int:user_card_id>/edit/', views.UserCardAdminEditView.as_view(), name='user_card_edit'),
    path('user-cards/<int:user_card_id>/delete/', views.UserCardAdminDeleteView.as_view(), name='user_card_delete'),
    path('user-cards/<int:user_card_id>/toggle/', views.UserCardAdminToggleStatusView.as_view(), name='user_card_toggle'),
]