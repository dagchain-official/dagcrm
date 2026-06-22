from django.contrib import admin

from .models import Commission, Expense

admin.site.register([
    Expense, Commission,
])
