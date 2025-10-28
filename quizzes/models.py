from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings

class Quiz(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    visibility = models.CharField(max_length=10)
    def __str__(self): return self.title
