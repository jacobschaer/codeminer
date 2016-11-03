from enum import Enum
from codeminer_tools import repositories
from django.db import models

# Create your models here.

class Change(models.Model):
    changeset = models.ForeignKey('ChangeSet', on_delete=models.CASCADE)
    previous_file = models.ForeignKey('File', related_name='+', null=True)
    current_file = models.ForeignKey('File', related_name='+', null=True)
    action = models.IntegerField()
