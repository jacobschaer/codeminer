from enum import IntEnum
from codeminer_tools import repositories
from django.db import models
from django.forms import ModelForm, Select
from . import Entity, Change, ChangeSet
from codeminer_tools.repositories.change import ChangeType
from codeminer_tools.repositories import SVNRepository, CVSRepository, HgRepository, GitRepository
from neomodel import db, StructuredRel
import shutil
from django.db.models.signals import pre_delete 
from django.dispatch import receiver

@receiver(pre_delete)
def delete_repo(sender, instance, **kwargs):
    if sender == Repository:
        shutil.rmtree(instance.local_copy)

class ChangePair:
    def __init__(self, source_entity, source_change, changeset,
                 destination_change, destination_entity, ancestery):
        self.source_entity = source_entity
        self.source_change = source_change
        self.changeset = changeset
        self.destination_change = destination_change
        self.destination_entity = destination_entity
        self.ancestery = ancestery

    def revision(self):
        if self.source_entity is not None:
            return int(self.source_entity.revision)
        else:
            return int(self.destination_entity.revision)

    def __lt__(self, other):
        return self.revision() < other.revision()

    def __gt__(self, other):
        return self.revision() > other.revision()

    def __ge__(self, other):
        return self.revision() >= other.revision()

    def __le__(self, other):
        return self.revision() <= other.revision()

    def __eq__(self, other):
        return self.revision() == other.revision()

    def __ne__(self, other):
        return self.revision() == other.revision()

    def __str__(self):
        strings = ['add', 'remove', 'modify', 'move', 'copy', 'derived']

        f1 = self.source_entity.path if self.source_entity is not None else 'None'
        f2 = self.destination_entity.path if self.destination_entity is not None else 'None'
        r1 = self.source_entity.revision if self.source_entity is not None else 'None'
        r2 = self.destination_entity.revision if self.destination_entity is not None else 'None'
        type1 = strings[self.source_change.action] if self.source_change is not None else ""
        type2 = strings[self.destination_change.action] if self.destination_change is not None else ""

        if type2 == 'add':
            return "!!!!!!\n!!!!!! ADD {f2}@{r2}\n!!!!!!\n!!!!!!".format(f2=f2,r2=f2)
        elif type1 == 'remove':
            return "!!!!!!\n!!!!!! DELETE {f1}@{r1}\n!!!!!!\n!!!!!!".format(f1=f1,r1=f1)
        else:
            return "{f1}@{r1} - ({type1} / {type2}) -> {f2}@{r2}".format(
                    f1=f1, f2=f2, r1=r1, r2=r2, type1=type1, type2=type2)


def get_local_repository_connection(repository_type, path, username, password, workspace, cleanup):
    REPOSITORY_OBJECT_MAP = {
        int(Repository.RepositoryType.svn) : SVNRepository,
        int(Repository.RepositoryType.cvs) : CVSRepository,
        int(Repository.RepositoryType.hg) : HgRepository,
        int(Repository.RepositoryType.git) : GitRepository,
    }
    return REPOSITORY_OBJECT_MAP[int(repository_type)](path, username=username, password=password, workspace=workspace, cleanup=cleanup)

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
    local_copy = models.CharField(max_length=512, blank=True, null=True)
    origin = models.CharField(max_length=512)
    name = models.CharField(max_length=512)
    repository_type = models.IntegerField()

    def type_string(self):
        return self.REPOSITORY_TYPE_CHOICES[self.repository_type][1]

    def get_unique_paths(self):
        query = '''MATCH (file:Entity)-[:CHANGE]->(:ChangeSet {{repository_id: {repository_id} }})
                   RETURN DISTINCT file.path'''.format(repository_id = self.pk)
        params = {}
        results, meta = db.cypher_query(query, params)
        for x in results:
            yield str(x[0])

    def get_change_triples(self, path):
        """ Gets the "triangles" of form
             changeset
            /         \
        file --------> file
        """
        query = '''MATCH (a:Entity {{path: '{path}'}})-[b:CHANGE]->(c:ChangeSet {{repository_id: {repository_id}}})-[d:CHANGE]->(e:Entity)-[f:ANCESTOR]->(g:Entity)
                   WHERE a = g
                   RETURN a,b,c,d,e,f
                   ORDER BY a.revision ASCENDING'''.format(repository_id = self.pk, path=path)
        params = {}
        print(query)
        results, meta = db.cypher_query(query, params)
        for a,b,c,d,e,f in results:
            yield ChangePair(
                Entity.inflate(a),
                Change.inflate(b),
                ChangeSet.inflate(c),
                Change.inflate(d),
                Entity.inflate(e),
                StructuredRel.inflate(f))

    def get_adds(self, path):
        """ Gets the add commit for a path"""
        query = '''MATCH (f:Entity {{path: '{path}'}})<-[c:CHANGE {{action: {action}}}]-(cs:ChangeSet {{repository_id: {repository_id} }})
                   RETURN f,c,cs
                   ORDER BY f.revision ASCENDING'''.format(repository_id=self.pk, path=path, action=ChangeType.add.value)
        params = {}
        print(query)
        results, meta = db.cypher_query(query, params)
        for f,c,cs in results:
            yield ChangePair(None, None, ChangeSet.inflate(cs), Change.inflate(c), Entity.inflate(f), None)
   
    def get_removes(self, path):
        """ Gets the remove commit for a path"""
        query = '''MATCH (f:Entity {{path: '{path}'}})-[c:CHANGE {{action: {action}}}]->(cs:ChangeSet {{repository_id: {repository_id} }})
                   RETURN f,c,cs
                   ORDER BY f.revision ASCENDING'''.format(repository_id=self.pk, path=path, action=ChangeType.remove.value)
        params = {}
        print(query)
        results, meta = db.cypher_query(query, params)
        for f,c,cs in results:
            yield ChangePair(Entity.inflate(f), Change.inflate(c), ChangeSet.inflate(cs), None, None, None)

    def get_leaf_nodes(self, path=''):
        if path == '':
            path_query = '[^/]+'
        # Add off trailing /
        elif path[-1] == '/':
            path_query = '{path}[^/]+'.format(path=path)
        else:
            path_query = '{path}/[^/]+'.format(path=path)
        # Match files that have no descendants whose paths are immediately below the 
        # provided one
        query = '''MATCH (f:Entity)-[c:CHANGE]-(:ChangeSet {{repository_id: {repository_id}}})
                   WHERE f.path =~ '{path_query}' AND
                   NOT (:Entity)-[:ANCESTOR]->(f)
                   RETURN f, c'''.format(repository_id=self.pk, path_query=path_query)
        params = {}
        print(query)
        results, meta = db.cypher_query(query, params)
        for row in results:
            yield (Entity.inflate(row[0]), Change.inflate(row[1]))

class RepositoryForm(ModelForm):
    class Meta:
        model = Repository
        fields = ['username', 'password', 'origin', 'name', 'repository_type']
        widgets = {
            'repository_type': Select(choices=Repository.REPOSITORY_TYPE_CHOICES),
        }