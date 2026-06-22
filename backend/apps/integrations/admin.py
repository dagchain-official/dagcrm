from django.contrib import admin

from .models import IntegrationConnection, IntegrationLog

admin.site.register([IntegrationConnection, IntegrationLog])
