from .models import AuditLog


class AuditService:
    """Service for creating audit logs"""

    @staticmethod
    def log(
        user, action, model_name, object_id, old_data=None, new_data=None, request=None
    ):
        """Create an audit log entry"""
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id),
            old_data=old_data or {},
            new_data=new_data or {},
            ip_address=getattr(request, "audit_ip", None) if request else None,
            user_agent=getattr(request, "audit_user_agent", "") if request else "",
        )

    @staticmethod
    def log_order_status_change(order, old_status, new_status, request=None):
        """Log order status change"""
        AuditService.log(
            user=getattr(order, "user", None),
            action="STATUS_CHANGE",
            model_name="Order",
            object_id=order.id,
            old_data={"status": old_status},
            new_data={"status": new_status},
            request=request,
        )

    @staticmethod
    def log_product_update(product, old_data, new_data, request=None):
        """Log product update"""
        AuditService.log(
            user=getattr(request, "user", None),
            action="UPDATE",
            model_name="Product",
            object_id=product.id,
            old_data=old_data,
            new_data=new_data,
            request=request,
        )

    @staticmethod
    def get_user_audit_logs(user_id, limit=50):
        """Get audit logs for a specific user"""
        return AuditLog.objects.filter(user_id=user_id)[:limit]

    @staticmethod
    def get_model_audit_logs(model_name, object_id, limit=50):
        """Get audit logs for a specific model instance"""
        return AuditLog.objects.filter(model_name=model_name, object_id=str(object_id))[
            :limit
        ]
