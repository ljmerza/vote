from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from polls.models import Poll


class Command(BaseCommand):
    help = 'Clean up expired and soft-deleted polls'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--force-expired',
            action='store_true',
            help='Immediately delete expired polls (skip soft delete)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_expired = options['force_expired']
        now = timezone.now()

        self.stdout.write(self.style.NOTICE(f'Starting poll cleanup at {now}'))
        self.stdout.write(self.style.NOTICE(f'Dry run: {dry_run}'))
        self.stdout.write('')

        # 1. Find and soft-delete expired polls (that aren't already deleted)
        expired_polls = Poll.objects.filter(
            expires_at__lte=now,
            deleted_at__isnull=True
        )
        expired_count = expired_polls.count()

        if expired_count > 0:
            self.stdout.write(self.style.WARNING(f'Found {expired_count} expired poll(s):'))
            for poll in expired_polls:
                self.stdout.write(f'  - "{poll.question}" (expired: {poll.expires_at})')

            if not dry_run:
                if force_expired:
                    expired_polls.delete()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Permanently deleted {expired_count} expired poll(s)'))
                else:
                    for poll in expired_polls:
                        poll.soft_delete()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Soft-deleted {expired_count} expired poll(s)'))
        else:
            self.stdout.write(self.style.SUCCESS('No expired polls found'))

        self.stdout.write('')

        # 2. Find and permanently delete soft-deleted polls older than 30 days
        permanent_deletion_threshold = now - timedelta(days=30)
        old_deleted_polls = Poll.objects.filter(
            deleted_at__lte=permanent_deletion_threshold
        )
        old_deleted_count = old_deleted_polls.count()

        if old_deleted_count > 0:
            self.stdout.write(self.style.WARNING(f'Found {old_deleted_count} soft-deleted poll(s) ready for permanent deletion:'))
            for poll in old_deleted_polls:
                days_deleted = (now - poll.deleted_at).days
                self.stdout.write(f'  - "{poll.question}" (deleted {days_deleted} days ago)')

            if not dry_run:
                # Get stats before deletion
                total_votes = sum(poll.total_votes() for poll in old_deleted_polls)
                total_choices = sum(poll.choices.count() for poll in old_deleted_polls)

                old_deleted_polls.delete()
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Permanently deleted {old_deleted_count} poll(s), '
                    f'{total_choices} choice(s), and {total_votes} vote record(s)'
                ))
        else:
            self.stdout.write(self.style.SUCCESS('No old soft-deleted polls found'))

        self.stdout.write('')

        # 3. Show statistics
        total_polls = Poll.objects.count()
        active_polls = Poll.active_objects.count()
        soft_deleted_polls = Poll.objects.filter(deleted_at__isnull=False).count()

        self.stdout.write(self.style.NOTICE('Database Statistics:'))
        self.stdout.write(f'  Total polls: {total_polls}')
        self.stdout.write(f'  Active polls: {active_polls}')
        self.stdout.write(f'  Soft-deleted polls: {soft_deleted_polls}')

        # Show polls approaching expiration
        week_from_now = now + timedelta(days=7)
        expiring_soon = Poll.active_objects.filter(
            expires_at__lte=week_from_now,
            expires_at__gt=now
        ).count()

        if expiring_soon > 0:
            self.stdout.write(self.style.WARNING(f'  Polls expiring within 7 days: {expiring_soon}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Cleanup complete!'))

        if dry_run:
            self.stdout.write(self.style.NOTICE('(This was a dry run - no changes were made)'))
