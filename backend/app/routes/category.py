from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.models import Category, db
from app.middleware import admin_required
from app.utils import success_response, error_response

category_bp = Blueprint('category', __name__)


@category_bp.route('', methods=['GET'])
def get_categories():
    """
    Get all categories (public)
    ---
    Query Parameters:
    - is_active: Filter by active status
    """
    is_active = request.args.get('is_active', type=bool)
    
    query = Category.query
    
    if is_active is not None:
        query = query.filter_by(is_active=is_active)
    
    categories = query.order_by(Category.display_order, Category.name).all()
    
    return success_response('Categories fetched', [category.to_dict() for category in categories], 200)


@category_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """
    Get single category (public)
    """
    category = Category.query.get(category_id)
    
    if not category:
        return error_response('Category not found', 404)
    
    return success_response('Category fetched', category.to_dict(), 200)


# Admin routes
@category_bp.route('/admin', methods=['GET'])
@jwt_required()
@admin_required()
def admin_get_categories():
    """Get all categories for admin"""
    categories = Category.query.order_by(Category.display_order, Category.name).all()
    
    return success_response('Categories fetched', [category.to_dict() for category in categories], 200)


@category_bp.route('/admin', methods=['POST'])
@jwt_required()
@admin_required()
def admin_create_category():
    """
    Create new category (admin only)
    ---
    Request Body:
    {
        "name": "Main Course",
        "description": "Main dishes",
        "display_order": 2
    }
    """
    data = request.get_json(silent=True) or {}
    
    if not data.get('name'):
        return error_response('Name is required', 400)
    
    # Check if category name already exists
    existing = Category.query.filter_by(name=data['name']).first()
    if existing:
        return error_response('Category with this name already exists', 400)
    
    try:
        new_category = Category(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            display_order=data.get('display_order', 0)
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        return success_response('Category created successfully', new_category.to_dict(), 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create category: {str(e)}', 500)


@category_bp.route('/admin/<int:category_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def admin_update_category(category_id):
    """
    Update category (admin only)
    """
    category = Category.query.get(category_id)
    
    if not category:
        return error_response('Category not found', 404)
    
    data = request.get_json(silent=True) or {}
    
    # Check if new name already exists
    if 'name' in data and data['name'].strip() != category.name:
        existing = Category.query.filter_by(name=data['name']).first()
        if existing:
            return error_response('Category with this name already exists', 400)
        category.name = data['name'].strip()
    
    if 'description' in data:
        category.description = data['description'].strip()
    if 'display_order' in data:
        category.display_order = data['display_order']
    if 'is_active' in data:
        category.is_active = data['is_active']
    if 'image_url' in data:
        category.image_url = data['image_url']
    
    try:
        db.session.commit()
        return success_response('Category updated successfully', category.to_dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update category: {str(e)}', 500)


@category_bp.route('/admin/<int:category_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def admin_delete_category(category_id):
    """
    Delete category (admin only)
    """
    category = Category.query.get(category_id)
    
    if not category:
        return error_response('Category not found', 404)
    
    # Check if category has menu items
    if category.menu_items.count() > 0:
        return error_response('Cannot delete category with menu items. Please delete or move menu items first.', 400)
    
    try:
        db.session.delete(category)
        db.session.commit()
        return success_response('Category deleted successfully', None, 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete category: {str(e)}', 500)
