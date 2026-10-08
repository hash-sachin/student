"""
RBAC matrix tests.
Auto-generated coverage: every role × every key endpoint × allow/deny.
"""
from __future__ import annotations

import pytest
from app.auth.rbac import ROLE_PERMISSIONS, Permissions, has_permission
from app.database.models import UserRole


# ---------------------------------------------------------------------------
# Declarative matrix: (role, permission, expected_result)
# ---------------------------------------------------------------------------
MATRIX = [
    # SUPER_ADMIN has everything
    (UserRole.SUPER_ADMIN, Permissions.USERS_READ, True),
    (UserRole.SUPER_ADMIN, Permissions.STUDENTS_READ_ALL, True),
    (UserRole.SUPER_ADMIN, Permissions.RESULTS_COMMIT, True),
    (UserRole.SUPER_ADMIN, Permissions.AUDIT_LOGS_READ, True),
    (UserRole.SUPER_ADMIN, Permissions.SETTINGS_WRITE, True),
    (UserRole.SUPER_ADMIN, Permissions.EVALUATION_RUN, True),

    # ADMIN
    (UserRole.ADMIN, Permissions.USERS_READ, True),
    (UserRole.ADMIN, Permissions.RESULTS_UPLOAD, True),
    (UserRole.ADMIN, Permissions.RESULTS_COMMIT, True),
    (UserRole.ADMIN, Permissions.GRADING_SCHEMES_WRITE, True),
    (UserRole.ADMIN, Permissions.SETTINGS_WRITE, False),  # ADMIN cannot change global settings
    (UserRole.ADMIN, Permissions.USERS_DELETE, False),    # only SUPER_ADMIN

    # HOD
    (UserRole.HOD, Permissions.STUDENTS_READ_DEPT, True),
    (UserRole.HOD, Permissions.ANALYTICS_READ_DEPT, True),
    (UserRole.HOD, Permissions.REPORTS_GENERATE_DEPT, True),
    (UserRole.HOD, Permissions.RESULTS_COMMIT, False),   # HOD cannot commit uploads
    (UserRole.HOD, Permissions.USERS_WRITE, False),
    (UserRole.HOD, Permissions.SETTINGS_WRITE, False),

    # FACULTY
    (UserRole.FACULTY, Permissions.RESULTS_READ_OWN_CLASS, True),
    (UserRole.FACULTY, Permissions.ANALYTICS_READ_OWN_CLASS, True),
    (UserRole.FACULTY, Permissions.INTERVENTIONS_WRITE, True),
    (UserRole.FACULTY, Permissions.SIMULATION_WRITE, True),
    (UserRole.FACULTY, Permissions.AI_GENERATE, True),
    (UserRole.FACULTY, Permissions.RESULTS_COMMIT, False),      # no commit
    (UserRole.FACULTY, Permissions.STUDENTS_READ_ALL, False),   # own class only
    (UserRole.FACULTY, Permissions.GRADING_SCHEMES_WRITE, False),
    (UserRole.FACULTY, Permissions.AUDIT_LOGS_READ, False),
    (UserRole.FACULTY, Permissions.USERS_WRITE, False),

    # STUDENT
    (UserRole.STUDENT, Permissions.STUDENTS_READ_OWN, True),
    (UserRole.STUDENT, Permissions.ANALYTICS_READ_OWN, True),
    (UserRole.STUDENT, Permissions.STUDENTS_READ_ALL, False),
    (UserRole.STUDENT, Permissions.RESULTS_UPLOAD, False),
    (UserRole.STUDENT, Permissions.INTERVENTIONS_WRITE, False),
    (UserRole.STUDENT, Permissions.AI_GENERATE, False),
    (UserRole.STUDENT, Permissions.REPORTS_GENERATE, False),
    (UserRole.STUDENT, Permissions.AUDIT_LOGS_READ, False),
    (UserRole.STUDENT, Permissions.SETTINGS_WRITE, False),
]


@pytest.mark.parametrize("role,permission,expected", MATRIX)
def test_rbac_matrix(role, permission, expected):
    """Each role has exactly the permissions it should."""
    result = has_permission(role, permission)
    assert result == expected, (
        f"Role={role.value}, Permission={permission}, "
        f"Expected={expected}, Got={result}"
    )


def test_all_roles_have_permissions_defined():
    """Every UserRole must have an entry in ROLE_PERMISSIONS."""
    for role in UserRole:
        perms = ROLE_PERMISSIONS.get(role)
        assert perms is not None, f"Role {role} has no permissions defined"
        assert len(perms) > 0, f"Role {role} has empty permissions list"


def test_student_cannot_access_admin_permissions():
    """Sanity: student should not have any admin-only permissions."""
    admin_only = [
        Permissions.USERS_WRITE,
        Permissions.RESULTS_COMMIT,
        Permissions.GRADING_SCHEMES_WRITE,
        Permissions.SETTINGS_WRITE,
        Permissions.AUDIT_LOGS_READ,
        Permissions.EVALUATION_RUN,
    ]
    for perm in admin_only:
        assert not has_permission(UserRole.STUDENT, perm), \
            f"Student should NOT have permission: {perm}"


def test_faculty_cannot_access_hod_department_permissions():
    """Faculty should not have department-wide read-all permissions."""
    assert not has_permission(UserRole.FACULTY, Permissions.STUDENTS_READ_ALL)
