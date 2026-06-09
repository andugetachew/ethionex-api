from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from products.models import Product
from products.serializers import ProductSerializer
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from .serializers import SellerStatsSerializer
from ethionex_api.permissions import IsSeller
from ethionex_api.throttles import SellerDashboardRateThrottle


class SellerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsSeller]
    throttle_classes = [SellerDashboardRateThrottle]

    def get(self, request):
        user = request.user

        products = Product.objects.filter(seller=user)
        total_products = products.count()
        low_stock_count = products.filter(stock_quantity__lte=5).count()

        orders = Order.objects.filter(items__product__seller=user).distinct()
        completed_orders = orders.filter(status__in=["paid", "delivered"])

        total_orders = orders.count()
        total_revenue = completed_orders.aggregate(total=Sum("total"))["total"] or 0

        total_items_sold = (
            OrderItem.objects.filter(product__seller=user).aggregate(
                total=Sum("quantity")
            )["total"]
            or 0
        )

        average_order_value = total_revenue / total_orders if total_orders > 0 else 0

        recent_orders = orders.order_by("-created_at")[:10]

        top_products = products.annotate(
            total_sold=Sum("orderitem__quantity")
        ).order_by("-total_sold")[:5]

        monthly_sales = {}
        today = timezone.now().date()
        for i in range(6):
            month_start = today.replace(day=1) - timedelta(days=30 * i)
            month_start = month_start.replace(day=1)
            next_month = month_start.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)

            month_orders = completed_orders.filter(
                created_at__date__gte=month_start, created_at__date__lte=month_end
            )
            monthly_sales[month_start.strftime("%B %Y")] = (
                month_orders.aggregate(total=Sum("total"))["total"] or 0
            )

        stats = {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_items_sold": total_items_sold,
            "average_order_value": average_order_value,
            "low_stock_count": low_stock_count,
            "recent_orders": OrderSerializer(recent_orders, many=True).data,
            "top_products": ProductSerializer(top_products, many=True).data,
            "monthly_sales": monthly_sales,
        }

        return Response(stats)
