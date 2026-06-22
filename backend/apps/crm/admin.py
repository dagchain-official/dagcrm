from django.contrib import admin

from .models import (
    Business, Communication, Customer, CustomerProduct, Lead, LeadActivity,
    LeadInterest, LeadSource, Opportunity, Product, Target, TargetAssignment,
)

admin.site.register([
    Business, Product, LeadSource, Lead, LeadInterest, LeadActivity,
    Opportunity, Customer, CustomerProduct, Communication, Target, TargetAssignment,
])
