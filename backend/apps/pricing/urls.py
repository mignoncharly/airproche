from django.urls import path

from .views import CoverageView, QuoteCreateView, QuoteDetailView

app_name = "pricing"

urlpatterns = [
    path("coverage/", CoverageView.as_view(), name="coverage"),
    path("quotes/", QuoteCreateView.as_view(), name="quote-create"),
    path("quotes/<uuid:public_id>/", QuoteDetailView.as_view(), name="quote-detail"),
]
