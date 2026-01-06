from rest_framework import serializers
from ..models import PhoneRequestLog

class PhoneRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneRequestLog
        fields = ['id', 'ip_address', 'file_requested', 'status_code', 'timestamp']
