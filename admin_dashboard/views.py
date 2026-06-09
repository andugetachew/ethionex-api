from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import generics, status
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order, OrderItem
from .serializers import (
    AdminStatsSerializer,
    UserListSerializer,
    UserUpdateSerializer,
    SalesReportSerializer,
    TopProductSerializer,
    TopSellerSerializer,
)

User = get_user_model()


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # User stats
        total_users = User.objects.count()
        total_sellers = User.objects.filter(groups__name="seller").count()

        # Product stats
        total_products = Product.objects.count()
        total_categories = Category.objects.count()

        # Order stats
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status="pending").count()
        completed_orders = Order.objects.filter(status="completed").count()
        cancelled_orders = Order.objects.filter(status="cancelled").count()

        # Revenue
        total_revenue = (
            Order.objects.filter(status__in=["completed", "delivered"]).aggregate(
                total=Sum("total")
            )["total"]
            or 0
        )

        stats = {
            "total_users": total_users,
            "total_sellers": total_sellers,
            "total_products": total_products,
            "total_categories": total_categories,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
        }

        serializer = AdminStatsSerializer(stats)
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserListSerializer

    def get_queryset(self):
        queryset = User.objects.all()

        # Filter by role
        role = self.request.query_params.get("role")
        if role == "seller":
            queryset = queryset.filter(groups__name="seller")
        elif role == "buyer":
            queryset = queryset.exclude(groups__name="seller")

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Search
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | Q(email__icontains=search)
            )

        return queryset.order_by("-date_joined")


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({"message": "User deactivated"})


class BlockUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_active = False
            user.save()
            return Response({"message": f"User {user.username} blocked"})
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class UnblockUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()
            return Response({"message": f"User {user.username} unblocked"})
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SalesReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        period = request.query_params.get("period", "month")

        end_date = timezone.now().date()
        if period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")

        if isinstance(start_date, str):
            from datetime import datetime

            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status__in=["completed", "delivered"],
        )

        # Daily breakdown
        report = []
        current_date = start_date
        while current_date <= end_date:
            day_orders = orders.filter(created_at__date=current_date)
            report.append(
                {
                    "date": current_date,
                    "total_orders": day_orders.count(),
                    "total_revenue": day_orders.aggregate(total=Sum("total"))["total"]
                    or 0,
                }
            )
            current_date += timedelta(days=1)

        serializer = SalesReportSerializer(report, many=True)
        return Response(serializer.data)


class TopProductsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))

        top_products = (
            Product.objects.annotate(
                total_sold=Sum("orderitem__quantity"),
                total_revenue=Sum(
                    "orderitem__price",
                    filter=Q(orderitem__order__status__in=["completed", "delivered"]),
                ),
            )
            .filter(total_sold__gt=0)
            .order_by("-total_sold")[:limit]
        )

        serializer = TopProductSerializer(top_products, many=True)
        return Response(serializer.data)


class TopSellersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))

        from django.db.models import Sum, Count

        sellers = (
            User.objects.filter(groups__name="seller")
            .annotate(
                total_products=Count("products"),
                total_sales=Count("products__orderitem"),
                total_revenue=Sum(
                    "products__orderitem__price",
                    filter=Q(
                        products__orderitem__order__status__in=[
                            "completed",
                            "delivered",
                        ]
                    ),
                ),
            )
            .order_by("-total_revenue")[:limit]
        )

        result = []
        for seller in sellers:
            result.append(
                {
                    "id": seller.id,
                    "username": seller.username,
                    "store_name": (
                        seller.seller.store_name
                        if hasattr(seller, "seller")
                        else seller.username
                    ),
                    "total_products": seller.total_products,
                    "total_sales": seller.total_sales,
                    "total_revenue": seller.total_revenue or 0,
                }
            )

        serializer = TopSellerSerializer(result, many=True)
        return Response(serializer.data)
