from rest_framework import serializers

from .models import FAQ, BusinessSettings, LegalDocument, ServiceContent, Testimonial


class BusinessSettingsPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessSettings
        fields = (
            "business_name",
            "tagline",
            "phone",
            "whatsapp_phone",
            "email",
            "support_hours",
            "address",
            "city",
            "postal_code",
            "country_code",
            "currency",
            "minimum_lead_hours",
            "maximum_booking_days",
            "quote_valid_minutes",
            "booking_enabled",
        )


class ServiceContentPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceContent
        fields = ("slug", "title", "summary", "description", "icon")


class FAQPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ("public_id", "question", "answer")


class TestimonialPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ("public_id", "author_name", "author_context", "quote", "rating")


class LegalDocumentPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocument
        fields = ("kind", "version", "title", "body", "effective_at")


class PublicContentSerializer(serializers.Serializer):
    settings = BusinessSettingsPublicSerializer()
    services = ServiceContentPublicSerializer(many=True)
    faqs = FAQPublicSerializer(many=True)
    testimonials = TestimonialPublicSerializer(many=True)
    legal_documents = LegalDocumentPublicSerializer(many=True)
