from django.db import models


# ------------------------------------------------------------------ Revenue
class Revenue(models.Model):
    customer = models.ForeignKey("crm.Customer", on_delete=models.CASCADE, related_name="revenues")
    business = models.ForeignKey("crm.Business", on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey("crm.Product", on_delete=models.SET_NULL, null=True, blank=True)
    gross_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.net_revenue = self.gross_revenue - self.commission
        super().save(*args, **kwargs)
