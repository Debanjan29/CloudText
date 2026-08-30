from django.db import models
from django.utils.timezone import now

# Create your models here.
class Store(models.Model):
    msg=models.TextField()
    id=models.TextField(max_length=5,primary_key=True)
    date=models.DateTimeField(default=now)

    # === 2026 update! ===
    is_file = models.BooleanField(default=False)
    file_data = models.BinaryField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(default=0)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    # === 2026 update! ===

    ordering = ['date']

    class Meta:
        ordering = ('-date',)
    def __str__(self):
        return self.id +" "+"on "+self.date.strftime("%m/%d/%Y %H:%M:%S")