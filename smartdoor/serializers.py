# smartdoor/serializers.py
from rest_framework import serializers
from .models import SpecialGuest

class SpecialGuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialGuest
        fields = ['image_id', 'pin_code', 'name', 'phone_number', 'additional_details']
