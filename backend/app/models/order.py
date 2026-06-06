from datetime import datetime
from app.models.user import db
from app.models.user import User


class Order(db.Model):
    """Order model"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.Enum(
            'pending',
            'confirmed',
            'preparing',
            'out_for_delivery',
            'delivered',
            'cancelled',
            name='order_statuses'
        ),
        default='pending',
        nullable=False,
    )
    delivery_address = db.Column(db.Text, nullable=True)
    delivery_phone = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert order to dictionary"""
        # Get user info
        user = User.query.get(self.user_id)
        user_data = None
        if user:
            user_name = getattr(user, 'name', None)
            if not user_name:
                user_name = user.email.split('@')[0] if user.email else 'Unknown'
            user_data = {
                'id': user.id,
                'name': user_name,
                'phone': user.phone
            }
        return {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'user': user_data,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'delivery_address': self.delivery_address,
            'delivery_phone': self.delivery_phone,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.order_items],
            'payment': self.payment.to_dict() if self.payment else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number (3-4 characters)"""
        import random
        import string
        # Generate 3-4 character random string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    """Order item model"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'menu_item_id': self.menu_item_id,
            'name': self.menu_item.name if self.menu_item else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'subtotal': float(self.subtotal)
        }
    
    def __repr__(self):
        return f'<OrderItem order={self.order_id} item={self.menu_item_id}>'
