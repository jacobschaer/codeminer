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
        with transaction.atomic():
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
                    previous_file = None,
                    current_file = None,
                    action = change.action.value
                )
                db_change.save()
                db_previous_file = File(
                    repository = db_repository,
                    path = change.previous_file.path,
                    revision = change.previous_file.revision,
                )
                db_current_file = File(
                    repository = db_repository,
                    path = change.current_file.path,
                    revision = change.current_file.revision,
                )
                db_current_file.save()
                db_previous_file.save()
                db_change.previous_file = db_previous_file
                db_change.current_file = db_current_file
                db_change.save()

@shared_task
def build_repository_history(repository_id):
    adds = Change.objects.filter(action=ChangeType.add.value, changeset__repository_id = repository_id)

    for add in adds:
        build_change_history(add.pk)

@shared_task
def build_change_history(change_id, history=None):
    next_change = None

    with transaction.atomic():
        change = Change.objects.prefetch_related(
            'changeset__repository', 'current_file', 'current_file').get(pk=change_id)
        if history is None:
            history = History(repository=change.changeset.repository)
            history.save()
            change.history = history

        if change.action != ChangeType.remove:
            try:
                next_change = Change.objects.filter(previous_file__revision__gt=change.current_file.revision,
                                                    previous_file__path=change.current_file.path).order_by('previous_file__revision').first()
            except ValueError:
                print("Something is wrong with a commit")
        # Fix file revisions as necessary
        # ..
        # ..

    if next_change is not None:
        print("Mapping: {p1}@{r1} to {p2}@{r2}".format(
            p1=change.current_file.path if change.current_file else None, r1=change.current_file.revision if change.current_file else None,
            p2=next_change.previous_file.path if next_change.previous_file else None, r2=next_change.previous_file.revision if next_change.previous_file else None))
        build_change_history(next_change.pk, history=history)