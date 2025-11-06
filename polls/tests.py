from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from polls.models import Poll, Choice, Vote
from io import StringIO
from django.core.management import call_command


class PollModelTests(TestCase):
    """Test Poll model methods and properties"""

    def setUp(self):
        """Create test polls"""
        self.active_poll = Poll.objects.create(
            question="Active poll?",
            expires_at=timezone.now() + timedelta(days=30)
        )
        Choice.objects.create(poll=self.active_poll, choice_text="Yes")
        Choice.objects.create(poll=self.active_poll, choice_text="No")

    def test_poll_creation_with_default_expiration(self):
        """Test that new polls get default 90-day expiration"""
        poll = Poll.objects.create(question="Test poll?")
        self.assertIsNotNone(poll.expires_at)
        # Should expire in approximately 90 days (allow 1 second margin)
        delta = poll.expires_at - timezone.now()
        self.assertAlmostEqual(delta.days, 90, delta=1)

    def test_poll_creation_with_custom_expiration(self):
        """Test creating poll with custom expiration date"""
        expires = timezone.now() + timedelta(days=7)
        poll = Poll.objects.create(
            question="Test poll?",
            expires_at=expires
        )
        self.assertEqual(poll.expires_at, expires)

    def test_poll_creation_without_expiration(self):
        """Test creating poll that never expires"""
        poll = Poll(question="Test poll?", expires_at=None)
        poll.save()
        self.assertIsNone(poll.expires_at)

    def test_is_expired_property(self):
        """Test is_expired property"""
        # Active poll (expires in future)
        self.assertFalse(self.active_poll.is_expired)

        # Expired poll
        expired_poll = Poll.objects.create(
            question="Expired poll?",
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(expired_poll.is_expired)

        # No expiration
        no_expire_poll = Poll(question="No expire?", expires_at=None)
        no_expire_poll.save()
        self.assertFalse(no_expire_poll.is_expired)

    def test_days_until_expiration(self):
        """Test days_until_expiration property"""
        # Active poll
        days = self.active_poll.days_until_expiration
        self.assertAlmostEqual(days, 30, delta=1)

        # Expired poll
        expired_poll = Poll.objects.create(
            question="Expired?",
            expires_at=timezone.now() - timedelta(days=5)
        )
        self.assertEqual(expired_poll.days_until_expiration, 0)

        # No expiration
        no_expire_poll = Poll(question="No expire?", expires_at=None)
        no_expire_poll.save()
        self.assertIsNone(no_expire_poll.days_until_expiration)

    def test_soft_delete(self):
        """Test soft deletion"""
        self.assertFalse(self.active_poll.is_soft_deleted)
        self.assertIsNone(self.active_poll.deleted_at)

        self.active_poll.soft_delete()

        self.assertTrue(self.active_poll.is_soft_deleted)
        self.assertIsNotNone(self.active_poll.deleted_at)

    def test_restore_soft_deleted_poll(self):
        """Test restoring a soft-deleted poll"""
        self.active_poll.soft_delete()
        self.assertTrue(self.active_poll.is_soft_deleted)

        self.active_poll.restore()

        self.assertFalse(self.active_poll.is_soft_deleted)
        self.assertIsNone(self.active_poll.deleted_at)

    def test_days_until_permanent_deletion(self):
        """Test days_until_permanent_deletion property"""
        self.assertIsNone(self.active_poll.days_until_permanent_deletion)

        self.active_poll.soft_delete()
        days = self.active_poll.days_until_permanent_deletion
        self.assertAlmostEqual(days, 30, delta=1)


class PollManagerTests(TestCase):
    """Test custom Poll managers"""

    def setUp(self):
        """Create test polls with different states"""
        # Active poll
        self.active_poll = Poll.objects.create(
            question="Active?",
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Expired poll
        self.expired_poll = Poll.objects.create(
            question="Expired?",
            expires_at=timezone.now() - timedelta(days=1)
        )

        # Soft-deleted poll
        self.deleted_poll = Poll.objects.create(
            question="Deleted?",
            expires_at=timezone.now() + timedelta(days=30)
        )
        self.deleted_poll.soft_delete()

    def test_default_manager_includes_all_polls(self):
        """Test that Poll.objects includes all polls"""
        self.assertEqual(Poll.objects.count(), 3)

    def test_active_objects_excludes_soft_deleted(self):
        """Test that active_objects excludes soft-deleted polls"""
        active_polls = Poll.active_objects.all()
        self.assertEqual(active_polls.count(), 2)
        self.assertNotIn(self.deleted_poll, active_polls)

    def test_active_method_excludes_expired_and_deleted(self):
        """Test that active() excludes both expired and deleted polls"""
        truly_active = Poll.active_objects.active()
        self.assertEqual(truly_active.count(), 1)
        self.assertIn(self.active_poll, truly_active)
        self.assertNotIn(self.expired_poll, truly_active)
        self.assertNotIn(self.deleted_poll, truly_active)


class PollViewTests(TestCase):
    """Test poll views with lifecycle management"""

    def setUp(self):
        """Create test client and polls"""
        self.client = Client()

        # Active poll
        self.active_poll = Poll.objects.create(
            question="Active poll?",
            expires_at=timezone.now() + timedelta(days=30),
            public_results=True
        )
        Choice.objects.create(poll=self.active_poll, choice_text="Yes")
        Choice.objects.create(poll=self.active_poll, choice_text="No")

        # Expired poll
        self.expired_poll = Poll.objects.create(
            question="Expired poll?",
            expires_at=timezone.now() - timedelta(days=1)
        )
        Choice.objects.create(poll=self.expired_poll, choice_text="Yes")

        # Soft-deleted poll
        self.deleted_poll = Poll.objects.create(
            question="Deleted poll?",
            expires_at=timezone.now() + timedelta(days=30)
        )
        Choice.objects.create(poll=self.deleted_poll, choice_text="Yes")
        self.deleted_poll.soft_delete()

    def test_create_poll_with_expiration(self):
        """Test creating poll with custom expiration"""
        response = self.client.post(reverse('create_poll'), {
            'question': 'New poll?',
            'choices[]': ['Choice 1', 'Choice 2'],
            'expiration_days': '7',
            'is_anonymous': 'on'
        })

        self.assertEqual(response.status_code, 200)
        poll = Poll.objects.get(question='New poll?')
        self.assertIsNotNone(poll.expires_at)

        # Should expire in approximately 7 days
        delta = poll.expires_at - timezone.now()
        self.assertAlmostEqual(delta.days, 7, delta=1)

    def test_create_poll_without_expiration(self):
        """Test creating poll that never expires"""
        response = self.client.post(reverse('create_poll'), {
            'question': 'Never expire poll?',
            'choices[]': ['Choice 1', 'Choice 2'],
            'expiration_days': 'never',
            'is_anonymous': 'on'
        })

        self.assertEqual(response.status_code, 200)
        poll = Poll.objects.get(question='Never expire poll?')
        self.assertIsNone(poll.expires_at)

    def test_vote_page_active_poll(self):
        """Test accessing vote page for active poll"""
        response = self.client.get(
            reverse('vote_page', args=[self.active_poll.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_poll.question)

    def test_vote_page_expired_poll(self):
        """Test that expired polls redirect with error"""
        response = self.client.get(
            reverse('vote_page', args=[self.expired_poll.slug])
        )
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_vote_page_soft_deleted_poll(self):
        """Test that soft-deleted polls return 404"""
        response = self.client.get(
            reverse('vote_page', args=[self.deleted_poll.slug])
        )
        self.assertEqual(response.status_code, 404)

    def test_voting_on_expired_poll(self):
        """Test that voting on expired poll is prevented"""
        choice = self.expired_poll.choices.first()
        response = self.client.post(
            reverse('vote', args=[self.expired_poll.slug]),
            {'choices': str(choice.id)}
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        choice.refresh_from_db()
        self.assertEqual(choice.votes, 0)  # No vote recorded

    def test_admin_results_shows_expired_poll(self):
        """Test that admin can still view expired polls"""
        response = self.client.get(
            reverse('admin_results', args=[self.expired_poll.admin_token])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.expired_poll.question)

    def test_admin_results_shows_soft_deleted_poll(self):
        """Test that admin can still view soft-deleted polls"""
        response = self.client.get(
            reverse('admin_results', args=[self.deleted_poll.admin_token])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.deleted_poll.question)

    def test_soft_delete_poll(self):
        """Test soft deletion via view"""
        response = self.client.post(
            reverse('delete_poll', args=[self.active_poll.admin_token]),
            {'action': 'soft_delete'}
        )
        self.assertEqual(response.status_code, 302)

        self.active_poll.refresh_from_db()
        self.assertTrue(self.active_poll.is_soft_deleted)

    def test_hard_delete_poll(self):
        """Test permanent deletion via view"""
        poll_id = self.active_poll.id
        response = self.client.post(
            reverse('delete_poll', args=[self.active_poll.admin_token]),
            {'action': 'hard_delete'}
        )
        self.assertEqual(response.status_code, 302)

        # Poll should be completely gone
        self.assertFalse(Poll.objects.filter(id=poll_id).exists())

    def test_restore_soft_deleted_poll(self):
        """Test restoring soft-deleted poll via view"""
        response = self.client.post(
            reverse('delete_poll', args=[self.deleted_poll.admin_token]),
            {'action': 'restore'}
        )
        self.assertEqual(response.status_code, 302)

        self.deleted_poll.refresh_from_db()
        self.assertFalse(self.deleted_poll.is_soft_deleted)

    def test_public_results_shows_expiration_warning(self):
        """Test that results page shows expiration info"""
        # Poll expiring soon
        soon_poll = Poll.objects.create(
            question="Expiring soon?",
            expires_at=timezone.now() + timedelta(days=3),
            public_results=True
        )
        Choice.objects.create(poll=soon_poll, choice_text="Yes")

        response = self.client.get(
            reverse('public_results', args=[soon_poll.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Expiring Soon')


class CleanupCommandTests(TestCase):
    """Test the cleanup_polls management command"""

    def setUp(self):
        """Create test polls in various states"""
        # Expired poll (should be soft-deleted)
        self.expired_poll = Poll.objects.create(
            question="Expired?",
            expires_at=timezone.now() - timedelta(days=1)
        )

        # Old soft-deleted poll (should be permanently deleted)
        self.old_deleted_poll = Poll.objects.create(
            question="Old deleted?",
            expires_at=timezone.now() + timedelta(days=30),
            deleted_at=timezone.now() - timedelta(days=31)
        )

        # Recent soft-deleted poll (should be kept)
        self.recent_deleted_poll = Poll.objects.create(
            question="Recent deleted?",
            expires_at=timezone.now() + timedelta(days=30),
            deleted_at=timezone.now() - timedelta(days=5)
        )

        # Active poll (should not be touched)
        self.active_poll = Poll.objects.create(
            question="Active?",
            expires_at=timezone.now() + timedelta(days=30)
        )

    def test_cleanup_dry_run(self):
        """Test cleanup command in dry-run mode"""
        out = StringIO()
        call_command('cleanup_polls', '--dry-run', stdout=out)

        # Check that expired poll is identified
        self.assertIn('1 expired poll(s)', out.getvalue())

        # Check that old deleted poll is identified
        self.assertIn('1 soft-deleted poll(s) ready for permanent deletion', out.getvalue())

        # Verify no changes were made
        self.expired_poll.refresh_from_db()
        self.assertFalse(self.expired_poll.is_soft_deleted)

        self.assertTrue(Poll.objects.filter(id=self.old_deleted_poll.id).exists())

    def test_cleanup_soft_delete_expired(self):
        """Test that cleanup soft-deletes expired polls"""
        call_command('cleanup_polls')

        self.expired_poll.refresh_from_db()
        self.assertTrue(self.expired_poll.is_soft_deleted)

    def test_cleanup_permanent_delete_old(self):
        """Test that cleanup permanently deletes old soft-deleted polls"""
        old_id = self.old_deleted_poll.id
        call_command('cleanup_polls')

        self.assertFalse(Poll.objects.filter(id=old_id).exists())

    def test_cleanup_keeps_recent_deleted(self):
        """Test that cleanup keeps recent soft-deleted polls"""
        call_command('cleanup_polls')

        self.assertTrue(Poll.objects.filter(id=self.recent_deleted_poll.id).exists())

    def test_cleanup_keeps_active(self):
        """Test that cleanup doesn't touch active polls"""
        call_command('cleanup_polls')

        self.active_poll.refresh_from_db()
        self.assertFalse(self.active_poll.is_soft_deleted)

    def test_cleanup_force_expired(self):
        """Test force deletion of expired polls"""
        expired_id = self.expired_poll.id
        call_command('cleanup_polls', '--force-expired')

        # Should be completely deleted, not soft-deleted
        self.assertFalse(Poll.objects.filter(id=expired_id).exists())

    def test_cleanup_statistics(self):
        """Test that cleanup command shows statistics"""
        out = StringIO()
        call_command('cleanup_polls', '--dry-run', stdout=out)
        output = out.getvalue()

        self.assertIn('Database Statistics:', output)
        self.assertIn('Total polls:', output)
        self.assertIn('Active polls:', output)
        self.assertIn('Soft-deleted polls:', output)


class PollCascadeDeletionTests(TestCase):
    """Test that related objects are properly deleted"""

    def setUp(self):
        """Create poll with votes"""
        self.poll = Poll.objects.create(
            question="Test?",
            expires_at=timezone.now() + timedelta(days=30)
        )
        self.choice1 = Choice.objects.create(poll=self.poll, choice_text="Yes")
        self.choice2 = Choice.objects.create(poll=self.poll, choice_text="No")

        # Create some votes
        Vote.objects.create(
            poll=self.poll,
            choice=self.choice1,
            ip_address="127.0.0.1",
            cookie_token="test-token-1"
        )
        Vote.objects.create(
            poll=self.poll,
            choice=self.choice2,
            ip_address="127.0.0.2",
            cookie_token="test-token-2"
        )

    def test_soft_delete_keeps_related_objects(self):
        """Test that soft delete doesn't cascade to related objects"""
        self.poll.soft_delete()

        # Choices and votes should still exist
        self.assertEqual(Choice.objects.filter(poll=self.poll).count(), 2)
        self.assertEqual(Vote.objects.filter(poll=self.poll).count(), 2)

    def test_hard_delete_cascades_to_related_objects(self):
        """Test that hard delete removes related objects"""
        poll_id = self.poll.id
        self.poll.delete()

        # Choices and votes should be deleted
        self.assertEqual(Choice.objects.filter(poll_id=poll_id).count(), 0)
        self.assertEqual(Vote.objects.filter(poll_id=poll_id).count(), 0)


class PollExpirationEdgeCaseTests(TestCase):
    """Test edge cases for poll expiration"""

    def test_poll_expiring_exactly_now(self):
        """Test poll that expires exactly at current time"""
        poll = Poll.objects.create(
            question="Test?",
            expires_at=timezone.now()
        )
        # Should be considered expired
        self.assertTrue(poll.is_expired)

    def test_poll_with_none_expiration(self):
        """Test poll with null expiration (never expires)"""
        poll = Poll(question="Test?", expires_at=None)
        poll.save()
        self.assertFalse(poll.is_expired)
        self.assertIsNone(poll.days_until_expiration)

    def test_multiple_soft_deletes(self):
        """Test that multiple soft deletes don't cause issues"""
        poll = Poll.objects.create(question="Test?")
        first_delete_time = poll.deleted_at

        poll.soft_delete()
        second_delete_time = poll.deleted_at

        poll.soft_delete()
        third_delete_time = poll.deleted_at

        # deleted_at should update each time
        self.assertIsNotNone(third_delete_time)
        self.assertNotEqual(first_delete_time, third_delete_time)

    def test_restore_non_deleted_poll(self):
        """Test restoring a poll that wasn't deleted"""
        poll = Poll.objects.create(question="Test?")
        poll.restore()  # Should not raise error
        self.assertIsNone(poll.deleted_at)
