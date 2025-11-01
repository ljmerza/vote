from django.contrib import admin
from .models import Poll, Choice, Vote

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2

class PollAdmin(admin.ModelAdmin):
    list_display = ['question', 'created_at', 'total_votes_display', 'is_anonymous', 'public_results', 'allow_multiple_choices']
    list_filter = ['created_at', 'is_anonymous', 'public_results', 'allow_multiple_choices']
    search_fields = ['question']
    readonly_fields = ['slug', 'admin_token', 'created_at', 'get_admin_url', 'get_voting_url']
    inlines = [ChoiceInline]
    
    def total_votes_display(self, obj):
        return obj.total_votes()
    total_votes_display.short_description = 'Total Votes'
    
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

