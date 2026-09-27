from rest_framework import serializers

from .models import Notification


class NotificationSerializer(
    serializers.ModelSerializer
):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification

        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "data",
            "read_at",
            "is_read",
            "created_at",
        ]

        read_only_fields = fields

    def get_is_read(self, obj):
        return obj.read_at is not None