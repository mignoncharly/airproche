from django.urls import path

from .views import PublicContentView

app_name = "content"

urlpatterns = [path("content/", PublicContentView.as_view(), name="public-content")]
