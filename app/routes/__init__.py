from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.menu import menu_bp
from app.routes.category import category_bp
from app.routes.cart import cart_bp
from app.routes.order import order_bp
from app.routes.admin import admin_bp
from app.routes.support import support_bp

__all__ = [
    'auth_bp',
    'user_bp',
    'menu_bp',
    'category_bp',
    'cart_bp',
    'order_bp',
    'admin_bp',
    'support_bp'
]
