from datetime import datetime
from app.models.user import db


class Payment(db.Model):
    """Payment model"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, card, upi
    transaction_id = db.Column(db.String(100), nullable=True, unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed, refunded
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def generate_transaction_id():
        """Generate unique transaction ID"""
        from datetime import datetime
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f'TXN{timestamp}{random_suffix}'
    
    def __repr__(self):
        return f'<Payment order={self.order_id} status={self.status}>'
