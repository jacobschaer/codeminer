from enum import Enum
from codeminer_tools import repositories
from django.db import models

# Create your models here.

class File(models.Model):
    repository = models.ForeignKey('Repository', on_delete=models.CASCADE)
    # A change can be associated with many histories (merges)
    history = models.ManyToManyField(History)
    path = models.CharField(max_length=512, null=True)
    revision = models.CharField(max_length=512, null=True)
    checksum = models.CharField(max_length=32, null=True)