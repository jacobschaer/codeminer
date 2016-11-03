from enum import IntEnum
from codeminer_tools import repositories
from django.db import models
from django.forms import ModelForm, Select

# Create your models here.
class Repository(models.Model):
    class RepositoryType(IntEnum):
        svn = 0
        cvs = 1
        hg = 2
        git = 3

    REPOSITORY_TYPE_CHOICES = (
        (int(RepositoryType.svn), 'Subversion'),
        (int(RepositoryType.cvs), 'CVS'),
        (int(RepositoryType.hg), 'Mercurial'),
        (int(RepositoryType.git), 'Git')
    )

    username = models.CharField(max_length=512, blank=True, null=True)
    password = models.CharField(max_length=512, blank=True, null=True)
    workspace = models.CharField(max_length=512, blank=True, null=True)
    origin = models.CharField(max_length=512)
    name = models.CharField(max_length=512)
    repository_type = models.IntegerField()

    def type_string(self):
        return self.REPOSITORY_TYPE_CHOICES[self.repository_type][1]

class RepositoryForm(ModelForm):
    class Meta:
        model = Repository
        fields = ['username', 'password', 'origin', 'name', 'repository_type']
        widgets = {
            'repository_type': Select(choices=Repository.REPOSITORY_TYPE_CHOICES),
        }
