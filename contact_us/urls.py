from django.urls import path
from .views import SupportListView, FAQListView, ContactUsMessageCreateView, SubscriberEmailCreateView, LandingPageContentView, SocialMediaLinkView, APPDownloadLinkView

urlpatterns = [
    path('support/', SupportListView.as_view(), name='support-contact'),
    path('faqs/', FAQListView.as_view(), name='faq-list'),
    path('social-media-links/', SocialMediaLinkView.as_view(), name='social-media-links'),
    path('app-download-links/', APPDownloadLinkView.as_view(), name='app-download-links'),
    path('contact-us/', ContactUsMessageCreateView.as_view(), name='contact-us-message-create'),
    path('subscribe/', SubscriberEmailCreateView.as_view(), name='subscriber-email-create'),
    path('landing-page-content/', LandingPageContentView.as_view(), name='landing-page-content'),
]