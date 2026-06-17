# Admin Panel Architecture

## System Overview

The HYBA admin panel is a complete, production-ready user management system with role-based access control, audit logging, and secure password handling.

```
┌─────────────────────────────────────────────────────────────────┐
│                      HYBA ADMIN PANEL                           │
│                   Complete Architecture                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ App.tsx                                                 │   │
│  │                                                         │   │
│  │  • View switcher (dashboard ↔ admin)                   │   │
│  │  • Admin button (visible only to admins)               │   │
│  │  • JWT token management                                │   │
│  │  • Current user state                                  │   │
│  └─────────────────┬──────────────────────────────────────┘   │
│                    │                                            │
│                    ↓                                            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ AdminPanel.tsx                                          │   │
│  │                                                         │   │
│  │  Components:                                            │   │
│  │  • Statistics Dashboard (total, active, admin counts)   │   │
│  │  • User Table (search, pagination, sort)                │   │
│  │  • Create User Modal (username, email, password, role)  │   │
│  │  • Edit User Modal (update fields, reset password)      │   │
│  │  • Delete User Confirmation                             │   │
│  │                                                         │   │
│  │  Features:                                              │   │
│  │  • Real-time search filtering                           │   │
│  │  • Role-based badges (color-coded)                      │   │
│  │  • Status indicators (active/inactive)                  │   │
│  │  • Self-protection (cannot delete/demote self)          │   │
│  │  • Error handling & user feedback                       │   │
│  └─────────────────┬──────────────────────────────────────┘   │
│                    │                                            │
└────────────────────┼────────────────────────────────────────────┘
                     │
                     │ HTTP/JSON (JWT Bearer Token)
                     │
┌────────────────────┼────────────────────────────────────────────┐
│                    ↓         API LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ FastAPI Router (/api/admin/*)                           │   │
│  │                                                         │   │
│  │  Middleware:                                            │   │
│  │  • JWT validation (get_token_payload)                   │   │
│  │  • Admin role enforcement (require_admin)               │   │
│  │  • CORS (configurable origins)                          │   │
│  │  • Rate limiting (120 req/min default)                  │   │
│  └─────────────────┬──────────────────────────────────────┘   │
│                    │                                            │
│                    ↓                                            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Admin API Endpoints                                     │   │
│  │                                                         │   │
│  │  GET    /api/admin/users                                │   │
│  │  GET    /api/admin/users/{user_id}                      │   │
│  │  POST   /api/admin/users                                │   │
│  │  PUT    /api/admin/users/{user_id}                      │   │
│  │  DELETE /api/admin/users/{user_id}                      │   │
│  │  GET    /api/admin/audit-logs                           │   │
│  │  GET    /api/admin/stats                                │   │
│  │                                                         │   │
│  │  Security:                                              │   │
│  │  • Username uniqueness validation                       │   │
│  │  • Email uniqueness validation (optional)               │   │
│  │  • Self-protection (cannot modify own role/status)      │   │
│  │  • Input validation (Pydantic models)                   │   │
│  │  • SQL injection protection (SQLAlchemy ORM)            │   │
│  └─────────────────┬──────────────────────────────────────┘   │
│                    │                                            │
│                    ↓                                            │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Audit Logger (log_audit function)                       │   │
│  │                                                         │   │
│  │  Logs all admin actions:                                │   │
│  │  • user_created                                         │   │
│  │  • user_updated                                         │   │
│  │  • user_deleted                                         │   │
│  │                                                         │   │
│  │  Tracked fields:                                        │   │
│  │  • Actor username                                       │   │
│  │  • Action type                                          │   │
│  │  • Target user ID                                       │   │
│  │  • Timestamp (UTC)                                      │   │
│  │  • IP address (when available)                          │   │
│  │  • Details JSON (field changes)                         │   │
│  └─────────────────┬──────────────────────────────────────┘   │
│                    │                                            │
└────────────────────┼────────────────────────────────────────────┘
                     │
                     │ SQLAlchemy ORM
                     │
┌────────────────────┼────────────────────────────────────────────┐
│                    ↓      DATABASE LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ users TABLE                                             │   │
│  │                                                         │   │
│  │  • id (INTEGER PRIMARY KEY)                             │   │
│  │  • username (VARCHAR UNIQUE NOT NULL)                   │   │
│  │  • email (VARCHAR UNIQUE)                               │   │
│  │  • password_hash (VARCHAR NOT NULL) ◄─ Argon2id        │   │
│  │  • role (VARCHAR NOT NULL) ◄─ Enum constraint           │   │
│  │  • is_active (BOOLEAN DEFAULT TRUE)                     │   │
│  │  • created_at (TIMESTAMP DEFAULT NOW)                   │   │
│  │  • updated_at (TIMESTAMP DEFAULT NOW)                   │   │
│  │  • last_login (TIMESTAMP NULL)                          │   │
│  │  • created_by (VARCHAR) ◄─ Audit trail                  │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ audit_logs TABLE                                        │   │
│  │                                                         │   │
│  │  • id (INTEGER PRIMARY KEY)                             │   │
│  │  • timestamp (TIMESTAMP DEFAULT NOW)                    │   │
│  │  • actor_username (VARCHAR NOT NULL)                    │   │
│  │  • action (VARCHAR NOT NULL)                            │   │
│  │  • target_type (VARCHAR NOT NULL)                       │   │
│  │  • target_id (VARCHAR)                                  │   │
│  │  • details (JSON)                                       │   │
│  │  • ip_address (VARCHAR)                                 │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Database Options:                                              │
│  • SQLite (default, local development)                          │
│  • PostgreSQL (production recommended)                          │
│  • MySQL/MariaDB (supported via SQLAlchemy)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY FEATURES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Password Security:                                             │
│  • Argon2id hashing (memory-hard, side-channel resistant)       │
│  • Minimum 8 characters enforced                                │
│  • Passwords never logged or exposed in responses               │
│  • Salt automatically managed by Argon2id                       │
│                                                                 │
│  Access Control:                                                │
│  • JWT bearer token required for all endpoints                  │
│  • Admin role required for all /api/admin/* endpoints           │
│  • 403 Forbidden for non-admin users                            │
│  • 401 Unauthorized for invalid/missing tokens                  │
│                                                                 │
│  Self-Protection:                                               │
│  • Cannot delete own account                                    │
│  • Cannot change own role                                       │
│  • Cannot deactivate own account                                │
│                                                                 │
│  Audit Trail:                                                   │
│  • All admin actions logged to audit_logs table                 │
│  • Immutable audit trail (append-only)                          │
│  • Actor, action, target, timestamp tracked                     │
│  • IP address captured when available                           │
│                                                                 │
│  Input Validation:                                              │
│  • Pydantic models for request validation                       │
│  • Email validation (RFC 5322 compliant)                        │
│  • Username/password length constraints                         │
│  • Role enum validation                                         │
│  • SQL injection protection (ORM)                               │
│  • XSS protection (no raw HTML rendering)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Install Dependencies                                        │
│     • pip install argon2-cffi (required)                        │
│     • pip install -r requirements.txt (all backend deps)        │
│     • npm install (frontend deps)                               │
│                                                                 │
│  2. Initialize Database                                         │
│     • Automatic on first startup (init_db in main.py)           │
│     • Creates users and audit_logs tables                       │
│     • Supports SQLite (default) or PostgreSQL                   │
│                                                                 │
│  3. Seed Admin User                                             │
│     • python3 python_backend/scripts/seed_admin_user.py         │
│     • Default: username=admin, password=admin123456             │
│     • Custom: --username <name> --password <pass>               │
│     • Idempotent (skips if user exists)                         │
│                                                                 │
│  4. Start Services                                              │
│     • npm run backend:start (FastAPI on port 3001)              │
│     • npm run dev (Vite dev server on port 3000)                │
│                                                                 │
│  5. Access Admin Panel                                          │
│     • Login as admin at http://localhost:3000                   │
│     • Click "Admin" button in header (visible to admins only)   │
│     • Create additional users via admin panel                   │
│                                                                 │
│  6. Production Configuration                                    │
│     • Change default admin password                             │
│     • Set JWT_SECRET environment variable                       │
│     • Configure HYBA_CORS_ORIGINS (no wildcards)                │
│     • Use PostgreSQL for production database                    │
│     • Enable HTTPS (required)                                   │
│     • Set up database backups                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        ROLE HIERARCHY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. admin                                                       │
│     • Full platform administration                              │
│     • Create, edit, delete users                                │
│     • View audit logs                                           │
│     • Access admin panel                                        │
│     • All operator/analyst/miner permissions                    │
│                                                                 │
│  2. operator                                                    │
│     • Mining operations control                                 │
│     • Pool management                                           │
│     • View telemetry dashboards                                 │
│     • Start/stop mining                                         │
│                                                                 │
│  3. analyst                                                     │
│     • Read-only analytics access                                │
│     • View telemetry and reports                                │
│     • Export data                                               │
│     • No control plane access                                   │
│                                                                 │
│  4. miner                                                       │
│     • Mining-specific access                                    │
│     • View own mining statistics                                │
│     • Limited telemetry access                                  │
│     • No admin or operator permissions                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      DATA FLOW EXAMPLE                          │
│                  (Create New User Flow)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Admin clicks "Create User" button in AdminPanel             │
│     ↓                                                           │
│  2. Modal displays with form fields:                            │
│     • Username (required, min 3 chars)                          │
│     • Email (optional, validated)                               │
│     • Password (required, min 8 chars)                          │
│     • Role (dropdown: admin/operator/analyst/miner)             │
│     ↓                                                           │
│  3. Form submitted to POST /api/admin/users                     │
│     • Headers: Authorization: Bearer <jwt_token>                │
│     • Body: { username, email, password, role }                 │
│     ↓                                                           │
│  4. Backend validates request:                                  │
│     • JWT token valid? ✓                                        │
│     • User has admin role? ✓                                    │
│     • Username unique? ✓                                        │
│     • Email unique? ✓                                           │
│     • Password meets requirements? ✓                            │
│     ↓                                                           │
│  5. Backend hashes password:                                    │
│     • password_hash = Argon2id.hash(password)                   │
│     ↓                                                           │
│  6. Backend creates user record:                                │
│     • INSERT INTO users (username, email, password_hash, ...)   │
│     ↓                                                           │
│  7. Backend logs audit trail:                                   │
│     • INSERT INTO audit_logs (actor, action, target, ...)       │
│     • action = "user_created"                                   │
│     ↓                                                           │
│  8. Backend returns UserResponse:                               │
│     • { id, username, email, role, created_at, ... }            │
│     • Password hash NOT included in response                    │
│     ↓                                                           │
│  9. Frontend updates user list:                                 │
│     • New user appears in table                                 │
│     • Statistics dashboard updates (total_users++)              │
│     • Success feedback shown to admin                           │
│     ↓                                                           │
│ 10. Audit log entry created:                                    │
│     • Timestamp: 2024-06-17 10:23:45 UTC                        │
│     • Actor: admin                                              │
│     • Action: user_created                                      │
│     • Target: user_id=123                                       │
│     • Details: { username: "new_operator", role: "operator" }   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   VALIDATION CHECKLIST                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Frontend:                                                      │
│  ✅ AdminPanel component exists                                 │
│  ✅ Integrated into App.tsx                                     │
│  ✅ Admin button (visible only to admins)                       │
│  ✅ User list with search and pagination                        │
│  ✅ Create user modal                                           │
│  ✅ Edit user modal                                             │
│  ✅ Delete user confirmation                                    │
│  ✅ Statistics dashboard                                        │
│  ✅ Error handling and feedback                                 │
│                                                                 │
│  Backend:                                                       │
│  ✅ Admin API module (admin.py)                                 │
│  ✅ 7 endpoints implemented (CRUD + audit + stats)              │
│  ✅ Admin router registered in main.py                          │
│  ✅ JWT authentication                                          │
│  ✅ Role-based access control (require_admin)                   │
│  ✅ Input validation (Pydantic models)                          │
│  ✅ Password hashing (Argon2id)                                 │
│  ✅ Audit logging (log_audit function)                          │
│  ✅ Self-protection mechanisms                                  │
│                                                                 │
│  Database:                                                      │
│  ✅ User model (username, email, password_hash, role, ...)      │
│  ✅ AuditLog model (actor, action, target, timestamp, ...)      │
│  ✅ UserRole enum (admin, operator, analyst, miner)             │
│  ✅ Auto-initialization (init_db in main.py)                    │
│                                                                 │
│  Deployment:                                                    │
│  ✅ Seed script (seed_admin_user.py)                            │
│  ✅ Argon2id dependency documented                              │
│  ✅ Startup instructions documented                             │
│  ✅ Production checklist provided                               │
│                                                                 │
│  Security:                                                      │
│  ✅ Argon2id password hashing                                   │
│  ✅ JWT bearer token authentication                             │
│  ✅ Admin role enforcement                                      │
│  ✅ Self-protection (cannot delete/demote self)                 │
│  ✅ Audit trail (all actions logged)                            │
│  ✅ Input validation                                            │
│  ✅ SQL injection protection                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
