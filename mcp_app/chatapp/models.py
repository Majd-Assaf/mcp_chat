from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="documents/")
    extracted_text = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} ({self.id})"
