from django.db import models


class Store(models.Model):
    """Physical or virtual stores."""
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Store name"
    )
    location = models.CharField(
        max_length=500,
        help_text="Store location/address"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Stores"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} - {self.location}"
