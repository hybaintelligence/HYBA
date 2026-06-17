# HYBA Admin Panel - Complete Guide

## Quick Summary

✅ **Status**: Production-ready admin panel with full user management  
✅ **Features**: Create, read, update, delete users with role-based access control  
✅ **Security**: Argon2id password hashing, JWT authentication, audit logging  
✅ **UI**: Modern React interface with search, pagination, and real-time statistics

---

## Table of Contents

1. [Features](#features)
2. [Screenshots](#screenshots)
3. [Quick Start](#quick-start)
4. [User Roles](#user-roles)
5. [API Endpoints](#api-endpoints)
6. [Security Features](#security-features)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Features

### User Management
- ✅ **Create users** - Add new operators with username, email, password, and role
- ✅ **Edit users** - Update email, role, password, or active status
- ✅ **Delete users** - Remove users with confirmation dialog
- ✅ **Search users** - Filter by username or email
- ✅ **View details** - Last login, creation date, creator

### Dashboard
- ✅ **Total users count** - See all registered users
- ✅ **Active users count** - Track active accounts
- ✅ **Admin users count** - Monitor admin accounts
- ✅ **Real-time updates** - Statistics refresh after changes

### Security
- ✅ **Role-based access** - Only admins can access admin panel
- ✅ **Self-protection** - Cannot delete or demote own account
- ✅ **Audit logging** - All actions tracked with actor, timestamp, and details
- ✅ **Password security** - Argon2id hashing (memory-hard, side-channel resistant)
- ✅ **JWT authentication** - Secure token-based auth

---

## Screenshots

### Admin Panel Main View
```
┌─────────────────────────────────────────────────────────────┐
│  User Management                  [+ Create User]           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Total Users    Active Users    Admin Users                │
│     15             12              3                        │
│                                                             │
│  🔍 Search users by username or email...     [Refresh]     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ User          │ Role     │ Status  │ Actions         │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ admin         │ Admin    │ Active  │ [Edit]          │  │
│  │ operator_1    │ Operator │ Active  │ [Edit] [Delete] │  │
│  │ analyst_2     │ Analyst  │ Active  │ [Edit] [Delete] │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Create User Modal
```
┌─────────────────────────────────────┐
│  Create New User              [✕]  │
├─────────────────────────────────────┤
│                                     │
│  Username *                         │
│  [_________________________]        │
│                                     │
│  Email (optional)                   │
│  [_________________________]        │
│                                     │
│  Password *                         │
│  [_________________________]        │
│                                     │
│  Role                               │
│  [Operator             ▼]          │
│                                     │
│  [Cancel]        [Create User]     │
└─────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Node.js 22+
- Python 3.12+
- PostgreSQL or SQLite

### Step 1: Install Dependencies

```bash
# Frontend dependencies
npm install

# Backend dependencies
cd python_backend
pip install -r requirements.txt
pip install argon2-cffi  # Required for password hashing
```

### Step 2: Create Admin User

```bash
# Create default admin (username: admin, password: admin123456)
python3 python_backend/scripts/seed_admin_user.py

# Or create custom admin
python3 python_backend/scripts/seed_admin_user.py \
  --username your_admin \
  --password YourSecurePassword2024 \
  --email admin@hyba.ai
```

### Step 3: Start Services

```bash
# Terminal 1: Start backend (port 3001)
npm run backend:start

# Terminal 2: Start frontend (port 3000)
npm run dev
```

### Step 4: Access Admin Panel

1. Open browser to `http://localhost:3000`
2. Login with admin credentials
3. Click **"Admin"** button in header (top-right corner)
4. Create additional users as needed

---

## User Roles

### 1. Admin
**Full platform administration**
- ✅ Access admin panel
- ✅ Create, edit, delete users
- ✅ View audit logs
- ✅ Change user roles
- ✅ All operator/analyst/miner permissions

### 2. Operator
**Mining operations control**
- ✅ Start/stop mining
- ✅ Configure pools
- ✅ View telemetry dashboards
- ✅ Manage mining jobs
- ❌ No admin panel access

### 3. Analyst
**Read-only analytics**
- ✅ View telemetry and reports
- ✅ Export data
- ✅ Access dashboards
- ❌ No control plane access
- ❌ No admin panel access

### 4. Miner
**Mining-specific access**
- ✅ View own mining stats
- ✅ Limited telemetry access
- ❌ No operator controls
- ❌ No admin panel access

---

## API Endpoints

### List Users
```http
GET /api/admin/users?skip=0&limit=50&search=operator
Authorization: Bearer <jwt_token>

Response 200:
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@hyba.ai",
      "role": "admin",
      "is_active": true,
      "created_at": "2024-06-17T10:00:00Z",
      "updated_at": "2024-06-17T10:00:00Z",
      "last_login": "2024-06-17T10:30:00Z",
      "created_by": "system_seed"
    }
  ],
  "total": 1
}
```

### Get User
```http
GET /api/admin/users/{user_id}
Authorization: Bearer <jwt_token>

Response 200:
{
  "id": 1,
  "username": "operator_1",
  "email": "operator@hyba.ai",
  "role": "operator",
  "is_active": true,
  ...
}
```

### Create User
```http
POST /api/admin/users
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "username": "new_operator",
  "email": "new@hyba.ai",
  "password": "SecurePass123",
  "role": "operator"
}

Response 201:
{
  "id": 2,
  "username": "new_operator",
  "email": "new@hyba.ai",
  "role": "operator",
  "is_active": true,
  "created_at": "2024-06-17T11:00:00Z",
  "created_by": "admin"
}
```

### Update User
```http
PUT /api/admin/users/{user_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "email": "updated@hyba.ai",
  "role": "analyst",
  "is_active": true
}

Response 200:
{
  "id": 2,
  "username": "operator_1",
  "email": "updated@hyba.ai",
  "role": "analyst",
  ...
}
```

### Delete User
```http
DELETE /api/admin/users/{user_id}
Authorization: Bearer <jwt_token>

Response 204: No Content
```

### Get Statistics
```http
GET /api/admin/stats
Authorization: Bearer <jwt_token>

Response 200:
{
  "total_users": 15,
  "active_users": 12,
  "admin_users": 3,
  "timestamp": "2024-06-17T12:00:00Z"
}
```

### Get Audit Logs
```http
GET /api/admin/audit-logs?skip=0&limit=100
Authorization: Bearer <jwt_token>

Response 200:
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2024-06-17T11:00:00Z",
      "actor_username": "admin",
      "action": "user_created",
      "target_type": "user",
      "target_id": "2",
      "details": {
        "username": "new_operator",
        "role": "operator"
      },
      "ip_address": "192.168.1.100"
    }
  ],
  "total": 1
}
```

---

## Security Features

### Password Security
- **Argon2id hashing** - Memory-hard, side-channel resistant
- **Minimum 8 characters** - Enforced on frontend and backend
- **Salt management** - Automatic salt generation and storage
- **No password exposure** - Never logged or returned in API responses

### Access Control
- **JWT bearer tokens** - Secure token-based authentication
- **Admin role required** - All `/api/admin/*` endpoints require admin role
- **Token validation** - Every request validated for authenticity
- **Token expiration** - Configurable token lifetime

### Self-Protection
- **Cannot delete self** - Prevents accidental account deletion
- **Cannot change own role** - Prevents privilege escalation
- **Cannot deactivate self** - Ensures admin access continuity
- **Confirmation dialogs** - Required for destructive actions

### Audit Trail
- **All actions logged** - Create, update, delete tracked
- **Actor identification** - Username of admin performing action
- **Timestamp tracking** - UTC timestamps for all events
- **IP address capture** - Source IP recorded when available
- **Immutable logs** - Audit trail is append-only

### Input Validation
- **Pydantic models** - Request validation with type checking
- **Email validation** - RFC 5322 compliant email validation
- **Username constraints** - 3-100 characters, uniqueness enforced
- **Password constraints** - 8-128 characters
- **Role validation** - Enum validation (admin, operator, analyst, miner)
- **SQL injection protection** - SQLAlchemy ORM prevents injection

---

## Deployment

### Development Environment

```bash
# Use default SQLite database
export HYBA_DATABASE_URL="sqlite:///./hyba.db"

# Start services
npm run backend:start
npm run dev
```

### Production Environment

```bash
# Use PostgreSQL database
export HYBA_DATABASE_URL="postgresql://user:pass@host:5432/hyba"

# Set secure JWT secret (minimum 32 random bytes)
export JWT_SECRET="$JWT_SECRET"

# Configure CORS (no wildcards in production)
export HYBA_CORS_ORIGINS="https://app.hyba.ai,https://console.hyba.ai"

# Change default admin password immediately after deployment
python3 python_backend/scripts/seed_admin_user.py \
  --username admin \
  --password YourProductionPassword2024

# Start with production settings
npm run build
npm run start
```

### Production Checklist

- [ ] Change default admin password
- [ ] Set secure JWT_SECRET (32+ random bytes)
- [ ] Configure production database (PostgreSQL)
- [ ] Set explicit CORS origins (no wildcards)
- [ ] Enable HTTPS (required for production)
- [ ] Set up database backups (daily recommended)
- [ ] Configure audit log retention policy
- [ ] Review and test role-based access
- [ ] Test failover scenarios
- [ ] Set up monitoring and alerts

---

## Troubleshooting

### Problem: Admin button not visible

**Cause**: User does not have admin role

**Solution**:
```bash
# Check user role in database
sqlite3 hyba.db "SELECT username, role FROM users;"

# Update user role to admin
sqlite3 hyba.db "UPDATE users SET role='admin' WHERE username='your_username';"
```

### Problem: Cannot create user (409 Conflict)

**Cause**: Username or email already exists

**Solution**:
- Use a different username
- Check existing users in database
- Delete duplicate user if appropriate

### Problem: Password hashing error

**Cause**: argon2-cffi not installed

**Solution**:
```bash
pip install argon2-cffi
```

### Problem: Admin panel returns 403 Forbidden

**Cause**: JWT token missing or invalid, or user is not admin

**Solution**:
1. Check browser console for token
2. Verify JWT_SECRET matches between frontend and backend
3. Verify user role is "admin"
4. Logout and login again to refresh token

### Problem: Database table does not exist

**Cause**: Database not initialized

**Solution**:
```bash
# Backend auto-initializes on startup, but you can force it:
python3 -c "from hyba_genesis_api.database import init_db; init_db()"
```

### Problem: Cannot delete user

**Cause**: Trying to delete own account (self-protection)

**Solution**:
- Login as a different admin user
- Use that admin account to delete the target user

---

## Support

For issues, questions, or feature requests:
- Check validation script: `python3 scripts/validate_admin_panel_complete.py`
- Review architecture diagram: `docs/ADMIN_PANEL_ARCHITECTURE.md`
- Read audit report: `docs/ADMIN_PANEL_COMPLETE_AUDIT.md`

---

## Summary

The HYBA admin panel is a **complete, production-ready** user management system with:

✅ Full CRUD operations (create, read, update, delete)  
✅ Role-based access control (4 roles: admin, operator, analyst, miner)  
✅ Secure password handling (Argon2id hashing)  
✅ Comprehensive audit trail (all actions logged)  
✅ Modern, responsive UI (React + TypeScript)  
✅ RESTful backend API (FastAPI + SQLAlchemy)  
✅ Database-backed storage (SQLite/PostgreSQL)  
✅ Self-protection mechanisms (cannot delete self)  
✅ Search and pagination (scalable for large user bases)  
✅ Real-time statistics dashboard

**Ready for internal deployment** with proper security configurations.

---

**Last Updated**: 2026-06-17  
**Version**: 2.0.1  
**Status**: ✅ Production Ready
