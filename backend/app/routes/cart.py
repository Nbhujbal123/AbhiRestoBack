from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import CartItem, MenuItem, db
from app.utils import success_response, error_response

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("", methods=["GET"])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    total = sum(item.menu_item.price * item.quantity for item in cart_items if item.menu_item)

    return success_response(
        "Cart fetched successfully",
        {
            "items": [item.to_dict() for item in cart_items],
            "item_count": len(cart_items),
            "total": float(total),
        },
        200,
    )


@cart_bp.route("/add", methods=["POST"])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    data = request.get_json(silent=True) or {}

    menu_item_id = data.get("menu_item_id")
    if not menu_item_id:
        return error_response("menu_item_id is required", 400)

    menu_item = MenuItem.query.get(menu_item_id)
    if not menu_item:
        return error_response("Menu item not found", 404)
    if not menu_item.is_available:
        return error_response("Menu item is not available", 400)

    try:
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return error_response("quantity must be an integer", 400)
    if quantity < 1:
        return error_response("Quantity must be at least 1", 400)

    try:
        existing_item = CartItem.query.filter_by(user_id=user_id, menu_item_id=menu_item_id).first()
        if existing_item:
            existing_item.quantity += quantity
            db.session.commit()
            return success_response("Cart updated successfully", existing_item.to_dict(), 200)

        new_item = CartItem(user_id=user_id, menu_item_id=menu_item_id, quantity=quantity)
        db.session.add(new_item)
        db.session.commit()
        return success_response("Item added to cart", new_item.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to add item to cart: {str(e)}", 500)


@cart_bp.route("/update/<int:item_id>", methods=["PUT"])
@jwt_required()
def update_cart_item(item_id):
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    data = request.get_json(silent=True) or {}

    cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not cart_item:
        return error_response("Cart item not found", 404)

    quantity = data.get("quantity")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return error_response("quantity must be an integer", 400)

    if quantity < 1:
        return error_response("Valid quantity is required", 400)

    try:
        cart_item.quantity = quantity
        db.session.commit()
        return success_response("Cart updated successfully", cart_item.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to update cart: {str(e)}", 500)


@cart_bp.route("/remove/<int:item_id>", methods=["DELETE"])
@jwt_required()
def remove_from_cart(item_id):
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not cart_item:
        return error_response("Cart item not found", 404)

    try:
        db.session.delete(cart_item)
        db.session.commit()
        return success_response("Item removed from cart", None, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to remove item: {str(e)}", 500)


@cart_bp.route("/clear", methods=["DELETE"])
@jwt_required()
def clear_cart():
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    try:
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return success_response("Cart cleared successfully", None, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to clear cart: {str(e)}", 500)
