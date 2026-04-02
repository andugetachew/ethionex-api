from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from products.models import Product


class SellerDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_seller:
            return Response({"error": "Not a seller"}, status=403)

        total_products = Product.objects.filter(seller=request.user).count()

        return Response(
            {"total_products": total_products, "message": "Dashboard working!"}
        )


class SellerOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_seller:
            return Response({"error": "Not a seller"}, status=403)

        return Response({"orders": []})


class UpdateOrderStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, order_number):
        return Response({"message": "Status updated"})


class SellerProductsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(seller=request.user)
        data = [{"id": p.id, "name": p.name, "price": str(p.price)} for p in products]
        return Response(data)


class TopSellingProductsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response([])
