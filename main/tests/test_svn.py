from django.test import TestCase, override_settings
from main.models import Repository, File, Change, ChangeSet, History
from codeminer_tools.repositories import SVNRepository
from codeminer_tools.repositories.change import ChangeType
from codeminer_tools.repositories.test.test_utils import run_shell_command
from main import tasks
import tempfile
import os
import shutil
import mock
from datetime import datetime, timedelta, timezone

class SubversionTest(TestCase):
    def setUp(self):
        self.repo_name = 'test_repo'
        self.server_root = tempfile.mkdtemp()
        self.checkout_root = tempfile.mkdtemp()
        self.repo_url = 'file://{server_root}/{repo_name}'.format(
            server_root=self.server_root, repo_name=self.repo_name)
        self.repo_working_directory = os.path.join(
            self.checkout_root, self.repo_name)
        run_shell_command('svnadmin create {repo_name}'.format(
            repo_name=self.repo_name), cwd=self.server_root)
        run_shell_command('svn co "{repo_url}"'.format(repo_url=self.repo_url),
                          cwd=self.checkout_root)
        self.repository_object = SVNRepository(self.repo_working_directory)

    def tearDown(self):
        shutil.rmtree(self.server_root)
        shutil.rmtree(self.checkout_root)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_linear_alive_history(self):
        ######## Setup step
        with open(os.path.join(self.repo_working_directory, 'a.txt'), 'w') as f:
            f.write('')
        self.repository_object.client.add('a.txt')
        self.repository_object.client.commit(message="Test 1", username='test')
        with open(os.path.join(self.repo_working_directory, 'a.txt'), 'w') as f:
            f.write('a')
        self.repository_object.client.commit(message="Test 2", username='test')
        with open(os.path.join(self.repo_working_directory, 'a.txt'), 'w') as f:
            f.write('b')
        self.repository_object.client.commit(message="Test 3", username='test')
        self.repository_object.client.update()
        #########

        sut = Repository(name='test_repo', repository_type=Repository.RepositoryType.svn.value, origin=self.repo_working_directory)
        sut.save()

        tasks.scrape_repository(sut.pk)

        # Verify repository
        changesets = list(sut.changeset_set.prefetch_related(
            'change_set', 'change_set__current_file', 'change_set__previous_files').order_by('change__current_file__revision'))

        self.assertEqual(len(changesets), 3)

        self.assertEqual(changesets[0].message, 'Test 1')
        self.assertTrue(abs(changesets[0].timestamp - datetime.now(timezone.utc)) <= timedelta(seconds=5))
        self.assertEqual(changesets[0].author, 'test')
        self.assertEqual(changesets[0].identifier, '1')

        changes = list(changesets[0].change_set.all())
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].action, ChangeType.add.value)
        self.assertEqual(list(changes[0].previous_files.all()), [])
        self.assertEqual(changes[0].current_file.path, 'a.txt')
        self.assertEqual(changes[0].current_file.revision, '1')

        self.assertEqual(changesets[1].message, 'Test 2')
        self.assertLess(changesets[0].timestamp, changesets[1].timestamp)
        self.assertEqual(changesets[1].author, 'test')
        self.assertEqual(changesets[1].identifier, '2')

        changes = list(changesets[1].change_set.all())
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].action, ChangeType.add.modify.value)
        self.assertEqual(changes[0].previous_files.count(), 1)
        self.assertEqual(changes[0].previous_files.all()[0], changesets[0].change_set.all()[0].current_file)
        self.assertEqual(changes[0].current_file.path, 'a.txt')
        self.assertEqual(changes[0].current_file.revision, '2')

        self.assertEqual(changesets[2].message, 'Test 3')
        self.assertLess(changesets[1].timestamp, changesets[2].timestamp)
        self.assertEqual(changesets[2].author, 'test')
        self.assertEqual(changesets[2].identifier, '3')

        changes = list(changesets[2].change_set.all())
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].action, ChangeType.add.modify.value)
        self.assertEqual(changes[0].previous_files.count(), 1)
        self.assertEqual(changes[0].previous_files.all()[0], changesets[1].change_set.all()[0].current_file)
        self.assertEqual(changes[0].current_file.path, 'a.txt')
        self.assertEqual(changes[0].current_file.revision, '3')

        # Verify history
        # tasks.build_repository_history(sut.pk)
        # histories = list(History.objects.all())
        # self.assertEqual(len(histories), 1)
        # self.assertEqual()

        # Verify only necessary file revisions are stored and have appropriate history
        files = [(x.path, x.revision) for x in File.objects.order_by('revision')]
        self.assertEqual(files, [
                ('a.txt', '1'), ('a.txt', '2'), ('a.txt', '3')
            ])

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_merge_history(self):
        pass

if __name__ == '__main__':
    unittest.main()