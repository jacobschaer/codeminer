from codeminer_tools.repositories import cvs, git, hg, svn
from codeminer_tools.repositories.entity import EntityType
from codeminer_tools.repositories import RepositoryDirectory, RepositoryFile
from codeminer_tools.repositories.change import ChangeType
from django.db import transaction
from main.models.change import Change
from main.models.changeset import ChangeSet
from main.models.entity import Entity
from main.models.repository import Repository
from celery import shared_task
from neomodel import db

@shared_task
def scrape_repository(repository_id):
    repo_type_map = {
        Repository.RepositoryType.svn: svn.SVNRepository,
        Repository.RepositoryType.cvs: cvs.CVSRepository,
        Repository.RepositoryType.hg: hg.HgRepository,
        Repository.RepositoryType.git: git.GitRepository,
    }

    db_repository = Repository.objects.get(pk=repository_id)
    real_repository = repo_type_map[db_repository.repository_type](
        db_repository.origin,
        username = db_repository.username,
        password = db_repository.password,
        workspace = db_repository.workspace
    )

    for changeset in real_repository.walk_history():
        with db.transaction:
            db_changeset = ChangeSet(
                repository_id = db_repository.pk,
                identifier = changeset.identifier,
                author = changeset.author,
                message = changeset.message,
                timestamp = changeset.timestamp
            )
            db_changeset.save()
            for change in changeset.changes:
                db_previous_entities = []
                db_current_entity = None

                for previous_entity in change.previous_entities:
                    if previous_entity.path != None:
                        db_previous_entity = Entity(
                            type = EntityType.directory.value if type(previous_entity) is RepositoryDirectory else EntityType.file.value,
                            repository = db_repository.pk,
                            path = previous_entity.path,
                            revision = previous_entity.revision,
                        )
                        db_previous_entity.save()
                        db_ancestor_change = db_previous_entity.change_input.connect(db_changeset, {'action' : change.action.value})
                        db_ancestor_change.save()
                        db_previous_entities.append(db_previous_entity)

                if change.current_entity.path != None:
                    db_current_entity = Entity(
                        type = EntityType.directory.value if type(change.current_entity) is RepositoryDirectory else EntityType.file.value,
                        repository = db_repository.pk,
                        path = change.current_entity.path,
                        revision = change.current_entity.revision,
                    )
                    db_current_entity.save()
                    db_descendant_change = db_current_entity.change_output.connect(db_changeset, {'action' : change.action.value})
                    db_descendant_change.save()

                # If it's not an add or delete, create the ancestry link
                if db_current_entity is not None and db_previous_entities:
                    db_current_entity.ancestor.connect(db_previous_entity)

@shared_task
def build_repository_history(repository_id):
    db_repository = Repository.objects.get(pk=repository_id)
    for path in db_repository.get_unique_paths():
        build_path_history.apply_async(args=[repository_id, path])

@shared_task
def build_path_history(repository_id, path):
    with db.transaction:
        db_repository = Repository.objects.get(pk=repository_id)
        change_list = [x for x in db_repository.get_change_triples(path)]
        change_list += [x for x in db_repository.get_adds(path)]
        change_list += [x for x in db_repository.get_removes(path)]
        change_list.sort()

        changes = iter(change_list)
        change = next(changes, None)

        while change is not None:
            change_on_deck = next(changes, None)
            if change.destination_entity is not None:
                if change_on_deck is not None:
                    if change_on_deck.source_entity is not None:
                        change_on_deck.source_entity.ancestor.connect(change.destination_entity)
            change = change_on_deck

# @shared_task
# def build_repository_history(repository_id):
#     # For all repositories, adds can be identified by nodes with no connections
#     adds = Change.objects.filter(action=ChangeType.add.value, changeset__repository_id = repository_id)

#     for add in adds:
#         history = History()
#         build_change_history.apply_async(args=[add.pk, history])

# @shared_task
# def build_change_history(change_id, history):
#     change = Change.objects.prefetch_related(
#         'current_entity', 'previous_entity').get(pk=change_id)

#     changes = [change]
#     while change:
#         if change.action == ChangeType.remove.value:
#             break
#         else:
#             results = Change.objects.filter(
#                 previous_entity__revision__gt=change.current_entity.revision,
#                 previous_entity__path=change.current_entity.path).prefetch_related(
#                     'previous_entity', 'current_entity').order_by(
#                         'previous_entity__revision')
#             if results:
#                 print_me = True
#                 changes += [x for x in results]
#                 change = changes[-1]
#             else:
#                 break

#     with transaction.atomic():
#         history.save()
#         for x in changes:
#             x.history = history
#             x.save()

#         # print("\n New File \n")
#         # for x in changes:
#         #     if x.current_entity:
#         #         print("++ %s @ %s" % (x.current_entity.path, x.current_entity.revision))
#         #     else:
#         #         print("++ Deleted")