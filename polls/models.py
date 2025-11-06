from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
import uuid
import random
import string

class ActivePollManager(models.Manager):
    """Manager that returns only active (non-deleted, non-expired) polls"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def active(self):
        """Return polls that are not deleted and not expired"""
        return self.get_queryset().filter(
            deleted_at__isnull=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )

class Poll(models.Model):
    question = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True, help_text="Optional description or context for your poll")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    admin_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_anonymous = models.BooleanField(default=True)
    public_results = models.BooleanField(default=False)
    allow_multiple_choices = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Expiration and lifecycle management
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Poll will be automatically deleted after this date. Leave blank for 90-day default."
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Soft deletion timestamp. Poll will be permanently deleted 30 days after this date."
    )

    # Managers
    objects = models.Manager()  # Default manager (includes deleted polls)
    active_objects = ActivePollManager()  # Only non-deleted polls

    # Track if expires_at was explicitly set
    _expires_at_set = False

    def __init__(self, *args, **kwargs):
        # Check if expires_at is in kwargs (explicitly set by user)
        if 'expires_at' in kwargs:
            self._expires_at_set = True
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.question)[:50]
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            self.slug = f"{base_slug}-{random_suffix}"

        # Set default expiration to 90 days from creation if not explicitly set
        if not self.pk and not self._expires_at_set and self.expires_at is None:
            self.expires_at = timezone.now() + timedelta(days=90)

        super().save(*args, **kwargs)

    def total_votes(self):
        return sum(choice.votes for choice in self.choices.all())

    @property
    def is_expired(self):
        """Check if the poll has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_soft_deleted(self):
        """Check if the poll is soft deleted"""
        return self.deleted_at is not None

    @property
    def days_until_expiration(self):
        """Return days until expiration, or None if already expired"""
        if not self.expires_at:
            return None
        delta = self.expires_at - timezone.now()
        return max(0, delta.days) if delta.days >= 0 else 0

    @property
    def days_until_permanent_deletion(self):
        """Return days until permanent deletion after soft delete"""
        if not self.deleted_at:
            return None
        permanent_deletion_date = self.deleted_at + timedelta(days=30)
        delta = permanent_deletion_date - timezone.now()
        return max(0, delta.days)

    def soft_delete(self):
        """Mark poll as soft deleted"""
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore a soft deleted poll"""
        self.deleted_at = None
        self.save()

    def __str__(self):
        return self.question

class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text

class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='vote_records')
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, related_name='vote_records')
    voter_name = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    cookie_token = models.CharField(max_length=64, blank=True, null=True, help_text="Browser cookie token to prevent duplicate votes")
    voted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vote for {self.choice.choice_text} in {self.poll.question}"
