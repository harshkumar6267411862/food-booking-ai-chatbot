from enum import Enum


class UserRole(str, Enum):
    STUDENT = "Student"
    ADMIN = "Admin"