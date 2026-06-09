from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "model_name", "object_id", "created_at"]
    list_filter = ["action", "model_name", "created_at"]
    search_fields = ["user__username", "object_id"]
    readonly_fields = [
        "user",
        "action",
        "model_name",
        "object_id",
        "old_data",
        "new_data",
        "ip_address",
        "user_agent",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
