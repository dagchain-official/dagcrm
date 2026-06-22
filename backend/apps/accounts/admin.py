from django.contrib import admin

from .models import ModulePermission, Role, Team, TeamMember, User, UserPermission

admin.site.register([Role, User, UserPermission, ModulePermission, Team, TeamMember])
