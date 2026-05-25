from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models import User, EmailOTP, db
from app.extensions import bcrypt, mail
from app.utils import success_response, error_response
import random
import string
from datetime import datetime, timedelta
from flask_mail import Message
from sqlalchemy.exc import OperationalError
import smtplib

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def send_otp_email(email, subject, body):
    msg = Message(
        subject=subject,
        recipients=[email],
        body=body
    )
    mail.send(msg)


@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """
    STEP 1: Send OTP to email
    Input: email
    """
    data = request.get_json(silent=True) or {}
    
    email = data.get('email', '').strip().lower()
    
    if not email:
        return error_response('Email is required', 400)
    
    if not validate_email(email):
        return error_response('Invalid email format', 400)
    
    try:
        # Check if email already registered
        if User.query.filter_by(email=email).first():
            return error_response('Email already registered', 409)
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)
    except Exception:
        db.session.rollback()
        return error_response('Unable to process request right now. Please try again.', 500)
    
    # Generate 6-digit OTP
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    # Calculate expiry (5 minutes from now)
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # Save OTP to database
    new_otp = EmailOTP(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at
    )
    
    try:
        db.session.add(new_otp)
        db.session.commit()
        
        try:
            send_otp_email(
                email,
                "Your RestoM OTP Verification Code",
                f"Your verification code is: {otp_code}\n\nThis code will expire in 5 minutes.\n\nIf you didn't request this, please ignore this email."
            )
        except smtplib.SMTPAuthenticationError as e:
            db.session.delete(new_otp)
            db.session.commit()
            print(f"Gmail rejected SMTP credentials for {email}: {e}")
            return error_response('Gmail rejected the sender email/password. Please update MAIL_USERNAME and MAIL_PASSWORD with a valid Gmail app password.', 502)
        except Exception as e:
            db.session.delete(new_otp)
            db.session.commit()
            print(f"Error sending email to {email}: {e}")
            return error_response('Unable to send OTP email. Please check the email configuration and try again.', 502)
        
        return success_response('OTP sent to your email', {
            'email': email,
            'expires_in': '5 minutes'
        }, 200)
        
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to send OTP: {str(e)}', 500)


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    STEP 2: Verify OTP
    Input: email + otp
    """
    data = request.get_json(silent=True) or {}
    
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()
    
    if not email or not otp:
        return error_response('Email and OTP are required', 400)
    
    try:
        # Find the latest unused OTP for this email
        otp_record = EmailOTP.query.filter_by(
            email=email,
            otp_code=otp,
            is_used=False
        ).order_by(EmailOTP.created_at.desc()).first()
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)
    
    if not otp_record:
        return error_response('Invalid OTP', 400)
    
    # Check if OTP is expired
    if datetime.utcnow() > otp_record.expires_at:
        return error_response('OTP has expired', 400)
    
    # Mark OTP as used
    otp_record.is_used = True
    
    try:
        db.session.commit()
        return success_response('OTP verified successfully', {
            'email': email,
            'verified': True
        }, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Verification failed: {str(e)}', 500)


@auth_bp.route('/create-account', methods=['POST'])
def create_account():
    """
    STEP 3: Create account after OTP verification
    Input: email, phone, password, confirm_password, first_name, last_name
    """
    data = request.get_json(silent=True) or {}
    
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    # Validation
    if not email or not phone or not password or not confirm_password:
        return error_response('All fields are required', 400)
    
    if not validate_email(email):
        return error_response('Invalid email format', 400)
    
    if password != confirm_password:
        return error_response('Passwords do not match', 400)
    
    if len(password) < 6:
        return error_response('Password must be at least 6 characters', 400)
    
    try:
        # Check if email already registered
        if User.query.filter_by(email=email).first():
            return error_response('Email already registered', 409)
        
        # Check if OTP was verified for this email
        verified_otp = EmailOTP.query.filter_by(
            email=email,
            is_used=True
        ).order_by(EmailOTP.created_at.desc()).first()
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)
    
    if not verified_otp:
        return error_response('Please verify your email with OTP first', 400)
    
    # Hash password
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Create user
    new_user = User(
        email=email,
        first_name=first_name if first_name else None,
        last_name=last_name if last_name else None,
        phone=phone,
        password_hash=password_hash,
        role='customer',
        is_verified=True
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=str(new_user.id))
        refresh_token = create_refresh_token(identity=str(new_user.id))
        
        return success_response('Account created successfully', {
            'user': new_user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Account creation failed: {str(e)}', 500)


@auth_bp.route('/forgot-password/send-otp', methods=['POST'])
def forgot_password_send_otp():
    """Send OTP for forgot password flow (existing users only)."""
    data = request.get_json(silent=True) or {}

    email = data.get('email', '').strip().lower()

    if not email:
        return error_response('Email is required', 400)

    if not validate_email(email):
        return error_response('Invalid email format', 400)

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return error_response('No account found with this email', 404)
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)
    except Exception:
        db.session.rollback()
        return error_response('Unable to process request right now. Please try again.', 500)

    otp_code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    new_otp = EmailOTP(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at
    )

    try:
        db.session.add(new_otp)
        db.session.commit()

        try:
            send_otp_email(
                email,
                "Your RestoM Password Reset OTP",
                f"Your password reset OTP is: {otp_code}\n\nThis code will expire in 5 minutes.\n\nIf you didn't request this, please ignore this email."
            )
        except smtplib.SMTPAuthenticationError as e:
            db.session.delete(new_otp)
            db.session.commit()
            print(f"Gmail rejected SMTP credentials for forgot-password email to {email}: {e}")
            return error_response('Gmail rejected the sender email/password. Please update MAIL_USERNAME and MAIL_PASSWORD with a valid Gmail app password.', 502)
        except Exception as e:
            db.session.delete(new_otp)
            db.session.commit()
            print(f"Error sending forgot-password email to {email}: {e}")
            return error_response('Unable to send OTP email. Please check the email configuration and try again.', 502)

        return success_response('Password reset OTP sent to your email', {
            'email': email,
            'expires_in': '5 minutes'
        }, 200)
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to send OTP: {str(e)}', 500)


@auth_bp.route('/forgot-password/reset', methods=['POST'])
def forgot_password_reset():
    """Reset password using email + OTP + new password."""
    data = request.get_json(silent=True) or {}

    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not email or not otp or not new_password or not confirm_password:
        return error_response('Email, OTP, new password and confirm password are required', 400)

    if not validate_email(email):
        return error_response('Invalid email format', 400)

    if new_password != confirm_password:
        return error_response('Passwords do not match', 400)

    if len(new_password) < 6:
        return error_response('Password must be at least 6 characters', 400)

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return error_response('No account found with this email', 404)

        otp_record = EmailOTP.query.filter_by(
            email=email,
            otp_code=otp,
            is_used=False
        ).order_by(EmailOTP.created_at.desc()).first()
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)

    if not otp_record:
        return error_response('Invalid OTP', 400)

    if datetime.utcnow() > otp_record.expires_at:
        return error_response('OTP has expired', 400)

    otp_record.is_used = True
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

    try:
        db.session.commit()
        return success_response('Password reset successful', {'email': email}, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Password reset failed: {str(e)}', 500)


@auth_bp.route('/login/send-otp', methods=['POST'])
def login_send_otp():
    """Step 1 of OTP login: validate credentials and send OTP to email."""
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return error_response('Email and password are required', 400)

    if not validate_email(email):
        return error_response('Invalid email format', 400)

    try:
        user = User.query.filter_by(email=email).first()
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return error_response('Invalid email or password', 401)

    if not user.is_active:
        return error_response('Account is deactivated', 403)

    otp_code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    new_otp = EmailOTP(email=email, otp_code=otp_code, expires_at=expires_at)

    try:
        db.session.add(new_otp)
        db.session.commit()

        try:
            send_otp_email(
                email,
                "Your RestoM Login OTP",
                f"Your login OTP is: {otp_code}\n\nThis code will expire in 5 minutes.\n\nIf you didn't request this, please ignore this email."
            )
        except smtplib.SMTPAuthenticationError as e:
            db.session.delete(new_otp)
            db.session.commit()
            print(f"Gmail rejected SMTP credentials for login OTP to {email}: {e}")
            return error_response('Unable to send OTP. Please check email configuration.', 502)
        except Exception as e:
            db.session.delete(new_otp)
            db.session.commit()
            print(f"Error sending login OTP to {email}: {e}")
            return error_response('Unable to send OTP email. Please try again.', 502)

        return success_response('OTP sent to your email', {
            'email': email,
            'expires_in': '5 minutes'
        }, 200)

    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to send OTP: {str(e)}', 500)


@auth_bp.route('/login/verify-otp', methods=['POST'])
def login_verify_otp():
    """Step 2 of OTP login: verify OTP and return JWT tokens."""
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()

    if not email or not otp:
        return error_response('Email and OTP are required', 400)

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return error_response('User not found', 404)

        otp_record = EmailOTP.query.filter_by(
            email=email,
            otp_code=otp,
            is_used=False
        ).order_by(EmailOTP.created_at.desc()).first()
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)

    if not otp_record:
        return error_response('Invalid OTP', 400)

    if datetime.utcnow() > otp_record.expires_at:
        return error_response('OTP has expired', 400)

    otp_record.is_used = True

    try:
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return success_response('Login successful', {
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Login failed: {str(e)}', 500)


# Also keep the original register and login endpoints for compatibility
@auth_bp.route('/register', methods=['POST'])
@auth_bp.route('/signup', methods=['POST'])
def register():
    """Register a new user (legacy - redirects to create-account flow)"""
    return create_account()


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return error_response('Email and password are required', 400)
    
    try:
        user = User.query.filter_by(email=email).first()
    except OperationalError:
        db.session.rollback()
        return error_response('Database connection lost. Please try again in a moment.', 503)
    
    if not user:
        return error_response('Invalid email or password', 401)
    
    if not bcrypt.check_password_hash(user.password_hash, password):
        return error_response('Invalid email or password', 401)
    
    if not user.is_active:
        return error_response('Account is deactivated', 403)
    
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return success_response('Login successful', {
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }, 200)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()
    # Convert string to int if needed for token creation
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    access_token = create_access_token(identity=user_id)
    
    return success_response('Token refreshed', {'access_token': access_token}, 200)


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """Get current logged in user info"""
    user_id = get_jwt_identity()
    # Convert string to int if needed
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        pass
    user = User.query.get(user_id)
    
    if not user:
        return error_response('User not found', 404)
    
    return success_response('User profile fetched', user.to_dict(), 200)
