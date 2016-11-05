from enum import Enum
from codeminer_tools import repositories
from django.db import models

# Create your models here.

class Change(models.Model):
    # A change can be part of only one ChangeSet
    changeset = models.ForeignKey('ChangeSet', on_delete=models.CASCADE)
    # A change can be associated with only one history
    history = models.ForeignKey('History', on_delete=models.CASCADE, null=True)
    # A change relates precisely two files - with the special case being the
    # null file (non-existant)
    previous_file = models.ForeignKey('File', related_name='+', null=True)
    current_file = models.ForeignKey('File', related_name='+', null=True)
    action = models.IntegerField()
