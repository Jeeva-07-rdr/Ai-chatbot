from django.db import models


class ConversionHistory(models.Model):

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    original_filename  = models.CharField(max_length=255)
    converted_filename = models.CharField(max_length=255)
    conversion_type    = models.CharField(max_length=100)
    file_size          = models.CharField(max_length=50)
    result             = models.CharField(max_length=20, default='Success')   # Success / Failed
    download_url       = models.CharField(max_length=512)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)
    record_status      = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Active',
        db_index=True,
    )

    class Meta:
        db_table   = 'conversion_history'
        ordering   = ['-created_at']
        verbose_name        = 'Conversion History'
        verbose_name_plural = 'Conversion History'

    def __str__(self):
        return f"{self.original_filename} [{self.record_status}]"

    def soft_delete(self):
        """Mark this record as Inactive without deleting it from the database."""
        self.record_status = 'Inactive'
        self.save(update_fields=['record_status', 'updated_at'])

    def restore(self):
        """Restore this record back to Active."""
        self.record_status = 'Active'
        self.save(update_fields=['record_status', 'updated_at'])