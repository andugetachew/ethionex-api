from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    """Allow access only to sellers"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(
            request.user, "is_seller", False
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission to only allow owners to edit"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            getattr(obj, "seller", None) == request.user
            or getattr(obj, "user", None) == request.user
        )


class CanModifyOrder(permissions.BasePermission):
    """Only buyer, seller, or admin can modify order"""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if obj.user == request.user:
            return True
        # Seller can update their own product orders
        if hasattr(obj, "product") and obj.product.seller == request.user:
            return True
        return False
