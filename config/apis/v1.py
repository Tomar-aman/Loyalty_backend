
from django.urls import include, path

app_name = "v1"

urlpatterns = [
    path("user/", include("users.urls")),
    path("news/", include("news.urls")),
    path("card/", include("card.urls")),
    path("business/", include("business.urls")),
]
