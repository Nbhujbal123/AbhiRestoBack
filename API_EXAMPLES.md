# Restaurant Management Backend – Example API Responses

Base URL: `http://localhost:5000`

## 1) Signup
`POST /api/auth/signup`

Request:
```json
{
  "email": "john@example.com",
  "password": "john12345",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+919876543210",
  "role": "customer"
}
```

Success (201):
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user": {
      "id": 1,
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+919876543210",
      "address": "",
      "role": "customer",
      "is_active": true,
      "created_at": "2026-02-28T11:00:00",
      "updated_at": "2026-02-28T11:00:00"
    },
    "access_token": "<jwt_access_token>",
    "refresh_token": "<jwt_refresh_token>"
  }
}
```

## 2) Login
`POST /api/auth/login`

Request:
```json
{
  "email": "john@example.com",
  "password": "john12345"
}
```

Success (200):
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+919876543210",
      "address": "",
      "role": "customer",
      "is_active": true,
      "created_at": "2026-02-28T11:00:00",
      "updated_at": "2026-02-28T11:00:00"
    },
    "access_token": "<jwt_access_token>",
    "refresh_token": "<jwt_refresh_token>"
  }
}
```

## 3) Add Category (Admin)
`POST /api/categories/admin`

Headers:
`Authorization: Bearer <admin_access_token>`

Request:
```json
{
  "name": "Main Course",
  "description": "Main dishes",
  "display_order": 1
}
```

## 4) Add Menu Item (Admin)
`POST /api/menu/admin/items`

Request:
```json
{
  "name": "Paneer Butter Masala",
  "description": "Creamy paneer curry",
  "price": 280,
  "category_id": 1,
  "food_type": "veg",
  "is_available": true
}
```

## 5) Add to Cart
`POST /api/cart/add`

Request:
```json
{
  "menu_item_id": 1,
  "quantity": 2
}
```

## 6) Create Order from Cart
`POST /api/orders/create`

Request:
```json
{
  "delivery_address": "Sector 12, Noida",
  "delivery_phone": "+919876543210",
  "notes": "Call before delivery",
  "payment_method": "upi"
}
```

## 7) View Cart
`GET /api/cart`

Success (200):
```json
{
  "success": true,
  "message": "Cart fetched successfully",
  "data": {
    "items": [],
    "item_count": 0,
    "total": 0.0
  }
}
```

## 8) Admin Dashboard
`GET /api/admin/dashboard`

Success (200):
```json
{
  "success": true,
  "message": "Dashboard stats fetched",
  "data": {
    "total_users": 25,
    "total_orders": 80,
    "total_revenue": 34000.0,
    "today_orders": 5,
    "today_revenue": 2200.0,
    "orders_by_status": {
      "pending": 2,
      "confirmed": 4,
      "preparing": 1,
      "out_for_delivery": 3,
      "delivered": 68,
      "cancelled": 2
    },
    "recent_orders": []
  }
}
```

## Common Error Format
```json
{
  "success": false,
  "message": "Invalid email or password"
}
```
