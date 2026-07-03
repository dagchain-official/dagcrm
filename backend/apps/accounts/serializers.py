from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import EmailAccount, ModulePermission, Role, Team, TeamMember, TeamRequest, UserPermission

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
        # `product` is part of the (user, business, product) unique_together. DRF's
        # auto UniqueTogetherValidator would otherwise force `product` to be required,
        # blocking business-only grants (no specific product) from the Permission
        # Matrix. Make it optional and drop that validator (the DB constraint still
        # protects against real duplicates; the UI checks before creating).
        extra_kwargs = {"product": {"required": False, "allow_null": True}}
        validators = []


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


class EmailAccountSerializer(serializers.ModelSerializer):
    # password is write-only — never sent back to the browser
    smtp_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_password = serializers.SerializerMethodField()

    class Meta:
        model = EmailAccount
        fields = ["id", "label", "from_name", "from_email", "smtp_host", "smtp_port",
                  "smtp_username", "smtp_password", "has_password", "use_tls",
                  "is_default", "is_active", "created_at"]
        read_only_fields = ["created_at"]

    def get_has_password(self, obj):
        return bool(obj.smtp_password)

    def update(self, instance, validated_data):
        # keep the existing password if the form left it blank
        if not validated_data.get("smtp_password"):
            validated_data.pop("smtp_password", None)
        return super().update(instance, validated_data)


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


class TeamRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source="requested_by.name", read_only=True)
    member_name = serializers.CharField(source="member.name", read_only=True)
    team_name = serializers.CharField(source="team.name", read_only=True)
    decided_by_name = serializers.CharField(source="decided_by.name", read_only=True)

    class Meta:
        model = TeamRequest
        fields = ["id", "requested_by", "requested_by_name", "member", "member_name",
                  "team", "team_name", "reason", "status", "decided_by", "decided_by_name",
                  "decided_at", "created_at"]
        read_only_fields = ["requested_by", "status", "decided_by", "decided_at", "created_at"]
