from enum import Enum
from codeminer_tools import repositories
from django.db import models
from neomodel import (StructuredNode, StringProperty, IntegerProperty, DateTimeProperty,
    RelationshipTo, RelationshipFrom)
from .change import Change

# Create your models here.

class ChangeSet(StructuredNode):
    repository_id = IntegerProperty()
    identifier = StringProperty()
    author = StringProperty()
    message = StringProperty()
    timestamp = DateTimeProperty()
    ancestor = RelationshipFrom('main.models.Entity', 'CHANGE', model=Change)
    descendant = RelationshipTo('main.models.Entity', 'CHANGE', model=Change)