"""Serializers for user-related models."""
from rest_framework import serializers

from .models import User, Role, UserRole


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model."""
    class Meta:
        model = Role
        fields = ('id', 'name', 'code', 'description', 'is_active')


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for the UserRole model."""
    role = RoleSerializer(read_only=True)
    
    class Meta:
        model = UserRole
        fields = ('id', 'role', 'assigned_at')


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    roles = UserRoleSerializer(source='user_roles', many=True, read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'avatar', 'date_of_birth', 'gender',
            'language_preference', 'roles', 'is_active', 'date_joined'
        )
        read_only_fields = ('email', 'date_joined')

    def get_full_name(self, obj):
        """Get user's full name or username if not set."""
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    password = serializers.CharField(write_only=True, required=True)
    role_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'first_name', 'last_name',
            'phone_number', 'role_code'
        )

    def create(self, validated_data):
        """Create new user and optionally assign a role."""
        role_code = validated_data.pop('role_code', None)
        user = User.objects.create_user(**validated_data)
        
        if role_code:
            try:
                role = Role.objects.get(code=role_code, is_active=True)
                UserRole.objects.create(user=user, role=role)
            except Role.DoesNotExist:
                pass
        
        return user 