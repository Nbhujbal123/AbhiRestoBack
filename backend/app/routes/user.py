from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Order, db
from app.utils import success_response, error_response, validate_phone

user_bp = Blueprint('user', __name__)


@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get user profile
    """
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', 404)
    
    return success_response('Profile fetched successfully', user.to_dict(), 200)


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    ---
    Request Body:
    {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+91 9876543210",
        "address": "123 Main St, City"
    }
    """
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', 404)
    
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return error_response('Invalid JSON payload', 400)

    if 'phone' in data:
        is_valid, err = validate_phone(data.get('phone'))
        if not is_valid:
            return error_response(err, 400)

    if 'first_name' in data and (not data['first_name'] or not str(data['first_name']).strip()):
        return error_response('first_name cannot be empty', 400)
    
    # Update fields
    if 'first_name' in data:
        user.first_name = str(data['first_name']).strip()
    if 'last_name' in data:
        user.last_name = str(data['last_name']).strip()
    if 'phone' in data:
        user.phone = str(data['phone']).strip()
    if 'address' in data:
        user.address = str(data['address']).strip()
    
    try:
        db.session.commit()
        return success_response('Profile updated successfully', user.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update profile: {str(e)}', 500)


@user_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_order_history():
    """
    Get user order history
    """
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', None)
    
    # Build query
    query = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc())
    
    # Filter by status if provided
    if status:
        query = query.filter_by(status=status)
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return success_response('Order history fetched', {
            'orders': [order.to_dict() for order in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }, 200)


@user_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    """
    Get specific order details
    """
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    
    if not order:
        return error_response('Order not found', 404)
    
    return success_response('Order details fetched', order.to_dict(), 200)
