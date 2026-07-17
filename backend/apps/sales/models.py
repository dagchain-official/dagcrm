from django.db import models


# ------------------------------------------------------------------ Revenue
class Revenue(models.Model):
    customer = models.ForeignKey("crm.Customer", on_delete=models.CASCADE, related_name="revenues")
    business = models.ForeignKey("crm.Business", on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey("crm.Product", on_delete=models.SET_NULL, null=True, blank=True)
    gross_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    external_id = models.CharField(max_length=80, blank=True, db_index=True)  # idempotent external sync key
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.net_revenue = self.gross_revenue - self.commission
        # A partial save (update_or_create passes update_fields=the defaults it set)
        # would drop the recomputed net_revenue, leaving it stale — always write it.
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"net_revenue"}
        super().save(*args, **kwargs)
