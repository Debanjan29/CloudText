from django.db import models
from django.utils.timezone import now

# Create your models here.
class Store(models.Model):
    msg=models.TextField()
    id=models.TextField(max_length=5,primary_key=True)
    date=models.DateTimeField(default=now)

    
    ordering = ['date']

    class Meta:
        ordering = ('-date',)
    def __str__(self):
        return self.id +" "+"on "+self.date.strftime("%m/%d/%Y %H:%M:%S")