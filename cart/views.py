from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer
from products.models import Product


class CartView(APIView):
    """View and manage cart"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        """Add item to cart"""
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data["product_id"]
            quantity = serializer.validated_data["quantity"]

            product = get_object_or_404(Product, id=product_id, is_available=True)
            cart, _ = Cart.objects.get_or_create(user=request.user)

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, product=product, defaults={"quantity": quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return Response(
                {
                    "message": f"Added {quantity} x {product.name} to cart",
                    "cart": CartSerializer(cart).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateCartItemView(APIView):
    """Update cart item quantity"""

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = request.data.get("quantity", 1)

        if quantity <= 0:
            cart_item.delete()
            message = "Item removed from cart"
        else:
            cart_item.quantity = quantity
            cart_item.save()
            message = "Cart updated"

        cart = Cart.objects.get(user=request.user)
        return Response({"message": message, "cart": CartSerializer(cart).data})


class RemoveFromCartView(APIView):
    """Remove item from cart"""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()

        cart = Cart.objects.get(user=request.user)
        return Response(
            {"message": "Item removed from cart", "cart": CartSerializer(cart).data}
        )
