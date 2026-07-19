# orders/seller_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework import permissions, status
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError

from products.models import Product
from products.serializers import ProductSerializer
from ethionex_api.permissions import IsSeller

from .models import Order, OrderItem
from .serializers import OrderSerializer
from .state_machine import OrderStateMachine


class SellerDashboardView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get(self, request):
        total_products = Product.objects.filter(seller=request.user).count()
        return Response(
            {"total_products": total_products, "message": "Dashboard working!"}
        )


class SellerOrdersView(ListAPIView):

    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(
            items__product__seller=self.request.user
        ).distinct().order_by("-created_at")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class UpdateOrderStatusView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def put(self, request, order_number):
        order = get_object_or_404(
            Order.objects.filter(items__product__seller=request.user).distinct(),
            order_number=order_number,
        )

        new_status = request.data.get("status")
        if not new_status:
            return Response(
                {"error": "status is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "")

        try:
            OrderStateMachine.transition(
                order, new_status, reason=reason, created_by=request.user
            )
        except (ValueError, DjangoValidationError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Status updated",
                "order_number": order.order_number,
                "status": order.status,
            }
        )


class SellerProductsView(ListAPIView):
    """
    GET /api/v1/seller/products/

    All products belonging to the requesting seller.
    """

    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user).order_by("-id")


class TopSellingProductsView(APIView):

    permission_classes = [permissions.IsAuthenticated, IsSeller]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 10))
        except (TypeError, ValueError):
            return Response(
                {"error": "limit must be a whole number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limit = max(1, min(limit, 100))  

        top_products = (
            Product.objects.filter(seller=request.user)
            .annotate(total_sold=Sum("orderitem__quantity"))
            .filter(total_sold__gt=0)
            .order_by("-total_sold")[:limit]
        )

        data = ProductSerializer(top_products, many=True).data
        return Response(data)