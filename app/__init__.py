import os
from flask import Flask, send_from_directory
from app.config import config
from app.models import db
from app.extensions import bcrypt, jwt, mail, cors
from app.utils import error_response


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config.get(config_name, config["development"]))
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize JWT with explicit secret key
    app.config['JWT_SECRET_KEY'] = app.config.get('JWT_SECRET_KEY', 'restom-jwt-secret-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # Create uploads folder
    upload_folder = app.config.get("UPLOAD_FOLDER")
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Register blueprints
    from app.routes import auth_bp, user_bp, menu_bp, category_bp, cart_bp, order_bp, admin_bp, support_bp
    from app.routes.auth import register as auth_register, login as auth_login, send_otp as auth_send_otp, verify_otp as auth_verify_otp, create_account as auth_create_account
    from app.routes.menu import get_menu_items as public_menu_items
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(category_bp, url_prefix='/api/categories')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(support_bp, url_prefix='/api/support')

    # Root auth routes required by frontend contract
    app.add_url_rule('/api/signup', endpoint='signup_root', view_func=auth_register, methods=['POST'])
    app.add_url_rule('/api/login', endpoint='login_root', view_func=auth_login, methods=['POST'])
    app.add_url_rule('/api/menu', endpoint='menu_root_exact', view_func=public_menu_items, methods=['GET'])
    
    # OTP routes
    app.add_url_rule('/api/send-otp', endpoint='send_otp', view_func=auth_send_otp, methods=['POST'])
    app.add_url_rule('/api/verify-otp', endpoint='verify_otp', view_func=auth_verify_otp, methods=['POST'])
    app.add_url_rule('/api/create-account', endpoint='create_account', view_func=auth_create_account, methods=['POST'])

    # Auto-create tables if not exists
    with app.app_context():
        db.create_all()
    
    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
    
    # Home route
    @app.route('/')
    def home():
        return {
            "success": True,
            "message": "Resto backend API is running successfully"
        }, 200

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {
            "success": True,
            "message": "API is running",
            "version": "1.0.0",
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return error_response("Resource not found", 404)

    @app.errorhandler(400)
    def bad_request(error):
        return error_response("Bad request", 400)
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return error_response("Internal server error", 500)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response("Token has expired", 401)
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return error_response("Invalid token", 401)
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return error_response("Authorization token is required", 401)

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return error_response("Token has been revoked", 401)
    
    return app
