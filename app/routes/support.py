from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import SupportMessage, User, db
from app.middleware import admin_required
from app.utils import success_response, error_response

support_bp = Blueprint('support', __name__)


@support_bp.route('/messages', methods=['POST'])
@jwt_required()
def create_support_message():
    data = request.get_json(silent=True) or {}

    full_name = str(data.get('full_name', '')).strip()
    email = str(data.get('email', '')).strip()
    message = str(data.get('message', '')).strip()

    if not full_name:
        return error_response('full_name is required', 400)
    if not email:
        return error_response('email is required', 400)
    if not message:
        return error_response('message is required', 400)

    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        user_id = None

    user = User.query.get(user_id) if user_id else None

    try:
        support_message = SupportMessage(
            user_id=user.id if user else None,
            full_name=full_name,
            email=email,
            message=message,
        )
        db.session.add(support_message)
        db.session.commit()
        return success_response('Support request submitted successfully', support_message.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to submit support request: {str(e)}', 500)


@support_bp.route('/messages', methods=['GET'])
@jwt_required()
@admin_required()
def get_support_messages():
    try:
        messages = SupportMessage.query.order_by(SupportMessage.created_at.desc()).limit(20).all()
        unread_count = SupportMessage.query.filter_by(is_read=False).count()
        return success_response('Support messages fetched', {
            'messages': [msg.to_dict() for msg in messages],
            'unread_count': unread_count,
        }, 200)
    except Exception as e:
        return error_response(f'Failed to fetch support messages: {str(e)}', 500)


@support_bp.route('/messages/<int:message_id>/read', methods=['PUT'])
@jwt_required()
@admin_required()
def mark_support_message_read(message_id):
    message = SupportMessage.query.get(message_id)
    if not message:
        return error_response('Support message not found', 404)

    try:
        message.is_read = True
        db.session.commit()
        return success_response('Support message marked as read', message.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to mark support message as read: {str(e)}', 500)
