from django.db import models


# ------------------------------------------------------------------ Expenses
class Expense(models.Model):
    department = models.ForeignKey("hr.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    expense_type = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    date = models.DateField()

    class Meta:
        ordering = ["-date"]


# ------------------------------------------------------------------ Commissions
class Commission(models.Model):
    partner_name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    business = models.ForeignKey("crm.Business", on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()

    class Meta:
        ordering = ["-date"]
