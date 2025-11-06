# Poll Lifecycle Management System

## Overview

This Django polling application now includes comprehensive lifecycle management to prevent unlimited database growth while maintaining data safety and user control.

## Features Implemented

### 1. Automatic Expiration System
- **Default Expiration**: All new polls automatically expire after 90 days
- **Configurable Duration**: Users can choose expiration periods when creating polls:
  - 7 days
  - 30 days
  - 90 days (default)
  - 180 days (6 months)
  - 365 days (1 year)
  - Never expire (optional)

### 2. Soft Delete with Grace Period
- **30-Day Grace Period**: When polls are deleted, they enter a soft-deleted state for 30 days
- **Restore Capability**: Soft-deleted polls can be restored within the grace period
- **Automatic Cleanup**: After 30 days, soft-deleted polls are permanently removed
- **Safety Net**: Prevents accidental data loss

### 3. Management Command for Cleanup
A Django management command handles automatic cleanup operations:

```bash
# Dry run (shows what would be deleted without actually deleting)
python manage.py cleanup_polls --dry-run

# Normal run (performs cleanup)
python manage.py cleanup_polls

# Force immediate deletion of expired polls (skip soft delete)
python manage.py cleanup_polls --force-expired
```

**What it does:**
1. Finds expired polls and soft-deletes them (or hard-deletes with `--force-expired`)
2. Permanently deletes soft-deleted polls older than 30 days
3. Shows database statistics and polls expiring soon

### 4. Enhanced Admin Dashboard
The Django admin interface now shows:
- **Lifecycle Status**: Visual indicators for active/expired/deleted polls
- **Days Until Expiration**: Color-coded warnings for polls expiring soon
- **Lifecycle Information**: Detailed timeline of poll creation, expiration, and deletion
- **Bulk Actions**:
  - Soft delete selected polls
  - Restore soft-deleted polls
  - Extend expiration by 90 days

### 5. User-Visible Expiration Warnings
- Polls display expiration dates in results pages
- Warning alerts for polls expiring within 7 days
- Error messages when attempting to vote on expired polls
- Visual indicators throughout the interface

## Database Schema Changes

### New Poll Model Fields

```python
expires_at = DateTimeField(null=True, blank=True)
# When the poll will automatically expire and stop accepting votes

deleted_at = DateTimeField(null=True, blank=True)
# Soft deletion timestamp; null = active, set = soft-deleted
```

### Custom Manager

```python
Poll.objects          # All polls (including deleted)
Poll.active_objects   # Only non-deleted polls
Poll.active_objects.active()  # Non-deleted AND non-expired polls
```

## Automated Cleanup Setup

### Option 1: Cron Job (Linux/Unix)

Edit your crontab:
```bash
crontab -e
```

Add this line to run cleanup daily at 2 AM:
```cron
0 2 * * * cd /path/to/project && /path/to/venv/bin/python manage.py cleanup_polls
```

### Option 2: Systemd Timer (Linux)

Create `/etc/systemd/system/poll-cleanup.service`:
```ini
[Unit]
Description=Clean up expired and soft-deleted polls
After=network.target

[Service]
Type=oneshot
User=youruser
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python manage.py cleanup_polls
```

Create `/etc/systemd/system/poll-cleanup.timer`:
```ini
[Unit]
Description=Run poll cleanup daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable poll-cleanup.timer
sudo systemctl start poll-cleanup.timer
```

### Option 3: Celery Beat (if using Celery)

Add to your Celery configuration:
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-polls-daily': {
        'task': 'polls.tasks.cleanup_polls',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

Create `polls/tasks.py`:
```python
from celery import shared_task
from django.core.management import call_command

@shared_task
def cleanup_polls():
    call_command('cleanup_polls')
```

## API Reference

### Poll Model Methods

```python
poll.soft_delete()           # Mark poll as soft-deleted
poll.restore()               # Restore a soft-deleted poll
poll.is_expired             # Property: Check if poll expired
poll.is_soft_deleted        # Property: Check if soft-deleted
poll.days_until_expiration  # Property: Days until expiration
poll.days_until_permanent_deletion  # Property: Days until hard delete
```

### View Behavior

- **Public views** (`vote_page`, `vote`, `public_results`): Only show active, non-deleted, non-expired polls
- **Admin views** (`admin_results`, `edit_poll`, `delete_poll`): Show all polls including soft-deleted
- **Expired poll access**: Returns error message and redirects to create poll page

## Testing the Implementation

### 1. Test Expiration Settings
```python
# Create a poll with custom expiration
from django.utils import timezone
from datetime import timedelta
from polls.models import Poll

poll = Poll.objects.create(
    question="Test poll",
    expires_at=timezone.now() + timedelta(days=7)
)
print(f"Expires in {poll.days_until_expiration} days")
```

### 2. Test Soft Delete
```python
poll.soft_delete()
print(f"Soft deleted: {poll.is_soft_deleted}")
print(f"Days until permanent: {poll.days_until_permanent_deletion}")

poll.restore()
print(f"Restored: {not poll.is_soft_deleted}")
```

### 3. Test Cleanup Command
```bash
# See what would be cleaned up
python manage.py cleanup_polls --dry-run

# Actually perform cleanup
python manage.py cleanup_polls
```

## Migration Path for Existing Polls

Existing polls without `expires_at` will:
1. Have `expires_at` set to NULL initially
2. **Option A**: Set default expiration on first save (90 days from now)
3. **Option B**: Leave as NULL (never expire) and let admins set manually

To bulk-set expiration for existing polls:
```python
from django.utils import timezone
from datetime import timedelta
from polls.models import Poll

# Set 90-day expiration for all polls without expiration
Poll.objects.filter(expires_at__isnull=True).update(
    expires_at=timezone.now() + timedelta(days=90)
)
```

## Monitoring and Metrics

### Check Database Health
```bash
python manage.py cleanup_polls --dry-run
```

### Django Admin Dashboard
Navigate to `/admin/polls/poll/` to see:
- Total polls by status
- Polls expiring soon
- Soft-deleted polls
- Database growth trends

## Best Practices

1. **Run cleanup daily** during low-traffic hours (e.g., 2-4 AM)
2. **Monitor logs** from cleanup command for unusual patterns
3. **Set appropriate expiration** based on poll type:
   - Quick surveys: 7-30 days
   - Event polls: Match event date
   - Long-term polls: 180-365 days
4. **Communicate expiration** to users creating polls
5. **Backup before cleanup** in production (optional safety measure)

## Troubleshooting

### Polls Not Being Cleaned Up
- Check if cron/systemd timer is running
- Verify command works manually: `python manage.py cleanup_polls`
- Check server timezone matches database timezone

### Soft-Deleted Polls Visible
- Ensure views use `Poll.active_objects` manager
- Check for direct queries using `Poll.objects.all()`

### Expiration Not Working
- Verify `expires_at` is set correctly
- Check timezone settings in Django settings
- Ensure `is_expired` property logic is correct

## Future Enhancements

Potential improvements for consideration:
1. **Email notifications** before poll expiration
2. **Export to CSV/JSON** before permanent deletion
3. **Archival to cold storage** instead of deletion
4. **Usage analytics** and reporting
5. **Automatic expiration extension** for active polls
6. **Admin email reports** of cleanup operations

## Security Considerations

- Only poll creators (via admin token) can delete polls
- Soft delete provides audit trail
- 30-day grace period prevents accidental data loss
- Admin dashboard requires authentication
- Cleanup command can be run manually or automatically
