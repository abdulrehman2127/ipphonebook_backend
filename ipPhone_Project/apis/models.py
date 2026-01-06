from django.db import models

class PhoneRequestLog(models.Model):
    ip_address = models.GenericIPAddressField()
    file_requested = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    status_code = models.IntegerField(default=200)

    def __str__(self):
        return f"{self.ip_address} requested {self.file_requested} at {self.timestamp}"
