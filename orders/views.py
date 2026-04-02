from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer
from cart.models import Cart
from ethionex_api.email_utils import send_order_confirmation


class OrderListCreateView(APIView):
    """List user's orders or create a new order from cart"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all orders for the logged-in user"""
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create an order from current cart"""
        serializer = CreateOrderSerializer(data=request.data)

        if serializer.is_valid():
            # Get user's cart
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                return Response(
                    {"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Check if cart has items
            if not cart.items.exists():
                return Response(
                    {"error": "Cannot create order from empty cart"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Calculate totals
            subtotal = cart.total_price
            delivery_fee = serializer.validated_data.get("delivery_fee", 0)
            total = subtotal + delivery_fee

            # Create order
            order = Order.objects.create(
                user=request.user,
                payment_method=serializer.validated_data["payment_method"],
                full_name=serializer.validated_data["full_name"],
                phone_number=serializer.validated_data["phone_number"],
                address=serializer.validated_data["address"],
                city=serializer.validated_data["city"],
                sub_city=serializer.validated_data.get("sub_city", ""),
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=total,
                notes=serializer.validated_data.get("notes", ""),
            )

            # Create order items from cart items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                )
                send_order_confirmation(order)

            # Clear the cart after order is created
            cart.items.all().delete()
            send_order_confirmation(order)

            # Return the created order
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailView(APIView):
    """Get, update or cancel a specific order"""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, order_id, user):
        return get_object_or_404(Order, id=order_id, user=user)

    def get(self, request, order_id):
        order = self.get_object(order_id, request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, order_id):
        """Cancel an order (only if pending)"""
        order = self.get_object(order_id, request.user)

        if order.status == "pending":
            order.status = "cancelled"
            order.save()
            serializer = OrderSerializer(order)
            return Response(
                {"message": "Order cancelled successfully", "order": serializer.data}
            )
        else:
            return Response(
                {"error": f"Cannot cancel order with status: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
