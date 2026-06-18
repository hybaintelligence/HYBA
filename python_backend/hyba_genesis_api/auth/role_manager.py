"""
Role-Based Access Control (RBAC)
HYBA Genesis Platform Authorization
"""

from enum import Enum
from typing import Set


class Permission(Enum):
    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # System configuration
    SYSTEM_CONFIG = "system_config"
    VIEW_SYSTEM_HEALTH = "view_system_health"
    
    # Security
    SECURITY_CONTROLS = "security_controls"
    VIEW_SECURITY_STATUS = "view_security_status"
    
    # Mining operations
    POOL_MANAGEMENT = "pool_management"
    MINING_OPERATIONS = "mining_operations"
    SHARE_SUBMISSION = "share_submission"
    
    # Analytics and metrics
    PERFORMANCE_METRICS = "performance_metrics"
    READ_ANALYTICS = "read_analytics"
    
    # AI and consciousness
    VIEW_CONSCIOUSNESS = "view_consciousness"
    ACCESS_QUANTUM_RESULTS = "access_quantum_results"
    
    # Funding and finance (Executive only)
    MANAGE_FUNDING = "manage_funding"
    APPROVE_FUNDING = "approve_funding"
    VIEW_FUNDING = "view_funding"
    DISBURSE_FUNDS = "disburse_funds"
    
    # Audit and compliance
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_AUDIT_REPORTS = "export_audit_reports"


class RolePermissions:
    # Executive roles - full access including funding
    EXECUTIVE_PERMISSIONS = {
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.SYSTEM_CONFIG,
        Permission.VIEW_SYSTEM_HEALTH,
        Permission.SECURITY_CONTROLS,
        Permission.VIEW_SECURITY_STATUS,
        Permission.POOL_MANAGEMENT,
        Permission.MINING_OPERATIONS,
        Permission.SHARE_SUBMISSION,
        Permission.PERFORMANCE_METRICS,
        Permission.READ_ANALYTICS,
        Permission.VIEW_CONSCIOUSNESS,
        Permission.ACCESS_QUANTUM_RESULTS,
        Permission.MANAGE_FUNDING,
        Permission.APPROVE_FUNDING,
        Permission.VIEW_FUNDING,
        Permission.DISBURSE_FUNDS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_AUDIT_REPORTS,
    }
    
    # Admin role - operational access but no funding
    ADMIN_PERMISSIONS = {
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.SYSTEM_CONFIG,
        Permission.VIEW_SYSTEM_HEALTH,
        Permission.SECURITY_CONTROLS,
        Permission.VIEW_SECURITY_STATUS,
        Permission.POOL_MANAGEMENT,
        Permission.MINING_OPERATIONS,
        Permission.SHARE_SUBMISSION,
        Permission.PERFORMANCE_METRICS,
        Permission.READ_ANALYTICS,
        Permission.VIEW_CONSCIOUSNESS,
        Permission.ACCESS_QUANTUM_RESULTS,
        Permission.VIEW_AUDIT_LOGS,
    }
    
    # Operator role - operational access
    OPERATOR_PERMISSIONS = {
        Permission.VIEW_USERS,
        Permission.VIEW_SYSTEM_HEALTH,
        Permission.VIEW_SECURITY_STATUS,
        Permission.POOL_MANAGEMENT,
        Permission.MINING_OPERATIONS,
        Permission.SHARE_SUBMISSION,
        Permission.PERFORMANCE_METRICS,
        Permission.READ_ANALYTICS,
    }
    
    # Analyst role - read-only access
    ANALYST_PERMISSIONS = {
        Permission.VIEW_USERS,
        Permission.VIEW_SYSTEM_HEALTH,
        Permission.VIEW_SECURITY_STATUS,
        Permission.PERFORMANCE_METRICS,
        Permission.READ_ANALYTICS,
        Permission.VIEW_CONSCIOUSNESS,
    }
    
    # Miner role - minimal access
    MINER_PERMISSIONS = {
        Permission.SHARE_SUBMISSION,
        Permission.VIEW_SYSTEM_HEALTH,
    }

    @classmethod
    def get_permissions_for_role(cls, role: str) -> Set[Permission]:
        role_mapping = {
            "ceo_heir_apparent": cls.EXECUTIVE_PERMISSIONS,
            "chairman": cls.EXECUTIVE_PERMISSIONS,
            "cto": cls.EXECUTIVE_PERMISSIONS,
            "cfo": cls.EXECUTIVE_PERMISSIONS,
            "legal": cls.EXECUTIVE_PERMISSIONS,
            "chief_of_staff": cls.EXECUTIVE_PERMISSIONS,
            "admin": cls.ADMIN_PERMISSIONS,
            "operator": cls.OPERATOR_PERMISSIONS,
            "analyst": cls.ANALYST_PERMISSIONS,
            "miner": cls.MINER_PERMISSIONS,
        }
        return role_mapping.get(role, set())
    
    @classmethod
    def is_executive_role(cls, role: str) -> bool:
        """Check if role is an executive role with funding permissions."""
        executive_roles = {
            "ceo_heir_apparent",
            "chairman",
            "cto",
            "cfo",
            "legal",
            "chief_of_staff",
        }
        return role in executive_roles
