"""
Role-Based Access Control (RBAC)
HYBA Genesis Platform Authorization
"""

from enum import Enum
from typing import List, Set

class Permission(Enum):
    MANAGE_USERS = "manage_users"
    SYSTEM_CONFIG = "system_config"
    SECURITY_CONTROLS = "security_controls"
    POOL_MANAGEMENT = "pool_management"
    MINING_OPERATIONS = "mining_operations"
    SHARE_SUBMISSION = "share_submission"
    PERFORMANCE_METRICS = "performance_metrics"
    READ_ANALYTICS = "read_analytics"
    VIEW_CONSCIOUSNESS = "view_consciousness"
    ACCESS_QUANTUM_RESULTS = "access_quantum_results"

class RolePermissions:
    ADMIN_PERMISSIONS = set(Permission)
    
    @classmethod
    def get_permissions_for_role(cls, role: str) -> Set[Permission]:
        if role == "admin":
            return cls.ADMIN_PERMISSIONS
        return set()
