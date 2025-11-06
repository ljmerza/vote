from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Poll, Choice, Vote
import secrets

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def has_already_voted(request, poll):
    """Check if user has already voted using cookie or IP address"""
    # Check cookie first (more reliable for individual users)
    vote_cookie = request.COOKIES.get(f'poll_voted_{poll.id}')
    if vote_cookie:
        if Vote.objects.filter(poll=poll, cookie_token=vote_cookie).exists():
            return True

    # Fallback to IP check (catches cases where cookie was cleared)
    ip_address = get_client_ip(request)
    if Vote.objects.filter(poll=poll, ip_address=ip_address).exists():
        return True

    return False

def create_poll(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        description = request.POST.get('description', '').strip()
        choices_list = request.POST.getlist('choices[]')
        allow_multiple = request.POST.get('allow_multiple_choices') == 'on'
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        public_results = request.POST.get('public_results') == 'on'
        expiration_days = request.POST.get('expiration_days', '90')

        choices_list = [c.strip() for c in choices_list if c.strip()]

        if len(choices_list) < 2:
            messages.error(request, 'Please provide at least 2 choices.')
            return redirect('create_poll')

        # Calculate expiration date
        expires_at = None
        if expiration_days != 'never':
            try:
                days = int(expiration_days)
                expires_at = timezone.now() + timedelta(days=days)
            except ValueError:
                expires_at = timezone.now() + timedelta(days=90)  # Default to 90 days

        poll = Poll.objects.create(
            question=question,
            description=description if description else None,
            allow_multiple_choices=allow_multiple,
            is_anonymous=is_anonymous,
            public_results=public_results,
            expires_at=expires_at
        )
        
        for choice_text in choices_list:
            Choice.objects.create(poll=poll, choice_text=choice_text)
        
        voting_url = request.build_absolute_uri(reverse('vote_page', args=[poll.slug]))
        admin_url = request.build_absolute_uri(reverse('admin_results', args=[poll.admin_token]))
        
        return render(request, 'polls/poll_created.html', {
            'poll': poll,
            'voting_url': voting_url,
            'admin_url': admin_url
        })
    
    return render(request, 'polls/create_poll.html')

def vote_page(request, slug):
    poll = get_object_or_404(Poll.active_objects, slug=slug)

    # Check if poll is expired
    if poll.is_expired:
        messages.error(request, 'This poll has expired and is no longer accepting votes.')
        return redirect('create_poll')

    if has_already_voted(request, poll):
        return render(request, 'polls/already_voted.html', {'poll': poll})

    return render(request, 'polls/vote.html', {'poll': poll})

def vote(request, slug):
    if request.method != 'POST':
        return redirect('vote_page', slug=slug)

    poll = get_object_or_404(Poll.active_objects, slug=slug)

    # Check if poll is expired
    if poll.is_expired:
        messages.error(request, 'This poll has expired and is no longer accepting votes.')
        return redirect('create_poll')

    if has_already_voted(request, poll):
        return render(request, 'polls/already_voted.html', {'poll': poll})

    ip_address = get_client_ip(request)
    voter_name = request.POST.get('voter_name', '').strip() if not poll.is_anonymous else None

    if poll.allow_multiple_choices:
        choice_ids = request.POST.getlist('choices')
    else:
        choice_ids = [request.POST.get('choices')]

    if not choice_ids or not any(choice_ids):
        messages.error(request, 'Please select at least one choice.')
        return redirect('vote_page', slug=slug)

    # Generate a unique cookie token for this vote
    cookie_token = secrets.token_urlsafe(32)

    for choice_id in choice_ids:
        try:
            choice = Choice.objects.get(id=choice_id, poll=poll)
            choice.votes += 1
            choice.save()

            Vote.objects.create(
                poll=poll,
                choice=choice,
                voter_name=voter_name,
                ip_address=ip_address,
                cookie_token=cookie_token
            )
        except Choice.DoesNotExist:
            pass

    # Create response and set cookie
    response = render(request, 'polls/thank_you.html', {'poll': poll})
    # Cookie expires in 10 years (effectively permanent for a poll)
    response.set_cookie(
        f'poll_voted_{poll.id}',
        cookie_token,
        max_age=315360000,  # 10 years in seconds
        httponly=True,
        samesite='Lax'
    )
    return response

def public_results(request, slug):
    poll = get_object_or_404(Poll.active_objects, slug=slug)

    if not poll.public_results:
        messages.error(request, 'Results for this poll are private.')
        return redirect('vote_page', slug=slug)

    return render_results(request, poll, is_admin=False)

def admin_results(request, admin_token):
    poll = get_object_or_404(Poll, admin_token=admin_token)
    return render_results(request, poll, is_admin=True)

def render_results(request, poll, is_admin=False):
    choices = poll.choices.all()
    total_votes = sum(choice.votes for choice in choices)
    
    results = []
    for choice in choices:
        percentage = round((choice.votes / total_votes * 100) if total_votes > 0 else 0, 1)
        results.append({
            'choice_text': choice.choice_text,
            'votes': choice.votes,
            'percentage': percentage
        })
    
    voters = None
    if is_admin and not poll.is_anonymous:
        voters = Vote.objects.filter(poll=poll).select_related('choice').order_by('-voted_at')
    
    return render(request, 'polls/results.html', {
        'poll': poll,
        'results': results,
        'total_votes': total_votes,
        'is_admin': is_admin,
        'voters': voters
    })

def edit_poll(request, admin_token):
    poll = get_object_or_404(Poll, admin_token=admin_token)
    
    # Only allow editing if no votes yet
    if poll.total_votes() > 0:
        messages.error(request, 'Cannot edit poll after votes have been cast.')
        return redirect('admin_results', admin_token=admin_token)
    
    if request.method == 'POST':
        poll.question = request.POST.get('question')
        poll.description = request.POST.get('description', '').strip() or None
        poll.allow_multiple_choices = request.POST.get('allow_multiple_choices') == 'on'
        poll.is_anonymous = request.POST.get('is_anonymous') == 'on'
        poll.public_results = request.POST.get('public_results') == 'on'
        poll.save()
        
        # Update choices
        existing_choice_ids = []
        choices_data = zip(
            request.POST.getlist('choice_ids[]'),
            request.POST.getlist('choices[]')
        )
        
        for choice_id, choice_text in choices_data:
            choice_text = choice_text.strip()
            if not choice_text:
                continue
                
            if choice_id and choice_id.isdigit():
                # Update existing choice
                try:
                    choice = Choice.objects.get(id=int(choice_id), poll=poll)
                    choice.choice_text = choice_text
                    choice.save()
                    existing_choice_ids.append(int(choice_id))
                except Choice.DoesNotExist:
                    pass
            else:
                # Create new choice
                new_choice = Choice.objects.create(poll=poll, choice_text=choice_text)
                existing_choice_ids.append(new_choice.id)
        
        # Delete removed choices
        poll.choices.exclude(id__in=existing_choice_ids).delete()
        
        messages.success(request, 'Poll updated successfully!')
        return redirect('admin_results', admin_token=admin_token)
    
    return render(request, 'polls/edit_poll.html', {'poll': poll})

def delete_poll(request, admin_token):
    poll = get_object_or_404(Poll, admin_token=admin_token)

    if request.method == 'POST':
        action = request.POST.get('action', 'soft_delete')

        if action == 'restore' and poll.is_soft_deleted:
            poll.restore()
            messages.success(request, f'Poll "{poll.question}" has been restored.')
            return redirect('admin_results', admin_token=admin_token)
        elif action == 'hard_delete':
            poll_question = poll.question
            poll.delete()
            messages.success(request, f'Poll "{poll_question}" has been permanently deleted.')
            return redirect('create_poll')
        else:  # soft_delete
            poll_question = poll.question
            poll.soft_delete()
            messages.success(request, f'Poll "{poll_question}" has been deleted. It will be permanently removed in 30 days.')
            return redirect('create_poll')

    return render(request, 'polls/delete_poll.html', {'poll': poll})

