"""
RBAC permission definitions and service-layer enforcement.

Roles: SUPER_ADMIN, ADMIN, HOD, FACULTY, STUDENT
Permissions follow (resource, action, scope) triplets.
Enforcement happens in service classes — NOT in routes.
"""
from __future__ import annotations

from typing import NamedTuple

from app.database.models import UserRole


class Perm(NamedTuple):
    resource: str
    action: str
    scope: str = "global"


# ---------------------------------------------------------------------------
# Permission constants
# ---------------------------------------------------------------------------

class Permissions:
    # Users
    USERS_READ = Perm("users", "read", "global")
    USERS_WRITE = Perm("users", "write", "global")
    USERS_DELETE = Perm("users", "delete", "global")

    # Students
    STUDENTS_READ_OWN = Perm("students", "read", "own")
    STUDENTS_READ_DEPT = Perm("students", "read", "own_department")
    STUDENTS_READ_ALL = Perm("students", "read", "global")
    STUDENTS_WRITE = Perm("students", "write", "global")

    # Results
    RESULTS_UPLOAD = Perm("results", "upload", "global")
    RESULTS_READ_OWN_CLASS = Perm("results", "read", "own_class")
    RESULTS_READ_DEPT = Perm("results", "read", "own_department")
    RESULTS_READ_ALL = Perm("results", "read", "global")
    RESULTS_COMMIT = Perm("results", "commit", "global")
    RESULTS_REJECT = Perm("results", "reject", "global")

    # Analytics
    ANALYTICS_READ_OWN = Perm("analytics", "read", "own")
    ANALYTICS_READ_OWN_CLASS = Perm("analytics", "read", "own_class")
    ANALYTICS_READ_DEPT = Perm("analytics", "read", "own_department")
    ANALYTICS_READ_ALL = Perm("analytics", "read", "global")

    # Intelligence / Attention
    INTELLIGENCE_READ_OWN_CLASS = Perm("intelligence", "read", "own_class")
    INTELLIGENCE_READ_DEPT = Perm("intelligence", "read", "own_department")
    INTELLIGENCE_READ_ALL = Perm("intelligence", "read", "global")

    # Interventions
    INTERVENTIONS_READ = Perm("interventions", "read", "own_class")
    INTERVENTIONS_WRITE = Perm("interventions", "write", "own_class")
    INTERVENTIONS_REVIEW = Perm("interventions", "review", "own_class")

    # Simulation
    SIMULATION_WRITE = Perm("simulation", "write", "own_class")
    SIMULATION_READ = Perm("simulation", "read", "own_class")

    # AI
    AI_GENERATE = Perm("ai", "generate", "own_class")
    AI_READ = Perm("ai", "read", "own_class")

    # Reports
    REPORTS_GENERATE = Perm("reports", "generate", "own_class")
    REPORTS_GENERATE_DEPT = Perm("reports", "generate", "own_department")
    REPORTS_GENERATE_ALL = Perm("reports", "generate", "global")

    # Admin / Master data
    MASTER_DATA_READ = Perm("master_data", "read", "global")
    MASTER_DATA_WRITE = Perm("master_data", "write", "global")
    GRADING_SCHEMES_WRITE = Perm("grading_schemes", "write", "global")
    AUDIT_LOGS_READ = Perm("audit_logs", "read", "global")
    SETTINGS_WRITE = Perm("settings", "write", "global")
    EVALUATION_RUN = Perm("evaluation", "run", "global")


# ---------------------------------------------------------------------------
# Role → permission mapping (seed data)
# ---------------------------------------------------------------------------

ROLE_PERMISSIONS: dict[UserRole, list[Perm]] = {
    UserRole.SUPER_ADMIN: [
        # All permissions
        Permissions.USERS_READ, Permissions.USERS_WRITE, Permissions.USERS_DELETE,
        Permissions.STUDENTS_READ_ALL, Permissions.STUDENTS_WRITE,
        Permissions.RESULTS_UPLOAD, Permissions.RESULTS_READ_ALL,
        Permissions.RESULTS_COMMIT, Permissions.RESULTS_REJECT,
        Permissions.ANALYTICS_READ_ALL,
        Permissions.INTELLIGENCE_READ_ALL,
        Permissions.INTERVENTIONS_READ, Permissions.INTERVENTIONS_WRITE,
        Permissions.INTERVENTIONS_REVIEW,
        Permissions.SIMULATION_WRITE, Permissions.SIMULATION_READ,
        Permissions.AI_GENERATE, Permissions.AI_READ,
        Permissions.REPORTS_GENERATE_ALL,
        Permissions.MASTER_DATA_READ, Permissions.MASTER_DATA_WRITE,
        Permissions.GRADING_SCHEMES_WRITE,
        Permissions.AUDIT_LOGS_READ,
        Permissions.SETTINGS_WRITE,
        Permissions.EVALUATION_RUN,
    ],
    UserRole.ADMIN: [
        Permissions.USERS_READ, Permissions.USERS_WRITE,
        Permissions.STUDENTS_READ_ALL, Permissions.STUDENTS_WRITE,
        Permissions.RESULTS_UPLOAD, Permissions.RESULTS_READ_ALL,
        Permissions.RESULTS_COMMIT, Permissions.RESULTS_REJECT,
        Permissions.ANALYTICS_READ_ALL,
        Permissions.INTELLIGENCE_READ_ALL,
        Permissions.INTERVENTIONS_READ, Permissions.INTERVENTIONS_WRITE,
        Permissions.SIMULATION_WRITE, Permissions.SIMULATION_READ,
        Permissions.AI_GENERATE, Permissions.AI_READ,
        Permissions.REPORTS_GENERATE_ALL,
        Permissions.MASTER_DATA_READ, Permissions.MASTER_DATA_WRITE,
        Permissions.GRADING_SCHEMES_WRITE,
        Permissions.AUDIT_LOGS_READ,
        Permissions.EVALUATION_RUN,
    ],
    UserRole.HOD: [
        Permissions.STUDENTS_READ_DEPT,
        Permissions.RESULTS_READ_DEPT,
        Permissions.ANALYTICS_READ_DEPT,
        Permissions.INTELLIGENCE_READ_DEPT,
        Permissions.INTERVENTIONS_READ, Permissions.INTERVENTIONS_REVIEW,
        Permissions.SIMULATION_READ,
        Permissions.AI_READ,
        Permissions.REPORTS_GENERATE_DEPT,
        Permissions.MASTER_DATA_READ,
    ],
    UserRole.FACULTY: [
        Permissions.STUDENTS_READ_DEPT,
        Permissions.RESULTS_READ_OWN_CLASS,
        Permissions.ANALYTICS_READ_OWN_CLASS,
        Permissions.INTELLIGENCE_READ_OWN_CLASS,
        Permissions.INTERVENTIONS_READ, Permissions.INTERVENTIONS_WRITE,
        Permissions.INTERVENTIONS_REVIEW,
        Permissions.SIMULATION_WRITE, Permissions.SIMULATION_READ,
        Permissions.AI_GENERATE, Permissions.AI_READ,
        Permissions.REPORTS_GENERATE,
        Permissions.MASTER_DATA_READ,
    ],
    UserRole.STUDENT: [
        Permissions.STUDENTS_READ_OWN,
        Permissions.ANALYTICS_READ_OWN,
        Permissions.MASTER_DATA_READ,
    ],
}


def get_role_permissions(role: UserRole) -> list[Perm]:
    """Return the list of permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: UserRole, required: Perm) -> bool:
    """Check if a role has a specific permission."""
    perms = get_role_permissions(role)
    return required in perms
