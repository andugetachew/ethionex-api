import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import permissions
from django.db import models
from orders.models import Order, OrderItem
from products.models import Product
from datetime import datetime


class ExportOrdersCSV(APIView):
    """Export orders to CSV file"""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="orders_{datetime.now().strftime("%Y%m%d")}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(
            ["Order Number", "Customer", "Date", "Status", "Total", "Items Count"]
        )

        orders = Order.objects.all().order_by("-created_at")
        for order in orders:
            writer.writerow(
                [
                    order.order_number,
                    order.user.username,
                    order.created_at.strftime("%Y-%m-%d"),
                    order.status,
                    float(order.total),
                    order.items.count(),
                ]
            )

        return response


class ExportProductsCSV(APIView):
    """Export products to CSV file"""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="products_{datetime.now().strftime("%Y%m%d")}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(["ID", "Name", "Price", "Stock", "Sold Count", "Rating"])

        products = Product.objects.all()
        for product in products:
            sold_count = (
                OrderItem.objects.filter(product=product).aggregate(
                    total=models.Sum("quantity")
                )["total"]
                or 0
            )

            writer.writerow(
                [
                    product.id,
                    product.name,
                    float(product.price),
                    product.quantity,
                    sold_count,
                    product.average_rating,
                ]
            )

        return response
