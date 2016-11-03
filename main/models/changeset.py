from enum import Enum
from codeminer_tools import repositories
from django.db import models

# Create your models here.

class ChangeSet(models.Model):
    repository = models.ForeignKey('Repository', on_delete=models.CASCADE)
    identifier = models.CharField(max_length=512)
    author = models.CharField(max_length=512, null=True)
    message = models.TextField(null=True)
    timestamp = models.DateTimeField(null=True)
    history = models.ForeignKey('History', null=True)