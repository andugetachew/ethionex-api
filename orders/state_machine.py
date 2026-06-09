# orders/state_machine.py
from enum import Enum
from django.core.exceptions import ValidationError
from django.utils import timezone  # <-- ADD THIS
from .services import InventoryService

class OrderState(Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderStateMachine:
    VALID_TRANSITIONS = {
        OrderState.PENDING: [OrderState.PAID, OrderState.CANCELLED],
        OrderState.PAID: [OrderState.PROCESSING, OrderState.CANCELLED],
        OrderState.PROCESSING: [OrderState.SHIPPED, OrderState.CANCELLED],
        OrderState.SHIPPED: [OrderState.DELIVERED],
        OrderState.DELIVERED: [],
        OrderState.CANCELLED: [],
    }

    @classmethod
    def can_transition(cls, current_state, new_state):
        if isinstance(current_state, str):
            current_state = OrderState(current_state)
        if isinstance(new_state, str):
            new_state = OrderState(new_state)
        return new_state in cls.VALID_TRANSITIONS.get(current_state, [])

    @classmethod
    def transition(cls, order, new_state, reason=None, created_by=None):
        if isinstance(new_state, str):
            new_state = OrderState(new_state)

        if not cls.can_transition(order.status, new_state):
            raise ValidationError(
                f"Cannot transition from {order.status} to {new_state}"
            )

        old_status = order.status
        order.status = new_state.value  # ← .value extracts the string
        order.save()

        from .models import OrderStatusLog
        OrderStatusLog.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_state.value,  # ← .value here too
            reason=reason or "",
            created_by=created_by,
        )

        if new_state == OrderState.CANCELLED:
            for item in order.items.all():
                InventoryService.release_stock(item.product.id, item.quantity)

        return order