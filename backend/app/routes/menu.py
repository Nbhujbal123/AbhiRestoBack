from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required
from app.models import MenuItem, Category, db
from app.middleware import admin_required
from app.utils import success_response, error_response
import os
import uuid
import re
import base64
from werkzeug.utils import secure_filename

menu_bp = Blueprint('menu', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_base64_image(data_url):
    """Save base64 data URL image to uploads and return relative URL path."""
    if not isinstance(data_url, str):
        return None

    pattern = r'^data:image/(png|jpg|jpeg|gif|webp);base64,(.+)$'
    match = re.match(pattern, data_url, re.IGNORECASE)
    if not match:
        return None

    ext = match.group(1).lower()
    if ext == 'jpeg':
        ext = 'jpg'

    try:
        image_bytes = base64.b64decode(match.group(2))
    except Exception:
        return None

    # Get absolute upload folder path
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.isabs(upload_folder):
        # Make it absolute relative to the app's root directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upload_folder = os.path.join(base_dir, upload_folder)
    
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)
    else:
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)

    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(upload_folder, filename)

    with open(filepath, 'wb') as f:
        f.write(image_bytes)

    return f"/uploads/{filename}"


@menu_bp.route('/items', methods=['GET'])
def get_menu_items():
    """
    Get all menu items (public)
    ---
    Query Parameters:
    - category_id: Filter by category
    - search: Search by name
    - is_available: Filter by availability
    - page: Page number
    - per_page: Items per page
    """
    # Get query parameters
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    is_available = request.args.get('is_available', type=bool)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    query = MenuItem.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(MenuItem.name.ilike(f'%{search}%'))
    
    if is_available is not None:
        query = query.filter_by(is_available=is_available)
    
    # Order by featured first, then by name
    query = query.order_by(MenuItem.is_featured.desc(), MenuItem.name)
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return success_response('Menu items fetched', {
        'items': [item.to_dict() for item in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }, 200)


@menu_bp.route('', methods=['GET'])
def get_menu_items_root():
    """Get all menu items (public) - root endpoint"""
    return get_menu_items()


@menu_bp.route('/items/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    """
    Get single menu item (public)
    """
    item = MenuItem.query.get(item_id)
    
    if not item:
        return error_response('Menu item not found', 404)
    
    return success_response('Menu item fetched', item.to_dict(), 200)


@menu_bp.route('/<int:item_id>', methods=['GET'])
def get_menu_item_root(item_id):
    """Get single menu item (public) - root endpoint"""
    return get_menu_item(item_id)


@menu_bp.route('/items/featured', methods=['GET'])
def get_featured_items():
    """
    Get featured menu items (public)
    """
    items = MenuItem.query.filter_by(is_featured=True, is_available=True).limit(10).all()
    
    return success_response('Featured items fetched', [item.to_dict() for item in items], 200)


# Admin routes
@menu_bp.route('/admin/items', methods=['GET'])
@jwt_required()
@admin_required()
def admin_get_menu_items():
    """Get all menu items for admin"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = MenuItem.query.order_by(MenuItem.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return success_response('Menu items fetched', {
        'items': [item.to_dict() for item in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }, 200)


@menu_bp.route('/admin/items', methods=['POST'])
@jwt_required()
@admin_required()
def admin_create_menu_item():
    """
    Create new menu item (admin only)
    ---
    Request Body:
    {
        "name": "Butter Chicken",
        "description": "Creamy tomato-based curry",
        "price": 350.00,
        "category_id": 1,
        "food_type": "non-veg",
        "is_available": true,
        "is_featured": false,
        "preparation_time": 20
    }
    """
    data = request.get_json(silent=True) or {}
    
    # Validate required fields
    required_fields = ['name', 'price', 'category_id']
    for field in required_fields:
        if not data.get(field):
            return error_response(f'{field} is required', 400)
    
    # Check if category exists
    category = Category.query.get(data['category_id'])
    if not category:
        return error_response('Category not found', 404)

    if float(data['price']) <= 0:
        return error_response('price must be greater than 0', 400)
    
    image_url = data.get('image_url')
    if isinstance(image_url, str) and image_url.startswith('data:image/'):
        saved_image_url = save_base64_image(image_url)
        if not saved_image_url:
            return error_response('Invalid image data', 400)
        image_url = saved_image_url

    try:
        new_item = MenuItem(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            price=data['price'],
            category_id=data['category_id'],
            image_url=image_url,
            food_type=data.get('food_type', 'veg'),
            is_available=data.get('is_available', True),
            is_featured=data.get('is_featured', False),
            preparation_time=data.get('preparation_time', 15)
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return success_response('Menu item created successfully', new_item.to_dict(), 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create menu item: {str(e)}', 500)


@menu_bp.route('/admin/items/<int:item_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def admin_update_menu_item(item_id):
    """
    Update menu item (admin only)
    """
    item = MenuItem.query.get(item_id)
    
    if not item:
        return error_response('Menu item not found', 404)
    
    data = request.get_json(silent=True) or {}
    
    # Update fields
    if 'name' in data:
        item.name = data['name'].strip()
    if 'description' in data:
        item.description = data['description'].strip()
    if 'price' in data:
        item.price = data['price']
    if 'category_id' in data:
        # Check if category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return error_response('Category not found', 404)
        item.category_id = data['category_id']
    if 'image_url' in data:
        image_url = data['image_url']
        if isinstance(image_url, str) and image_url.startswith('data:image/'):
            saved_image_url = save_base64_image(image_url)
            if not saved_image_url:
                return error_response('Invalid image data', 400)
            image_url = saved_image_url
        item.image_url = image_url
    if 'food_type' in data:
        item.food_type = data['food_type']
    if 'is_available' in data:
        item.is_available = data['is_available']
    if 'is_featured' in data:
        item.is_featured = data['is_featured']
    if 'preparation_time' in data:
        item.preparation_time = data['preparation_time']
    
    try:
        db.session.commit()
        return success_response('Menu item updated successfully', item.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update menu item: {str(e)}', 500)


@menu_bp.route('/admin/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def admin_delete_menu_item(item_id):
    """
    Delete menu item (admin only)
    """
    item = MenuItem.query.get(item_id)
    
    if not item:
        return error_response('Menu item not found', 404)
    
    try:
        db.session.delete(item)
        db.session.commit()
        return success_response('Menu item deleted successfully', None, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete menu item: {str(e)}', 500)


@menu_bp.route('/admin/items/<int:item_id>/image', methods=['POST'])
@jwt_required()
@admin_required()
def admin_upload_item_image(item_id):
    """
    Upload image for menu item (admin only)
    """
    item = MenuItem.query.get(item_id)
    
    if not item:
        return error_response('Menu item not found', 404)
    
    if 'image' not in request.files:
        return error_response('No image file provided', 400)
    
    file = request.files['image']
    
    if file.filename == '':
        return error_response('No image file selected', 400)
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4()}.{ext}"
        
        # Create uploads directory if not exists
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if upload_folder and not os.path.isabs(upload_folder):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_folder = os.path.join(base_dir, upload_folder)
        
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        filepath = os.path.join(upload_folder, new_filename)
        file.save(filepath)
        
        # Update item image URL
        item.image_url = f"/uploads/{new_filename}"
        db.session.commit()
        
        return success_response('Image uploaded successfully', {'image_url': item.image_url}, 200)
    
    return error_response('Invalid file type', 400)
