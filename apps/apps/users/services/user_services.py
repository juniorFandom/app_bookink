"""User management service functions."""
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.users.models import Role, UserRole

User = get_user_model()


def create_user(email, password=None, **extra_fields):
    """Create a new user with the given email and password."""
    if not email:
        raise ValueError('The Email field must be set')
    email = User.objects.normalize_email(email)
    user = User(email=email, username=email, **extra_fields)
    if password:
        user.set_password(password)
    user.save()
    return user


def assign_role(user, role_code):
    """Assign a role to a user by role code."""
    try:
        role = Role.objects.get(code=role_code, is_active=True)
    except Role.DoesNotExist:
        raise ValueError(f'Role with code {role_code} does not exist or is not active')

    UserRole.objects.get_or_create(user=user, role=role)
    return True


@transaction.atomic
def create_user_with_role(email, role_code, password=None, **extra_fields):
    """Create a new user and assign them a role in one transaction."""
    user = create_user(email=email, password=password, **extra_fields)
    assign_role(user, role_code)
    return user 