# Controllers package - Business logic layer
# This file contains controller functions for handling route logic

# The actual controller logic is embedded in the route files in app/routes/
# This file serves as a reference/entry point for controllers

"""
RestoM Restaurant Management System - Controllers

This file documents the controller layer structure:

1. Auth Controllers (app/routes/auth.py)
   - send_otp(): Send OTP to email
   - verify_otp(): Verify OTP
   - create_account(): Create new account
   - login(): User login
   - forgot_password_send_otp(): Send password reset OTP
   - forgot_password_reset(): Reset password

2. User Controllers (app/routes/user.py)
   - get_profile(): Get user profile
   - update_profile(): Update user profile
   - change_password(): Change password

3. Menu Controllers (app/routes/menu.py)
   - get_menu_items(): Get all menu items
   - get_menu_item(): Get single menu item
   - create_menu_item(): Create menu item (admin)
   - update_menu_item(): Update menu item (admin)
   - delete_menu_item(): Delete menu item (admin)

4. Category Controllers (app/routes/category.py)
   - get_categories(): Get all categories
   - create_category(): Create category (admin)
   - update_category(): Update category (admin)
   - delete_category(): Delete category (admin)

5. Cart Controllers (app/routes/cart.py)
   - get_cart(): Get user cart
   - add_to_cart(): Add item to cart
   - update_cart_item(): Update cart item quantity
   - remove_from_cart(): Remove item from cart
   - clear_cart(): Clear all cart items

6. Order Controllers (app/routes/order.py)
   - create_order(): Create new order
   - get_orders(): Get user orders
   - get_order(): Get single order
   - update_order_status(): Update order status (admin)
   - cancel_order(): Cancel order

7. Admin Controllers (app/routes/admin.py)
   - get_dashboard_stats(): Get dashboard statistics
   - get_all_orders(): Get all orders (admin)
   - get_all_users(): Get all users (admin)
   - manage_user(): Activate/deactivate user
"""

# Re-export route functions as controllers for clarity
from app.routes import auth_bp, user_bp, menu_bp, category_bp, cart_bp, order_bp, admin_bp

__all__ = [
    'auth_bp',
    'user_bp',
    'menu_bp', 
    'category_bp',
    'cart_bp',
    'order_bp',
    'admin_bp'
]
