from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Poll, Choice, Vote

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2

class PollAdmin(admin.ModelAdmin):
    list_display = [
        'question', 'created_at', 'total_votes_display',
        'lifecycle_status', 'days_until_expiration_display',
        'is_anonymous', 'public_results', 'allow_multiple_choices'
    ]
    list_filter = ['created_at', 'is_anonymous', 'public_results', 'allow_multiple_choices', 'deleted_at']
    search_fields = ['question']
    readonly_fields = [
        'slug', 'admin_token', 'created_at', 'updated_at',
        'get_admin_url', 'get_voting_url', 'lifecycle_info'
    ]
    inlines = [ChoiceInline]
    actions = ['soft_delete_polls', 'restore_polls', 'extend_expiration']

    def total_votes_display(self, obj):
        return obj.total_votes()
    total_votes_display.short_description = 'Total Votes'

    def lifecycle_status(self, obj):
        if obj.is_soft_deleted:
            days_left = obj.days_until_permanent_deletion
            return format_html(
                '<span style="color: red;">🗑️ Deleted ({} days until permanent)</span>',
                days_left
            )
        elif obj.is_expired:
            return format_html('<span style="color: orange;">⏰ Expired</span>')
        else:
            return format_html('<span style="color: green;">✓ Active</span>')
    lifecycle_status.short_description = 'Status'

    def days_until_expiration_display(self, obj):
        if obj.is_soft_deleted:
            return '-'
        if not obj.expires_at:
            return 'Never'
        days = obj.days_until_expiration
        if days == 0 and obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        else:
            return f'{days} days'
    days_until_expiration_display.short_description = 'Expires In'

    def lifecycle_info(self, obj):
        info = []
        info.append(f'<strong>Created:</strong> {obj.created_at.strftime("%Y-%m-%d %H:%M")}')

        if obj.expires_at:
            info.append(f'<strong>Expires:</strong> {obj.expires_at.strftime("%Y-%m-%d %H:%M")}')
            if not obj.is_expired:
                info.append(f'<strong>Days until expiration:</strong> {obj.days_until_expiration}')

        if obj.deleted_at:
            info.append(f'<strong>Soft deleted:</strong> {obj.deleted_at.strftime("%Y-%m-%d %H:%M")}')
            info.append(f'<strong>Days until permanent deletion:</strong> {obj.days_until_permanent_deletion}')

        info.append(f'<strong>Total votes:</strong> {obj.total_votes()}')

        return format_html('<br>'.join(info))
    lifecycle_info.short_description = 'Lifecycle Information'

    def soft_delete_polls(self, request, queryset):
        count = 0
        for poll in queryset:
            if not poll.is_soft_deleted:
                poll.soft_delete()
                count += 1
        self.message_user(request, f'{count} poll(s) soft deleted.')
    soft_delete_polls.short_description = 'Soft delete selected polls'

    def restore_polls(self, request, queryset):
        count = 0
        for poll in queryset:
            if poll.is_soft_deleted:
                poll.restore()
                count += 1
        self.message_user(request, f'{count} poll(s) restored.')
    restore_polls.short_description = 'Restore soft-deleted polls'

    def extend_expiration(self, request, queryset):
        from datetime import timedelta
        count = 0
        for poll in queryset:
            if poll.expires_at:
                poll.expires_at = timezone.now() + timedelta(days=90)
                poll.save()
                count += 1
        self.message_user(request, f'Extended expiration for {count} poll(s) by 90 days.')
    extend_expiration.short_description = 'Extend expiration by 90 days'
    
    def get_admin_url(self, obj):
        if obj.pk:
            from django.urls import reverse
            url = reverse('admin_results', args=[obj.admin_token])
            return f"http://YOUR_DOMAIN:6243{url}"
        return "-"
    get_admin_url.short_description = 'Admin URL'
    
    def get_voting_url(self, obj):
        if obj.pk:
            from django.urls import reverse
            url = reverse('vote_page', args=[obj.slug])
            return f"http://YOUR_DOMAIN:6243{url}"
        return "-"
    get_voting_url.short_description = 'Voting URL'

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['choice_text', 'poll', 'votes']
    list_filter = ['poll']
    search_fields = ['choice_text', 'poll__question']

class VoteAdmin(admin.ModelAdmin):
    list_display = ['poll', 'choice', 'voter_name', 'ip_address', 'voted_at']
    list_filter = ['voted_at', 'poll']
    search_fields = ['voter_name', 'ip_address']

admin.site.register(Poll, PollAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Vote, VoteAdmin)

