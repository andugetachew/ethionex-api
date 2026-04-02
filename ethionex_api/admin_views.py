from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from products.models import Product, Category, Review
from orders.models import Order, OrderItem


class AdminDashboardView(APIView):
    """Admin dashboard analytics"""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Get date ranges
        today = timezone.now()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # User statistics
        total_users = User.objects.count()
        total_sellers = User.objects.filter(is_seller=True).count()
        new_users_week = User.objects.filter(date_joined__gte=week_ago).count()

        # Product statistics
        total_products = Product.objects.count()
        total_categories = Category.objects.count()
        out_of_stock = Product.objects.filter(quantity=0).count()
        low_stock = Product.objects.filter(quantity__lt=5, quantity__gt=0).count()

        # Order statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status="pending").count()
        completed_orders = Order.objects.filter(status="delivered").count()
        total_revenue = (
            Order.objects.filter(status="delivered").aggregate(total=Sum("total"))[
                "total"
            ]
            or 0
        )

        # Weekly revenue
        weekly_revenue = (
            Order.objects.filter(
                created_at__gte=week_ago, status="delivered"
            ).aggregate(total=Sum("total"))["total"]
            or 0
        )

        # Monthly revenue
        monthly_revenue = (
            Order.objects.filter(
                created_at__gte=month_ago, status="delivered"
            ).aggregate(total=Sum("total"))["total"]
            or 0
        )

        # Review statistics
        total_reviews = Review.objects.count()
        average_rating = Review.objects.aggregate(Avg("rating"))["rating__avg"] or 0

        # Recent orders (last 10)
        recent_orders = Order.objects.order_by("-created_at")[:10]
        recent_orders_data = []
        for order in recent_orders:
            recent_orders_data.append(
                {
                    "order_number": order.order_number,
                    "customer": order.user.username,
                    "total": float(order.total),
                    "status": order.status,
                    "date": order.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        # Top selling products
        top_products = (
            OrderItem.objects.values("product__id", "product__name", "product__price")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:10]
        )

        top_products_data = []
        for item in top_products:
            top_products_data.append(
                {
                    "id": item["product__id"],
                    "name": item["product__name"],
                    "total_sold": item["total_sold"],
                    "revenue": float(item["product__price"]) * item["total_sold"],
                }
            )

        return Response(
            {
                "users": {
                    "total": total_users,
                    "sellers": total_sellers,
                    "new_this_week": new_users_week,
                },
                "products": {
                    "total": total_products,
                    "categories": total_categories,
                    "out_of_stock": out_of_stock,
                    "low_stock": low_stock,
                },
                "orders": {
                    "total": total_orders,
                    "pending": pending_orders,
                    "completed": completed_orders,
                    "total_revenue": float(total_revenue),
                    "weekly_revenue": float(weekly_revenue),
                    "monthly_revenue": float(monthly_revenue),
                },
                "reviews": {
                    "total": total_reviews,
                    "average_rating": round(average_rating, 1),
                },
                "recent_orders": recent_orders_data,
                "top_products": top_products_data,
            }
        )
