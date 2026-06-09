from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.db.models import Prefetch, Sum, Q
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, CreateOrderSerializer
from cart.models import Cart, CartItem
from notifications.email_service import EmailService
from django.contrib.auth import get_user_model
from ethionex_api.throttles import OrderRateThrottle
from ethionex_api.pagination import StandardPagination, CursorPagination

User = get_user_model()


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrderRateThrottle]

    def post(self, request):
        print("=== OrderCreateView called! ===")
        cart, created = Cart.objects.get_or_create(user=request.user)

        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Stock validation
        for item in cart.items.all():
            if item.product.stock_quantity < item.quantity:
                return Response(
                    {
                        "error": f"Insufficient stock for {item.product.title}. Available: {item.product.stock_quantity}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if item.product.stock_quantity == 0:
                return Response(
                    {"error": f"{item.product.title} is out of stock"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        order_number = get_random_string(12).upper()
        total = sum(item.product.price * item.quantity for item in cart.items.all())

        order = Order.objects.create(
            user=request.user,
            order_number=order_number,
            total=total,
            shipping_address=request.data.get("shipping_address", ""),
            phone=request.data.get("phone", ""),
            notes=request.data.get("notes", ""),
            status="pending",
        )

        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
            )
            # Decrease stock
            product = cart_item.product
            product.stock_quantity -= cart_item.quantity
            product.save()

        cart.items.all().delete()

        # Send email using EmailService (only once)
        try:
            EmailService.send_order_confirmation(order)
        except Exception as e:
            print(f"Email error in OrderCreateView: {e}")

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    """List user's orders"""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related(
                Prefetch("items", queryset=OrderItem.objects.select_related("product"))
            )
            .order_by("-created_at")
        )


class OrderDetailView(APIView):
    """Get single order details and update status"""

    permission_classes = [IsAuthenticated]

    def get_object(self, order_number, user):
        return get_object_or_404(Order, order_number=order_number, user=user)

    def get(self, request, order_number):
        order = self.get_object(order_number, request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, order_number):
        order = self.get_object(order_number, request.user)

        if order.status == "pending":
            # First, restore stock
            for item in order.items.all():
                product = item.product
                product.stock_quantity += item.quantity
                product.save()

            # Then, cancel the order
            order.status = "cancelled"
            order.save()

            return Response({"message": "Order cancelled successfully"})
        else:
            return Response(
                {"error": f"Cannot cancel order with status: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def patch(self, request, order_number):
        """Update order status (for admin)"""
        order = get_object_or_404(Order, order_number=order_number)
        new_status = request.data.get("status")

        valid_transitions = {
            "pending": ["paid", "cancelled"],
            "paid": ["processing", "cancelled"],
            "processing": ["shipped", "cancelled"],
            "shipped": ["delivered", "cancelled"],
        }

        if new_status not in valid_transitions.get(order.status, []):
            return Response(
                {"error": f"Invalid transition from {order.status} to {new_status}"},
                status=400,
            )

        # If cancelling, restore stock
        if new_status == "cancelled" and order.status == "pending":
            for item in order.items.all():
                product = item.product
                product.stock_quantity += item.quantity
                product.save()

        order.status = new_status
        order.save()
        return Response({"status": order.status, "order_number": order.order_number})


class AdminOrderListView(generics.ListAPIView):
    """Admin: List all orders"""

    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Order.objects.all().order_by("-created_at")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class AdminOrderDetailView(generics.RetrieveUpdateAPIView):
    """Admin: Update order status"""

    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all()
    lookup_field = "id"


class AdminOrderStatusUpdateView(APIView):
    """Admin only - update order status"""

    permission_classes = [IsAdminUser]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        new_status = request.data.get("status")
        tracking_number = request.data.get("tracking_number", "")

        if not new_status:
            return Response({"error": "Status is required"}, status=400)

        old_status = order.status
        order.status = new_status
        if tracking_number:
            order.tracking_number = tracking_number
        order.save()

        # Send email notification
        try:
            EmailService.send_order_status_update(order, old_status, new_status)
        except Exception as e:
            print(f"Notification error: {e}")

        return Response(
            {
                "message": f"Order status updated from {old_status} to {new_status}",
                "order_id": order.id,
                "status": new_status,
                "tracking_number": tracking_number,
            }
        )


class OrderFeedView(generics.ListAPIView):
    """For infinite scroll (mobile app)"""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CursorPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


class OrderListCreateView(APIView):
    """Alternative order creation with address fields"""

    permission_classes = [IsAuthenticated]
    throttle_classes = [OrderRateThrottle]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        print("=== OrderCreateView called! ===")
        serializer = CreateOrderSerializer(data=request.data)

        if serializer.is_valid():
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                return Response(
                    {"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST
                )

            if not cart.items.exists():
                return Response(
                    {"error": "Cannot create order from empty cart"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Stock validation
            for cart_item in cart.items.all():
                if cart_item.quantity > cart_item.product.stock_quantity:
                    return Response(
                        {
                            "error": f"Insufficient stock for {cart_item.product.title}. Available: {cart_item.product.stock_quantity}"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if cart_item.product.stock_quantity <= 0:
                    return Response(
                        {"error": f"{cart_item.product.title} is out of stock"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            subtotal = cart.subtotal if hasattr(cart, "subtotal") else cart.total_price
            delivery_fee = serializer.validated_data.get("delivery_fee", 0)
            total = subtotal + delivery_fee

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

            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                )
                product = cart_item.product
                product.stock_quantity -= cart_item.quantity
                product.save()

            cart.items.all().delete()

            # Send email using EmailService
            try:
                EmailService.send_order_confirmation(order)
            except Exception as e:
                print(f"Email error in OrderListCreateView: {e}")

            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, order_id=None, order_number=None):
        if order_id:
            order = get_object_or_404(Order, id=order_id)
        elif order_number:
            order = get_object_or_404(Order, order_number=order_number)
        else:
            return Response({"error": "Order identifier required"}, status=400)

        new_status = request.data.get("status")

        valid_transitions = {
            "pending": ["paid", "cancelled"],
            "paid": ["processing", "cancelled"],
            "processing": ["shipped", "cancelled"],
            "shipped": ["delivered", "cancelled"],
        }

        if new_status not in valid_transitions.get(order.status, []):
            return Response(
                {"error": f"Invalid transition from {order.status} to {new_status}"},
                status=400,
            )

        order.status = new_status
        order.save()
        return Response({"status": order.status})
