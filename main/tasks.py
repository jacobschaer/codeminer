from codeminer_tools.repositories import cvs, git, hg, svn
from codeminer_tools.repositories.change import ChangeType
from django.db import transaction
from main.models.change import Change
from main.models.changeset import ChangeSet
from main.models.file import File
from main.models.repository import Repository
from main.models.history import History
from celery import shared_task

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
        import_changeset.apply_async(args=[repository_id, changeset])

@shared_task
def import_changeset(repository_id, changeset):
    with transaction.atomic():
        db_repository = Repository.objects.get(pk=repository_id)
        db_changeset = ChangeSet(
            repository = db_repository,
            identifier = changeset.identifier,
            author = changeset.author,
            message = changeset.message,
            timestamp = changeset.timestamp
        )
        db_changeset.save()
        for change in changeset.changes:
            db_change = Change(
                changeset = db_changeset,
                current_file = None,
                action = change.action.value
            )
            db_change.save()
            for previous_file in change.previous_files:
                db_previous_file, created = File.objects.get_or_create(
                    repository = db_repository,
                    path = previous_file.path,
                    revision = previous_file.revision,
                )
                if created:
                    db_previous_file.save()
                db_change.previous_files.add(db_previous_file)
            if change.current_file.path != None:                
                db_current_file, created = File.objects.get_or_create(
                    repository = db_repository,
                    path = change.current_file.path,
                    revision = change.current_file.revision,
                )
                if created:
                    db_current_file.save()
                db_change.current_file = db_current_file
            db_change.save()

@shared_task
def build_repository_history(repository_id):
    adds = Change.objects.filter(action=ChangeType.add.value, changeset__repository_id=repository_id)

    for add in adds:
        build_change_history_from_add.apply_async(args=[add.pk])

@shared_task
def build_change_history_from_add(change_id):
    change = Change.objects.prefetch_related(
        'current_file', 'previous_file', 'current_file__history', 'previous_file__history').get(pk=change_id)

    file_at_add = change.previous_file
    file_at_head = change.current_file

    history_files = [file_at_add, file_at_head]

    # Iterate over all files with the same name as the "add". Each loop is a new history
    # A history "ends" with one of the following:
    # - file's path changes
    # - file is deleted
    # - file revision is current repository head
    while True:       
        # Filters
        filters = {
            'revision__gt' : file_at_tail.revision, # Files after the known head
            'path' : file_at_head.path,             # Files must have the same path as current head          
        }

        # Look for future deletes - lineages must stop at these
        delete_change = Change.objects.filter(
            action=ChangeType.remove.value, previous_file__revision__gt=file_at_head.revision).order_by('revision').first()

        if delete_change:
            filters['revision__lte'] = delete_change.previous_file.revision # File revisions after delete are part of a different history

        # Run main query
        results = File.objects.filter(**filters).prefetch_related(
                'history, change_set').order_by('revision')

        # Update histories
        history = History()
        history.save()

        if results:
            history_files += [x for x in results]
            history = History()
            history.save()
            for x in history_files:
                x.history.add(history)

            # Update history head
            file_at_head = history[-1]
            history.head_file = file_at_head


            # Look to see if there's any more to this lineage
            for change in x.change_set:
                if change.action == ChangeType.remove.value:
                    pass

        else:
            break

        # print("\n New File \n")
        # for x in changes:
        #     if x.current_file:
        #         print("++ %s @ %s" % (x.current_file.path, x.current_file.revision))
        #     else:
        #         print("++ Deleted")