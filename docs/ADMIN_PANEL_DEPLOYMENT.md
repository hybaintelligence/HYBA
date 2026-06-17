# Admin Panel Deployment Guide

## Overview

The HYBA platform now includes a complete admin panel for user management with role-based access control (RBAC). This guide covers deployment, initial setup, and usage.

## Features

- **User Management**: Create, read, update, and delete users
- **Role-Based Access Control**: Admin, Operator, Analyst, Miner roles
- **Audit Logging**: All admin actions are logged to the audit trail
- **Security**: Argon2id password hashing, fail-closed authentication
- **Database-Backed**: Users stored in SQLite/PostgreSQL with fallback to env var credentials

## Architecture

### Backend Components

1. **Database Models** (`python_backend/consciousness_db/models.py`)
   - `User`: User accounts with username, email, password_hash, role, is_active
   - `AuditLog`: Audit trail for all administrative actions
   - `UserRole`: Enum for admin, operator, analyst, miner roles

2. **Admin API** (`python_backend/hyba_genesis_api/api/admin.py`)
   - `GET /api/admin/users` - List users with search and pagination
   - `GET /api/admin/users/{id}` - Get specific user
   - `POST /api/admin/users` - Create new user
   - `PUT /api/admin/users/{id}` - Update user
   - `DELETE /api/admin/users/{id}` - Delete user
   - `GET /api/admin/audit-logs` - View audit trail
   - `GET /api/admin/stats` - Admin statistics

3. **Authentication** (`python_backend/hyba_genesis_api/api/auth.py`)
   - Updated to support database users with fallback to env var credentials
   - Maintains backward compatibility with existing `HYBA_OPERATOR_CREDENTIALS`

### Frontend Components

1. **AdminPanel** (`src/components/AdminPanel.tsx`)
   - User list with search and filtering
   - Create user modal with form validation
   - Edit user modal with role assignment
   - Delete user with confirmation
   - Admin statistics dashboard
   - Real-time feedback on operations

2. **Navigation** (`src/App.tsx`)
   - Admin button in header (visible only to admin users)
   - Toggle between dashboard and admin panel
   - Role-based access control

## Deployment Steps

### 1. Database Initialization

The database tables are automatically created on backend startup via `init_db()` in `hyba_genesis_api/database.py`. No manual migration required.

### 2. Create Initial Admin User

Run the seed script to create the first admin user:

```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
python3 python_backend/scripts/seed_admin_user.py --username admin --password secure_password_123 --email admin@hyba.ai
```

**Note**: Ensure `argon2-cffi` is installed in your Python environment:
```bash
pip install argon2-cffi
```

### 3. Configure Environment Variables

The admin panel works with both database users and environment variable credentials. For production, use database users:

```bash
# Optional: Keep env var fallback for initial admin
export HYBA_OPERATOR_CREDENTIALS="admin:$argon2id$v=19$m=65536,t=3,p=4$...:admin"
```

### 4. Start Backend

```bash
npm run backend:start
```

The backend will:
- Initialize database tables
- Register admin router at `/api/admin/*`
- Enable database authentication
- Start on `http://127.0.0.1:3001`

### 5. Start Frontend

```bash
npm run dev
```

The frontend will:
- Load AdminPanel component
- Show admin button for admin users
- Proxy `/api` requests to backend

## Usage

### Accessing Admin Panel

1. Login as an admin user
2. Click the "Admin" button in the header (shield icon)
3. Navigate between dashboard and admin panel

### Creating Users

1. Click "Create User" button
2. Fill in username, email (optional), password, and role
3. Click "Create User"
4. User is created with audit log entry

### Managing Users

- **Edit**: Click edit icon to modify user details, role, or status
- **Delete**: Click trash icon to remove user (with confirmation)
- **Search**: Use search box to filter by username or email
- **Refresh**: Click refresh button to reload user list

### Role Permissions

| Role | Permissions |
|------|-------------|
| **admin** | Full access to admin panel, can create/edit/delete users |
| **operator** | Can view dashboard, manage pools, no admin access |
| **analyst** | Read-only access to telemetry and analytics |
| **miner** | Basic mining operations, no admin access |

## Security Features

### Password Security

- Argon2id hashing (memory-hard, GPU-resistant)
- Minimum 8 character password requirement
- Password never stored in plaintext

### Access Control

- Admin-only endpoints protected by `require_admin()` middleware
- Self-protection: Admins cannot deactivate/delete themselves
- Role changes prevented on own account

### Audit Trail

All admin actions are logged:
- User creation, updates, deletions
- Timestamp, actor username, target details
- IP address tracking
- Queryable via `/api/admin/audit-logs`

## API Endpoints

### User Management

```bash
# List users
GET /api/admin/users?skip=0&limit=50&search=query
Authorization: Bearer <token>

# Get user
GET /api/admin/users/{id}
Authorization: Bearer <token>

# Create user
POST /api/admin/users
Content-Type: application/json
Authorization: Bearer <token>
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password",
  "role": "operator"
}

# Update user
PUT /api/admin/users/{id}
Content-Type: application/json
Authorization: Bearer <token>
{
  "email": "newemail@example.com",
  "role": "admin",
  "is_active": true
}

# Delete user
DELETE /api/admin/users/{id}
Authorization: Bearer <token>
```

### Admin Statistics

```bash
GET /api/admin/stats
Authorization: Bearer <token>

Response:
{
  "total_users": 10,
  "active_users": 8,
  "admin_users": 2,
  "timestamp": "2024-06-17T14:00:00Z"
}
```

## Troubleshooting

### Admin Button Not Showing

- Verify user role is "admin" in database
- Check JWT token includes "admin" in roles array
- Ensure token is valid and not expired

### Database Connection Errors

- Check `DATABASE_URL` environment variable
- Verify SQLite file permissions or PostgreSQL connection
- Ensure `init_db()` is called on backend startup

### Authentication Fails

- Verify password hashing matches Argon2id format
- Check user is active (`is_active = true`)
- Review auth logs for specific error messages

## Production Considerations

### Security

1. **Change Default Password**: Immediately change the default admin password
2. **Use HTTPS**: Enable TLS for all API communications
3. **Rate Limiting**: Backend includes rate limiting (120 req/min default)
4. **Input Validation**: All inputs validated via Pydantic schemas
5. **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

### Scalability

- Database supports both SQLite (development) and PostgreSQL (production)
- Pagination built into user list endpoint
- Audit logs can be archived periodically

### Monitoring

- Monitor `/api/admin/stats` for user growth
- Review audit logs regularly for suspicious activity
- Track failed authentication attempts

## Backup and Recovery

### Database Backup

```bash
# SQLite
cp data/metrics.db data/metrics.db.backup

# PostgreSQL
pg_dump hyba_db > hyba_backup.sql
```

### User Recovery

If admin user is locked out:
1. Use env var credential fallback
2. Direct database update to reset password
3. Re-run seed script with new credentials

## Testing

### Manual Testing

1. Create test user via admin panel
2. Login as test user
3. Verify role-based access (admin button visibility)
4. Test user CRUD operations
5. Check audit log entries

### API Testing

```bash
# Test admin endpoint
curl -H "Authorization: Bearer <token>" \
  http://localhost:3001/api/admin/users

# Test RBAC (should fail for non-admin)
curl -H "Authorization: Bearer <operator_token>" \
  http://localhost:3001/api/admin/users
```

## Support

For issues or questions:
1. Check backend logs: `python_backend/logs/`
2. Review audit logs via admin panel
3. Verify database connectivity
4. Check environment variable configuration

## Summary

The admin panel provides a complete user management system with:
- ✅ Database-backed user storage
- ✅ Role-based access control
- ✅ Secure password hashing
- ✅ Comprehensive audit logging
- ✅ Modern React UI with real-time updates
- ✅ Backward compatibility with env var credentials
- ✅ Production-ready security features

The system is now ready for production deployment with full user management capabilities.
