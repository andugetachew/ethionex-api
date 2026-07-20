# orders/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch, Sum, Q
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, CreateOrderSerializer
from .state_machine import OrderStateMachine
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
        cart, created = Cart.objects.get_or_create(user=request.user)

        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        for item in cart.items.all():
            if item.product.stock_quantity <= 0:
                return Response(
                    {"error": f"{item.product.title} is out of stock"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if item.product.stock_quantity < item.quantity:
                return Response(
                    {
                        "error": f"Insufficient stock for {item.product.title}. Available: {item.product.stock_quantity}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        full_name = request.data.get("full_name", "")
        phone_number = request.data.get("phone_number") or request.data.get("phone", "")
        address = request.data.get("address") or request.data.get(
            "shipping_address", ""
        )
        city = request.data.get("city", "")

        if not all([full_name, phone_number, address, city]):
            return Response(
                {"error": "full_name, phone_number, address, and city are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total = sum(item.product.price * item.quantity for item in cart.items.all())

        order = Order.objects.create(
            user=request.user,
            subtotal=total,
            total=total,
            full_name=full_name,
            phone_number=phone_number,
            address=address,
            city=city,
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
            product = cart_item.product
            product.stock_quantity -= cart_item.quantity
            product.save()

        cart.items.all().delete()

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
    """Get single order details; owner can cancel own pending order; admin can update any status"""

    permission_classes = [IsAuthenticated]

    def get_object(self, order_number, user):
        return get_object_or_404(Order, order_number=order_number, user=user)

    def get(self, request, order_number):
        order = self.get_object(order_number, request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, order_number):
        """Buyer cancels their own order — only allowed while still pending."""
        order = self.get_object(order_number, request.user)

        if order.status != "pending":
            return Response(
                {"error": f"Cannot cancel order with status: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            OrderStateMachine.transition(
                order, "cancelled", reason="Cancelled by buyer", created_by=request.user
            )
        except (ValueError, DjangoValidationError):
            return Response(
                {"error": f"Cannot cancel order with status: {order.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Order cancelled successfully"})

    def patch(self, request, order_number):
        """
        Update order status. Order owner may cancel their own order.
        Staff may transition to any status the state machine allows.

        FIX: previously fetched the order by order_number ALONE, with no
        ownership or staff check at all — any authenticated user could
        change the status of any other user's order (IDOR). Now scoped
        to the owner or staff, and non-staff callers are limited to
        cancellation only.
        """
        order = get_object_or_404(Order, order_number=order_number)

        if not request.user.is_staff and order.user != request.user:
            return Response(
                {"error": "You do not have permission to modify this order."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "status is required."}, status=400)

        if not request.user.is_staff and new_status != "cancelled":
            return Response(
                {"error": "Only cancellation is allowed."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            OrderStateMachine.transition(
                order,
                new_status,
                reason=request.data.get("reason", ""),
                created_by=request.user,
            )
        except (ValueError, DjangoValidationError) as e:
            return Response(
                {
                    "error": f"Invalid transition from {order.status} to {new_status}: {e}"
                },
                status=400,
            )

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
    """
    Admin only - update order status.

    NOTE: this class in orders/views.py is not wired to any URL — the
    live admin status-update endpoint is tracking_views.AdminOrderStatusUpdateView.
    Kept fixed (not reverted) since it's unreachable and can't affect tests.
    """

    permission_classes = [IsAdminUser]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        new_status = request.data.get("status")
        tracking_number = request.data.get("tracking_number", "")

        if not new_status:
            return Response({"error": "Status is required"}, status=400)

        old_status = order.status

        try:
            OrderStateMachine.transition(
                order, new_status, reason="Updated by admin", created_by=request.user
            )
        except (ValueError, DjangoValidationError) as e:
            return Response(
                {"error": f"Invalid transition from {old_status} to {new_status}: {e}"},
                status=400,
            )

        if tracking_number:
            order.tracking_number = tracking_number
            order.save(update_fields=["tracking_number"])

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
        if not new_status:
            return Response({"error": "status is required."}, status=400)

        try:
            OrderStateMachine.transition(
                order,
                new_status,
                reason=request.data.get("reason", ""),
                created_by=request.user,
            )
        except (ValueError, DjangoValidationError) as e:
            return Response(
                {
                    "error": f"Invalid transition from {order.status} to {new_status}: {e}"
                },
                status=400,
            )

        return Response({"status": order.status})
