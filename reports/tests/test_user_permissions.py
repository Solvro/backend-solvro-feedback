import pytest
from django.contrib.auth.models import User

from reports.models import Application


@pytest.mark.django_db
class TestUserAppPermissions:
    def test_accessible_users_m2m(self):
        app = Application.objects.create(
            name="Permission App",
            repo_url="https://github.com/test/repo",
        )
        user = User.objects.create_user(username="testuser", email="test@example.com")
        app.accessible_users.add(user)
        assert app.accessible_users.count() == 1
        assert user in app.accessible_users.all()

    def test_accessible_users_reverse_relation(self):
        app = Application.objects.create(
            name="Reverse Permission App",
            repo_url="https://github.com/test/repo",
        )
        user = User.objects.create_user(
            username="reverseuser", email="reverse@example.com"
        )
        app.accessible_users.add(user)
        assert user.accessible_applications.count() == 1
        assert app in user.accessible_applications.all()

    def test_accessible_users_empty_by_default(self):
        app = Application.objects.create(
            name="Empty Permission App",
            repo_url="https://github.com/test/repo",
        )
        assert app.accessible_users.count() == 0

    def test_accessible_users_multiple_users(self):
        app = Application.objects.create(
            name="Multiple Permission App",
            repo_url="https://github.com/test/repo",
        )
        user1 = User.objects.create_user(username="user1", email="user1@example.com")
        user2 = User.objects.create_user(username="user2", email="user2@example.com")
        app.accessible_users.add(user1, user2)
        assert app.accessible_users.count() == 2

    def test_accessible_users_remove(self):
        app = Application.objects.create(
            name="Remove Permission App",
            repo_url="https://github.com/test/repo",
        )
        user = User.objects.create_user(
            username="removeuser", email="remove@example.com"
        )
        app.accessible_users.add(user)
        app.accessible_users.remove(user)
        assert app.accessible_users.count() == 0

    def test_accessible_users_clear(self):
        app = Application.objects.create(
            name="Clear Permission App",
            repo_url="https://github.com/test/repo",
        )
        user1 = User.objects.create_user(username="clear1", email="clear1@example.com")
        user2 = User.objects.create_user(username="clear2", email="clear2@example.com")
        app.accessible_users.add(user1, user2)
        app.accessible_users.clear()
        assert app.accessible_users.count() == 0

    def test_accessible_users_set(self):
        app = Application.objects.create(
            name="Set Permission App",
            repo_url="https://github.com/test/repo",
        )
        user1 = User.objects.create_user(username="set1", email="set1@example.com")
        user2 = User.objects.create_user(username="set2", email="set2@example.com")
        user3 = User.objects.create_user(username="set3", email="set3@example.com")
        app.accessible_users.add(user1)
        app.accessible_users.set([user2, user3])
        assert app.accessible_users.count() == 2
        assert user1 not in app.accessible_users.all()
        assert user2 in app.accessible_users.all()
        assert user3 in app.accessible_users.all()
