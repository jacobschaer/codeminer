from enum import Enum
from codeminer_tools import repositories
from neomodel import (StructuredRel, StringProperty, IntegerProperty,
    RelationshipTo, RelationshipFrom)

# Create your models here.

class Change(StructuredRel):
-    action = IntegerProperty()