from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Order, OrderItem, CartItem, MenuItem, Payment, db
from app.utils import success_response, error_response, validate_phone

order_bp = Blueprint("order", __name__)


@order_bp.route("/create", methods=["POST"])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    data = request.get_json(silent=True) or {}

    # Get items from request body or from database cart
    items_from_request = data.get("items", [])
    
    # If items provided in request, use them; otherwise check database cart
    if items_from_request:
        # Validate items
        if not isinstance(items_from_request, list):
            return error_response("Items must be a list", 400)
        
        cart_items = []
        for item in items_from_request:
            menu_item_id = item.get("menu_item_id")
            quantity = item.get("quantity", 1)
            
            if not menu_item_id:
                return error_response("menu_item_id is required for each item", 400)
            
            menu_item = MenuItem.query.get(menu_item_id)
            if not menu_item:
                return error_response(f"Menu item {menu_item_id} not found", 404)
            if not menu_item.is_available:
                return error_response(f"Item {menu_item.name} is no longer available", 400)
            
            # Create a cart-like object
            cart_items.append(type('obj', (object,), {
                'menu_item': menu_item,
                'quantity': quantity
            }))
    else:
        # Use database cart items (original behavior)
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        if not cart_items:
            return error_response("Cart is empty", 400)

        for cart_item in cart_items:
            if not cart_item.menu_item or not cart_item.menu_item.is_available:
                item_name = cart_item.menu_item.name if cart_item.menu_item else "Unknown"
                return error_response(f"Item {item_name} is no longer available", 400)

    payment_method = data.get("payment_method", "cash")
    if payment_method not in ["cash", "card", "upi"]:
        return error_response("Invalid payment_method. Use cash, card, or upi", 400)

    is_valid_phone, phone_err = validate_phone(data.get("delivery_phone", ""))
    if not is_valid_phone:
        return error_response(phone_err, 400)

    total_amount = sum(
        cart_item.menu_item.price * cart_item.quantity for cart_item in cart_items if cart_item.menu_item
    )

    try:
        order = Order(
            order_number=Order.generate_order_number(),
            user_id=user_id,
            total_amount=total_amount,
            delivery_address=str(data.get("delivery_address", "")).strip(),
            delivery_phone=str(data.get("delivery_phone", "")).strip(),
            notes=str(data.get("notes", "")).strip(),
            status="pending",
        )
        db.session.add(order)
        db.session.flush()

        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=cart_item.menu_item.id,
                quantity=cart_item.quantity,
                unit_price=cart_item.menu_item.price,
                subtotal=cart_item.menu_item.price * cart_item.quantity,
            )
            db.session.add(order_item)

        payment = Payment(
            order_id=order.id,
            payment_method=payment_method,
            amount=total_amount,
            status="pending",
        )

        if payment_method in ["card", "upi"]:
            payment.transaction_id = Payment.generate_transaction_id()
            payment.status = "completed"
            order.status = "confirmed"

        db.session.add(payment)
        
        # Only clear database cart if we used it (not items from request)
        if not items_from_request:
            CartItem.query.filter_by(user_id=user_id).delete()
        
        db.session.commit()

        return success_response("Order placed successfully", order.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to create order: {str(e)}", 500)


@order_bp.route("", methods=["GET"])
@jwt_required()
def get_my_orders():
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    pagination = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return success_response(
        "Orders fetched",
        {
            "orders": [order.to_dict() for order in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            },
        },
        200,
    )


@order_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return error_response("Order not found", 404)
    return success_response("Order fetched", order.to_dict(), 200)


@order_bp.route("/<int:order_id>/status", methods=["GET"])
@jwt_required()
def get_order_status(order_id):
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return error_response("Order not found", 404)

    return success_response(
        "Order status fetched",
        {
            "order_id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        },
        200,
    )


@order_bp.route("/<int:order_id>/payment", methods=["PUT"])
@jwt_required()
def update_payment_status(order_id):
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return error_response("Order not found", 404)

    payment = Payment.query.filter_by(order_id=order.id).first()
    if not payment:
        return error_response("Payment record not found", 404)

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ["pending", "completed", "failed", "refunded"]:
        return error_response("Invalid payment status", 400)

    transaction_id = data.get("transaction_id")
    if transaction_id:
        payment.transaction_id = str(transaction_id).strip()

    payment.status = status
    if status == "completed" and order.status == "pending":
        order.status = "confirmed"

    try:
        db.session.commit()
        return success_response("Payment updated", payment.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f"Failed to update payment: {str(e)}", 500)


@order_bp.route("/track/<string:order_number>", methods=["GET"])
def track_order(order_number):
    phone = request.args.get("phone")
    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        return error_response("Order not found", 404)

    if phone and order.delivery_phone != phone:
        return error_response("Invalid phone number for this order", 404)

    return success_response(
        "Order tracking details fetched",
        {
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "items": [item.to_dict() for item in order.order_items],
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
        },
        200,
    )
