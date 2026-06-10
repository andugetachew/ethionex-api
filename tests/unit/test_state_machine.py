# tests/unit/test_state_machine.py
import pytest
from orders.models import Order
from unittest.mock import patch
from orders.models import OrderItem


@pytest.fixture
def order(db, test_user):
    return Order.objects.create(
        user=test_user,
        full_name="User",
        phone_number="09",
        address="Addr",
        city="City",
        payment_method="cash",
        status="pending",
        subtotal=100,
        total=100,
    )


@pytest.mark.django_db
class TestOrderStateMachine:

    def test_pending_to_paid(self, order):
        from orders.state_machine import OrderStateMachine

        result = OrderStateMachine.transition(order, "paid")
        assert result.status == "paid"

    def test_paid_to_processing(self, order):
        from orders.state_machine import OrderStateMachine

        order.status = "paid"
        order.save()
        result = OrderStateMachine.transition(order, "processing")
        assert result.status == "processing"

    def test_processing_to_shipped(self, order):
        from orders.state_machine import OrderStateMachine

        order.status = "processing"
        order.save()
        result = OrderStateMachine.transition(order, "shipped")
        assert result.status == "shipped"

    def test_shipped_to_delivered(self, order):
        from orders.state_machine import OrderStateMachine

        order.status = "shipped"
        order.save()
        result = OrderStateMachine.transition(order, "delivered")
        assert result.status == "delivered"

    def test_pending_to_cancelled(self, order):
        from orders.state_machine import OrderStateMachine

        result = OrderStateMachine.transition(order, "cancelled")
        assert result.status == "cancelled"

    def test_invalid_transition_raises(self, order):
        from orders.state_machine import OrderStateMachine

        with pytest.raises(Exception):
            OrderStateMachine.transition(order, "delivered")

    def test_delivered_is_terminal(self, order):
        from orders.state_machine import OrderStateMachine

        order.status = "delivered"
        order.save()
        with pytest.raises(Exception):
            OrderStateMachine.transition(order, "paid")


@pytest.mark.django_db
class TestOrderStateMachineExtra:

    def test_can_transition_valid(self):
        from orders.state_machine import (
            OrderStateMachine,
            OrderState,
        )

        assert OrderStateMachine.can_transition(
            OrderState.PENDING,
            OrderState.PAID,
        )

    def test_can_transition_invalid(self):
        from orders.state_machine import (
            OrderStateMachine,
            OrderState,
        )

        assert not OrderStateMachine.can_transition(
            OrderState.PENDING,
            OrderState.SHIPPED,
        )

    def test_can_transition_string_values(self):
        from orders.state_machine import OrderStateMachine

        assert OrderStateMachine.can_transition(
            "pending",
            "paid",
        )

    @patch("orders.models.OrderStatusLog.objects.create")
    def test_status_log_created(
        self,
        mock_log,
        order,
    ):
        from orders.state_machine import OrderStateMachine

        OrderStateMachine.transition(
            order,
            "paid",
            reason="payment received",
        )

        mock_log.assert_called_once()

    @patch("orders.state_machine.InventoryService.release_stock")
    def test_cancel_calls_inventory_release(
        self,
        mock_release,
        order,
        test_product,
    ):
        from orders.state_machine import OrderStateMachine

        OrderItem.objects.create(
            order=order,
            product=test_product,
            quantity=3,
            price=100,
        )
        OrderStateMachine.transition(order, "cancelled")
        mock_release.assert_called_once_with(test_product.id, 3)
