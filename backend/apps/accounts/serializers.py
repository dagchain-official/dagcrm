from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ModulePermission, Role, Team, TeamMember, UserPermission

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class UserPermissionSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = UserPermission
        fields = ["id", "user", "user_name", "business", "business_name", "product",
                  "can_view", "can_create", "can_edit", "can_delete"]


class ModulePermissionSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = ModulePermission
        fields = ["id", "role", "role_name", "module",
                  "can_view", "can_create", "can_edit", "can_delete"]


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    manager_name = serializers.CharField(source="manager.name", read_only=True)
    is_admin_view = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id", "employee_id", "name", "email", "phone", "role", "role_name",
            "manager", "manager_name", "status", "is_active", "created_at",
            "is_admin_view", "password",
        ]
        read_only_fields = ["created_at"]

    def get_is_admin_view(self, obj):
        from .utils import is_admin_view
        return is_admin_view(obj)

    def create(self, validated_data):
        password = validated_data.pop("password", None) or "changeme123"
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TeamMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = TeamMember
        fields = ["id", "team", "user", "user_name"]


class TeamSerializer(serializers.ModelSerializer):
    leader_name = serializers.CharField(source="leader.name", read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "leader", "leader_name", "members", "created_at"]
