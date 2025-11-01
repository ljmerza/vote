from django.db import models
from django.utils.text import slugify
import uuid
import random
import string

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

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.question)[:50]
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            self.slug = f"{base_slug}-{random_suffix}"
        super().save(*args, **kwargs)

    def total_votes(self):
        return sum(choice.votes for choice in self.choices.all())

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
    voted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vote for {self.choice.choice_text} in {self.poll.question}"
