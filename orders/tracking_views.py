from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Order
from .tracking_serializers import OrderTrackingSerializer, OrderStatusUpdateSerializer


class TrackOrderView(APIView):
    """Public order tracking by order number or tracking number"""

    permission_classes = []

    def get(self, request):
        order_number = request.query_params.get("order_number")
        tracking_number = request.query_params.get("tracking_number")

        if order_number:
            order = get_object_or_404(Order, order_number=order_number)
        elif tracking_number:
            order = get_object_or_404(Order, tracking_number=tracking_number)
        else:
            return Response(
                {"error": "Please provide order_number or tracking_number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OrderTrackingSerializer(order)
        return Response(serializer.data)


class MyOrderTrackingView(APIView):
    """Get tracking info for authenticated user's order"""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        serializer = OrderTrackingSerializer(order)
        return Response(serializer.data)


class AdminOrderStatusUpdateView(APIView):
    """Admin only - update order status and tracking info"""

    permission_classes = [IsAdminUser]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderStatusUpdateSerializer(data=request.data)

        if serializer.is_valid():
            new_status = serializer.validated_data["status"]
            tracking_number = serializer.validated_data.get("tracking_number", "")
            note = serializer.validated_data.get("note", "")

            # Update tracking number if provided
            if tracking_number:
                order.tracking_number = tracking_number

            # Update status with history
            old_status = order.status
            order.update_status(new_status, note)

            # Send email notification on status change
            if old_status != new_status:
                self._send_status_notification(order, old_status, new_status)

            return Response(
                {
                    "message": f"Order status updated to {new_status}",
                    "order_id": order.id,
                    "new_status": new_status,
                    "tracking_number": order.tracking_number,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _send_status_notification(self, order, old_status, new_status):
        """Send email notification to customer"""
        try:
            subject = f"Order {order.order_number} Status Update"
            message = f"""
            Dear {order.user.username},
            
            Your order #{order.order_number} status has been updated:
            
            Previous Status: {old_status}
            New Status: {new_status}
            
            """
            if order.tracking_number:
                message += f"Tracking Number: {order.tracking_number}\n"

            if new_status == "shipped":
                message += "\nYour order has been shipped and is on its way!"
            elif new_status == "delivered":
                message += (
                    "\nYour order has been delivered. Thank you for shopping with us!"
                )
            elif new_status == "cancelled":
                message += (
                    "\nYour order has been cancelled. Contact support for questions."
                )

            message += "\n\nThank you for shopping with EthioNex!"

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error: {e}")


class AdminBulkOrderUpdateView(APIView):
    """Admin only - bulk update multiple orders"""

    permission_classes = [IsAdminUser]

    def post(self, request):
        order_ids = request.data.get("order_ids", [])
        new_status = request.data.get("status")
        tracking_numbers = request.data.get("tracking_numbers", {})

        if not order_ids or not new_status:
            return Response(
                {"error": "order_ids and status are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_orders = []
        for order_id in order_ids:
            try:
                order = Order.objects.get(id=order_id)
                order.update_status(new_status, f"Bulk update to {new_status}")

                if order_id in tracking_numbers:
                    order.tracking_number = tracking_numbers[order_id]
                    order.save()

                updated_orders.append(order_id)
            except Order.DoesNotExist:
                continue

        return Response(
            {
                "message": f"Updated {len(updated_orders)} orders",
                "updated_orders": updated_orders,
            }
        )
