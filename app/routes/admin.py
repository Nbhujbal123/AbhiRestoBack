from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Order, OrderItem, Payment, MenuItem, Category, db
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.middleware import admin_required
from app.utils import success_response, error_response
import bcrypt

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/menu', methods=['GET'])
@jwt_required()
@admin_required()
def get_admin_menu_items():
    """Get all menu items (admin)"""
    try:
        items = MenuItem.query.order_by(MenuItem.created_at.desc()).all()
        return success_response('Menu items fetched', [item.to_dict() for item in items], 200)
    except Exception as e:
        return error_response(f'Failed to fetch menu items: {str(e)}', 500)


@admin_bp.route('/menu', methods=['POST'])
@jwt_required()
@admin_required()
def create_admin_menu_item():
    """Create menu item (admin only)"""
    data = request.get_json(silent=True) or {}

    for field in ['name', 'price', 'category_id']:
        if data.get(field) in [None, '']:
            return error_response(f'{field} is required', 400)

    category = Category.query.get(data.get('category_id'))
    if not category:
        return error_response('Category not found', 404)

    try:
        price = float(data.get('price'))
    except (TypeError, ValueError):
        return error_response('price must be a valid number', 400)

    if price <= 0:
        return error_response('price must be greater than 0', 400)

    try:
        item = MenuItem(
            name=str(data.get('name')).strip(),
            description=str(data.get('description', '')).strip(),
            price=price,
            category_id=category.id,
            image_url=str(data.get('image_url', '')).strip() or None,
            food_type=data.get('food_type', 'veg') if data.get('food_type') in ['veg', 'non-veg'] else 'veg',
            is_available=bool(data.get('is_available', True)),
            is_featured=bool(data.get('is_featured', False)),
            preparation_time=int(data.get('preparation_time', 15)) if str(data.get('preparation_time', '15')).isdigit() else 15,
        )
        db.session.add(item)
        db.session.commit()
        return success_response('Menu item created successfully', item.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create menu item: {str(e)}', 500)


@admin_bp.route('/menu/<int:item_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_admin_menu_item(item_id):
    """Update menu item (admin only)"""
    item = MenuItem.query.get(item_id)
    if not item:
        return error_response('Menu item not found', 404)

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        if not str(data.get('name', '')).strip():
            return error_response('name cannot be empty', 400)
        item.name = str(data.get('name')).strip()

    if 'description' in data:
        item.description = str(data.get('description', '')).strip()

    if 'price' in data:
        try:
            price = float(data.get('price'))
        except (TypeError, ValueError):
            return error_response('price must be a valid number', 400)
        if price <= 0:
            return error_response('price must be greater than 0', 400)
        item.price = price

    if 'category_id' in data:
        category = Category.query.get(data.get('category_id'))
        if not category:
            return error_response('Category not found', 404)
        item.category_id = category.id

    if 'image_url' in data:
        item.image_url = str(data.get('image_url', '')).strip() or None

    if 'food_type' in data:
        if data.get('food_type') not in ['veg', 'non-veg']:
            return error_response('food_type must be veg or non-veg', 400)
        item.food_type = data.get('food_type')

    if 'is_available' in data:
        item.is_available = bool(data.get('is_available'))

    if 'is_featured' in data:
        item.is_featured = bool(data.get('is_featured'))

    if 'preparation_time' in data:
        try:
            prep = int(data.get('preparation_time'))
        except (TypeError, ValueError):
            return error_response('preparation_time must be integer', 400)
        if prep < 0:
            return error_response('preparation_time must be >= 0', 400)
        item.preparation_time = prep

    try:
        db.session.commit()
        return success_response('Menu item updated successfully', item.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update menu item: {str(e)}', 500)


@admin_bp.route('/menu/<int:item_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_admin_menu_item(item_id):
    """Delete menu item (admin only)"""
    item = MenuItem.query.get(item_id)
    if not item:
        return error_response('Menu item not found', 404)

    try:
        db.session.delete(item)
        db.session.commit()
        return success_response('Menu item deleted successfully', None, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete menu item: {str(e)}', 500)


@admin_bp.route('/categories', methods=['GET'])
@jwt_required()
@admin_required()
def get_admin_categories():
    """Get all categories (admin)"""
    try:
        categories = Category.query.order_by(Category.display_order, Category.name).all()
        return success_response('Categories fetched', [cat.to_dict() for cat in categories], 200)
    except Exception as e:
        return error_response(f'Failed to fetch categories: {str(e)}', 500)


@admin_bp.route('/categories', methods=['POST'])
@jwt_required()
@admin_required()
def create_admin_category():
    """Create category (admin only)"""
    data = request.get_json(silent=True) or {}
    name = str(data.get('name', '')).strip()
    if not name:
        return error_response('name is required', 400)

    if Category.query.filter(func.lower(Category.name) == name.lower()).first():
        return error_response('Category with this name already exists', 400)

    try:
        category = Category(
            name=name,
            description=str(data.get('description', '')).strip() or None,
            image_url=str(data.get('image_url', '')).strip() or None,
            is_active=bool(data.get('is_active', True)),
            display_order=int(data.get('display_order', 0)) if str(data.get('display_order', '0')).lstrip('-').isdigit() else 0,
        )
        db.session.add(category)
        db.session.commit()
        return success_response('Category created successfully', category.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create category: {str(e)}', 500)


@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_admin_category(category_id):
    """Update category (admin only)"""
    category = Category.query.get(category_id)
    if not category:
        return error_response('Category not found', 404)

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        name = str(data.get('name', '')).strip()
        if not name:
            return error_response('name cannot be empty', 400)
        existing = Category.query.filter(func.lower(Category.name) == name.lower(), Category.id != category_id).first()
        if existing:
            return error_response('Category with this name already exists', 400)
        category.name = name

    if 'description' in data:
        category.description = str(data.get('description', '')).strip() or None
    if 'image_url' in data:
        category.image_url = str(data.get('image_url', '')).strip() or None
    if 'is_active' in data:
        category.is_active = bool(data.get('is_active'))
    if 'display_order' in data:
        try:
            category.display_order = int(data.get('display_order'))
        except (TypeError, ValueError):
            return error_response('display_order must be integer', 400)

    try:
        db.session.commit()
        return success_response('Category updated successfully', category.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update category: {str(e)}', 500)


@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_admin_category(category_id):
    """Delete category (admin only)"""
    category = Category.query.get(category_id)
    if not category:
        return error_response('Category not found', 404)

    if category.menu_items.count() > 0:
        return error_response('Cannot delete category with menu items', 400)

    try:
        db.session.delete(category)
        db.session.commit()
        return success_response('Category deleted successfully', None, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete category: {str(e)}', 500)


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required()
def get_dashboard_stats():
    """
    Get admin dashboard statistics
    """
    try:
        # Total users
        total_users = User.query.filter_by(role='customer').count()
        
        # Total orders
        total_orders = Order.query.count()
        
        # Total revenue (completed orders)
        total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            Order.status == 'delivered'
        ).scalar() or 0
        
        # Today's orders
        today = datetime.utcnow().date()
        today_orders = Order.query.filter(
            func.date(Order.created_at) == today
        ).count()
        
        # Today's revenue
        today_revenue = db.session.query(func.sum(Order.total_amount)).filter(
            and_(
                func.date(Order.created_at) == today,
                Order.status == 'delivered'
            )
        ).scalar() or 0
        
        # Orders by status
        orders_by_status = {}
        statuses = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']
        for status in statuses:
            count = Order.query.filter_by(status=status).count()
            orders_by_status[status] = count
        
        # Active orders (not delivered or cancelled)
        active_orders = Order.query.filter(
            Order.status.in_(['pending', 'confirmed', 'preparing', 'out_for_delivery'])
        ).order_by(Order.created_at.desc()).all()
        
        return success_response('Dashboard stats fetched', {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_revenue': float(total_revenue),
            'today_orders': today_orders,
            'today_revenue': float(today_revenue),
            'orders_by_status': orders_by_status,
            'recent_orders': [order.to_dict() for order in active_orders]
        }, 200)
        
    except Exception as e:
        return error_response(f'Failed to get dashboard stats: {str(e)}', 500)


@admin_bp.route('/monthly-sales', methods=['GET'])
@jwt_required()
@admin_required()
def get_monthly_sales():
    """
    Get monthly sales data for the last 12 months
    """
    try:
        # Get last 12 months data
        monthly_data = []
        
        for i in range(11, -1, -1):
            # Calculate month
            month_date = datetime.utcnow() - timedelta(days=30 * i)
            month_start = month_date.replace(day=1)
            
            if i == 0:
                # Current month - use current date
                month_end = datetime.utcnow()
            else:
                # Previous months - get last day of month
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1, day=1)
            
            # Get orders for this month
            orders = Order.query.filter(
                and_(
                    Order.created_at >= month_start,
                    Order.created_at < month_end,
                    Order.status == 'delivered'
                )
            ).all()
            
            revenue = sum(float(order.total_amount) for order in orders)
            count = len(orders)
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'revenue': revenue,
                'orders': count
            })
        
        return success_response('Monthly sales fetched', monthly_data, 200)
        
    except Exception as e:
        return error_response(f'Failed to get monthly sales: {str(e)}', 500)


@admin_bp.route('/top-items', methods=['GET'])
@jwt_required()
@admin_required()
def get_top_selling_items():
    """
    Get top selling menu items
    """
    try:
        # Get top 10 items by quantity sold
        top_items = db.session.query(
            MenuItem.id,
            MenuItem.name,
            MenuItem.price,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.subtotal).label('total_revenue')
        ).join(OrderItem).join(Order).filter(
            Order.status == 'delivered'
        ).group_by(MenuItem.id).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(10).all()
        
        return success_response('Top selling items fetched', [{
            'id': item.id,
            'name': item.name,
            'price': float(item.price),
            'total_sold': item.total_sold,
            'total_revenue': float(item.total_revenue)
        } for item in top_items], 200)
        
    except Exception as e:
        return error_response(f'Failed to get top items: {str(e)}', 500)


@admin_bp.route('/orders', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_orders():
    """
    Get all orders (admin)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', None)
        
        query = Order.query.order_by(Order.created_at.desc())
        
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return success_response('Orders fetched', {
            'orders': [order.to_dict() for order in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }, 200)
        
    except Exception as e:
        return error_response(f'Failed to get orders: {str(e)}', 500)


@admin_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
@admin_required()
def update_order_status(order_id):
    """
    Update order status (admin)
    ---
    Request Body:
    {
        "status": "preparing"  // pending, confirmed, preparing, out_for_delivery, delivered, cancelled
    }
    """
    order = Order.query.get(order_id)
    
    if not order:
        return error_response('Order not found', 404)
    
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    
    valid_statuses = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return error_response(f'Invalid status. Must be one of: {", ".join(valid_statuses)}', 400)
    
    try:
        order.status = new_status
        db.session.commit()
        
        return success_response('Order status updated', order.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update status: {str(e)}', 500)


@admin_bp.route('/payments/<int:payment_id>/status', methods=['PUT'])
@jwt_required()
@admin_required()
def update_payment_status(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return error_response('Payment not found', 404)

    data = request.get_json(silent=True) or {}
    status = data.get('status')
    if status not in ['pending', 'completed', 'failed', 'refunded']:
        return error_response('Invalid payment status', 400)

    transaction_id = data.get('transaction_id')
    if transaction_id:
        payment.transaction_id = str(transaction_id).strip()
    payment.status = status

    if status == 'completed' and payment.order and payment.order.status == 'pending':
        payment.order.status = 'confirmed'

    try:
        db.session.commit()
        return success_response('Payment status updated', payment.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update payment status: {str(e)}', 500)


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_users():
    """
    Get all users (admin)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role = request.args.get('role', None)
        
        query = User.query.order_by(User.created_at.desc())
        
        if role:
            query = query.filter_by(role=role)
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return success_response('Users fetched', {
            'users': [user.to_dict() for user in pagination.items],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }, 200)
        
    except Exception as e:
        return error_response(f'Failed to get users: {str(e)}', 500)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['PUT'])
@jwt_required()
@admin_required()
def toggle_user_status(user_id):
    """
    Toggle user active status (admin)
    """
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', 404)
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        return success_response(
            f'User {"activated" if user.is_active else "deactivated"} successfully',
            user.to_dict(),
            200
        )
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update user status: {str(e)}', 500)


@admin_bp.route('/profile', methods=['GET'])
@jwt_required()
@admin_required()
def get_admin_profile():
    """
    Get current admin profile
    """
    try:
        identity = get_jwt_identity()
        # Identity is user ID (stored as string), convert to int
        try:
            user_id = int(identity)
        except (ValueError, TypeError):
            return error_response('Invalid token', 401)
        
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email.split('@')[0]
        
        return success_response('Profile fetched', {
            'id': user.id,
            'full_name': full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.email.split('@')[0],
            'email': user.email,
            'phone': user.phone,
            'role': user.role
        }, 200)
        
    except Exception as e:
        return error_response(f'Failed to get profile: {str(e)}', 500)


@admin_bp.route('/profile', methods=['PUT'])
@jwt_required()
@admin_required()
def update_admin_profile():
    """
    Update current admin profile
    ---
    Request Body:
    {
        "full_name": "New Name",
        "first_name": "First Name",
        "last_name": "Last Name",
        "phone": "1234567890",
        "current_password": "oldpassword", (required if changing password)
        "new_password": "newpassword" (optional)
    }
    """
    try:
        identity = get_jwt_identity()
        # Identity is user ID (stored as string), convert to int
        try:
            user_id = int(identity)
        except (ValueError, TypeError):
            return error_response('Invalid token', 401)
        
        user = User.query.get(user_id)
        
        if not user:
            return error_response('User not found', 404)
        
        data = request.get_json(silent=True) or {}
        
        # Update name fields
        if 'full_name' in data:
            full_name = str(data.get('full_name', '')).strip()
            # Split full_name into first_name and last_name
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if 'first_name' in data:
            user.first_name = str(data.get('first_name', '')).strip()
        
        if 'last_name' in data:
            user.last_name = str(data.get('last_name', '')).strip()
        
        if 'phone' in data:
            user.phone = str(data.get('phone', '')).strip() or None
        
        # Handle password change
        if data.get('new_password'):
            try:
                current_password = data.get('current_password', '')
                if not current_password:
                    return error_response('Current password is required to change password', 400)
                
                # Verify current password
                if not bcrypt.check_password_hash(user.password_hash, current_password):
                    return error_response('Current password does not match', 400)
                
                # Update password
                new_password = str(data.get('new_password', ''))
                if len(new_password) < 6:
                    return error_response('Password must be at least 6 characters', 400)
                
                user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            except Exception as e:
                return error_response('Failed to update password', 400)
        
        db.session.commit()
        
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email.split('@')[0]
        
        return success_response('Profile updated successfully', {
            'id': user.id,
            'full_name': full_name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.email.split('@')[0],
            'email': user.email,
            'phone': user.phone,
            'role': user.role
        }, 200)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update profile: {str(e)}', 500)
