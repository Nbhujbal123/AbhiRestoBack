import os
from app import create_app, db
from app.models import User, Category
from app.extensions import bcrypt

app = create_app(os.environ.get('FLASK_ENV', 'production'))


def init_db():
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
        
        # Create default admin user if not exists
        admin_email = "admin@restom.com"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
            admin = User(
                email=admin_email,
                phone="9876543210",
                password_hash=admin_password,
                role="admin",
                is_verified=True,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin@restom.com / admin123")
        else:
            print("Admin user already exists")
            
        # Create test customer user if not exists
        test_email = "testuser@example.com"
        test_user = User.query.filter_by(email=test_email).first()
        if not test_user:
            test_password = bcrypt.generate_password_hash("test123").decode('utf-8')
            test_user = User(
                email=test_email,
                first_name="John",
                last_name="Doe",
                phone="9876543210",
                password_hash=test_password,
                role="customer",
                is_verified=True,
                is_active=True
            )
            db.session.add(test_user)
            db.session.commit()
            print("Test customer user created: testuser@example.com / test123")
        else:
            # Update existing user with name fields if they don't have it
            if not test_user.first_name:
                test_user.first_name = "John"
                test_user.last_name = "Doe"
                db.session.commit()
                print("Test customer user updated with name")
            print("Test customer user already exists")
            
        # Create default categories if not exists
        default_categories = [
            {"name": "Starters", "display_order": 1},
            {"name": "Main Course", "display_order": 2},
            {"name": "Kids", "display_order": 3},
            {"name": "Desserts", "display_order": 4},
            {"name": "Beverages", "display_order": 5},
        ]
        for cat_data in default_categories:
            existing = Category.query.filter_by(name=cat_data["name"]).first()
            if not existing:
                category = Category(
                    name=cat_data["name"],
                    display_order=cat_data["display_order"],
                    is_active=True
                )
                db.session.add(category)
        db.session.commit()
        print("Default categories created")


if __name__ == '__main__':
    init_db()
    
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host=host, port=port, debug=debug)
