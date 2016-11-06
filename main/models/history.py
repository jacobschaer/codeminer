from django.db import models
# Create your models here.

class History(models.Model):
    head_file = models.ForeignKey('File', null=True, related_name='+')