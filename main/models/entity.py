from enum import Enum
from codeminer_tools import repositories
from django.db import models
from neomodel import (StructuredNode, StringProperty, IntegerProperty,
    RelationshipTo, RelationshipFrom)
from .change import Change

# Create your models here.

class Entity(StructuredNode):
    type = IntegerProperty()
    repository_id = IntegerProperty()
    path = StringProperty()
    revision = StringProperty()
    checksum = StringProperty()
    change_input = RelationshipTo('main.models.ChangeSet', 'CHANGE', model=Change)
    change_output = RelationshipFrom('main.models.ChangeSet', 'CHANGE', model=Change)
    ancestor = RelationshipTo('main.models.Entity', 'ANCESTOR')