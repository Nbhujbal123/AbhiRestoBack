from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import User
from app.utils import error_response


def admin_required():
    """Decorator to check if user is admin"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            # Convert string to int if needed
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                pass
            user = User.query.get(user_id)
            
            if not user:
                return error_response("User not found", 404)
            
            if user.role != 'admin':
                return error_response("Admin access required", 403)
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def customer_required():
    """Decorator to check if user is a customer"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            # Convert string to int if needed
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                pass
            user = User.query.get(user_id)
            
            if not user:
                return error_response("User not found", 404)
            
            if user.role not in ['customer', 'admin']:
                return error_response("Invalid user role", 403)
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def get_current_user():
    """Get current logged in user"""
    try:
        user_id = get_jwt_identity()
        # Convert string to int if needed
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass
        return User.query.get(user_id)
    except Exception:
        return None
