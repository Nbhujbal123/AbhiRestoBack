from datetime import datetime
from app.models.user import db


class CartItem(db.Model):
    """Cart item model"""
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert cart item to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'menu_item_id': self.menu_item_id,
            'quantity': self.quantity,
            'menu_item': self.menu_item.to_dict() if self.menu_item else None,
            'subtotal': float(self.menu_item.price) * self.quantity if self.menu_item else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<CartItem user={self.user_id} item={self.menu_item_id}>'
