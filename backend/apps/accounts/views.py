from django.contrib.auth import authenticate, get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .api_permissions import IsAdminView
from .models import ModulePermission, Role, Team, TeamMember, UserPermission
from .serializers import (
    ModulePermissionSerializer,
    RoleSerializer,
    TeamMemberSerializer,
    TeamSerializer,
    UserPermissionSerializer,
    UserSerializer,
)

User = get_user_model()


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def me_payload(user):
    """User profile + effective access (role, dashboard, modules, businesses)."""
    from .access import ROLE_DASHBOARD, allowed_business_ids, role_permissions
    from apps.crm.models import Business

    data = UserSerializer(user).data
    role = getattr(user.role, "name", None)
    ids = allowed_business_ids(user)
    businesses = Business.objects.all()
    if ids is not None:
        businesses = businesses.filter(id__in=ids)
    data["dashboard"] = "admin" if user.is_superuser else ROLE_DASHBOARD.get(role, "sales-exec")
    data["is_superuser"] = user.is_superuser
    data["modules"] = role_permissions(user)
    data["business_ids"] = ids  # null = all
    data["businesses"] = [{"id": b.id, "name": b.name} for b in businesses]
    return data


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"user": me_payload(user), **tokens_for(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(me_payload(request.user))


class ProfileView(APIView):
    """Self-service: view/update own profile (name, phone, email)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(me_payload(request.user))

    def patch(self, request):
        user = request.user
        for field in ["name", "phone", "email"]:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return Response(me_payload(user))


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old = request.data.get("old_password")
        new = request.data.get("new_password")
        if not user.check_password(old or ""):
            return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        if not new or len(new) < 6:
            return Response({"detail": "New password must be at least 6 characters."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new)
        user.save()
        return Response({"status": "Password changed successfully."})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        email = (request.data.get("email") or "").strip()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            send_mail(
                "[DAGOS] Reset your password",
                f"Hi {user.name},\n\nReset your password using this link:\n{link}\n\n"
                "If you didn't request this, ignore this email.",
                settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True,
            )
        # never reveal whether the email exists
        return Response({"status": "If that email exists, a reset link has been sent."})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode

        uid = request.data.get("uid")
        token = request.data.get("token")
        new = request.data.get("new_password")
        if not new or len(new) < 6:
            return Response({"detail": "Password must be at least 6 characters."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
        except Exception:
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Reset link is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new)
        user.save()
        return Response({"status": "Password reset successfully. You can now sign in."})


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("role", "manager").all().order_by("-created_at")
    serializer_class = UserSerializer
    filterset_fields = ["role", "status", "manager"]
    search_fields = ["name", "email", "employee_id", "phone"]

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def assignable(self, request):
        """Users a lead can be assigned to — sales roles only.
        (Super Admin / Business Head / Support / HR / Finance excluded.)"""
        from .access import ASSIGNABLE_LEAD_ROLES
        users = (User.objects.filter(role__name__in=ASSIGNABLE_LEAD_ROLES, is_active=True)
                 .select_related("role").order_by("name"))
        return Response([
            {"id": u.id, "name": u.name, "role_name": getattr(u.role, "name", "")}
            for u in users
        ])


class UserPermissionViewSet(viewsets.ModelViewSet):
    queryset = UserPermission.objects.select_related("user", "business", "product").all()
    serializer_class = UserPermissionSerializer
    permission_classes = [IsAdminView]
    filterset_fields = ["user", "business", "product"]


class ModulePermissionViewSet(viewsets.ModelViewSet):
    queryset = ModulePermission.objects.select_related("role").all()
    serializer_class = ModulePermissionSerializer
    permission_classes = [IsAdminView]
    filterset_fields = ["role", "module"]
    pagination_class = None


class AccessMetaView(APIView):
    """Reference data for the Permission Matrix UI."""

    permission_classes = [IsAdminView]

    def get(self, request):
        from .access import MODULES, ROLE_MATRIX
        return Response({"modules": MODULES, "roles": list(ROLE_MATRIX.keys())})


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.select_related("leader").prefetch_related("members").all()
    serializer_class = TeamSerializer
    search_fields = ["name"]


class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.select_related("team", "user").all()
    serializer_class = TeamMemberSerializer
    filterset_fields = ["team", "user"]
