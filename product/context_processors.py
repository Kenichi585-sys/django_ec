from .models import Cart, CartItem


def cart_count(request):
    cart_id = request.session.get('cart_id')

    if cart_id:
        try:
            cart = Cart.objects.get(pk=cart_id)
            cart_items = CartItem.objects.filter(cart=cart)
            count = sum(item.quantity for item in cart_items)
        except Cart.DoesNotExist:
            count = 0
    else:
        count = 0

    return {'cart_count': count}

