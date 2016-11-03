from django.db import models

# Create your models here.

class History(models.Model):
    repository = models.ForeignKey('Repository', on_delete=models.CASCADE)