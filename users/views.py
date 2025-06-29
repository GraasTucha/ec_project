# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q

from webapp.models import FantasyTeam, FantasyRankedPlayer, Friendship
from .forms import UserRegistrationForm

@login_required(login_url='users:login')
def user_dashboard(request):
    return render(request, "users/user.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', reverse("webapp:home"))
            return HttpResponseRedirect(next_url)
        messages.error(request, "Invalid Credentials.")
    return render(request, "users/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('users:login')


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created! You can now log in.")
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile_view(request, user_id=None):
    # if user_id provided, show that profile, else your own
    profile_user = get_object_or_404(User, id=user_id) if user_id else request.user

    # fetch their fantasy team
    team_obj = FantasyTeam.objects.filter(user=profile_user).first()
    team = team_obj.players.all() if team_obj else []

    # are we viewing our own?
    is_self = (profile_user == request.user)

    return render(request, "users/profile.html", {
        "profile_user": profile_user,
        "username":     profile_user.username,   # so {{ username }} in template works
        "team":         team,
        "is_self":      is_self,
    })


@login_required
def search_players(request):
    q = request.GET.get('q', '').strip()
    players = FantasyRankedPlayer.objects.filter(name__icontains=q, removed=False)[:10] if q else []
    results = [{
        'id': p.id, 'name': p.name, 'rank': getattr(p, 'rank','N/A'),
        'ppg': p.ppg,'rpg': p.rpg,'apg': p.apg,'bpg': p.bpg,'spg': p.spg,
        'injury_status': p.injury_status,
    } for p in players]
    return JsonResponse({'players': results})


@login_required
def add_player_to_team(request):
    if request.method == 'POST':
        pid = request.POST.get('player_id')
        if not pid:
            return JsonResponse({'success': False, 'error': 'No player_id provided.'})
        try:
            p = FantasyRankedPlayer.objects.get(id=pid, removed=False)
        except FantasyRankedPlayer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Player not found.'})
        team, _ = FantasyTeam.objects.get_or_create(user=request.user)
        if team.players.count() >= 15:
            return JsonResponse({'success': False, 'error': 'Team is full.'})
        if p in team.players.all():
            return JsonResponse({'success': False, 'error': 'Already in your team.'})
        team.players.add(p)
        return JsonResponse({'success': True, 'player': {
            'id': p.id, 'name': p.name, 'ppg': p.ppg, 'rpg': p.rpg,
            'apg': p.apg, 'bpg': p.bpg, 'spg': p.spg,
            'injury_status': p.injury_status,
        }})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def remove_player_from_team(request):
    if request.method == 'POST':
        pid = request.POST.get('player_id')
        if not pid:
            return JsonResponse({'success': False, 'error': 'No player_id provided.'})
        try:
            p = FantasyRankedPlayer.objects.get(id=pid)
        except FantasyRankedPlayer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Player not found.'})
        team, _ = FantasyTeam.objects.get_or_create(user=request.user)
        if p not in team.players.all():
            return JsonResponse({'success': False, 'error': 'Not in your team.'})
        team.players.remove(p)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def profile_friends_list(request):
    # all friendships where I'm user1 or user2
    qs = Friendship.objects.filter(Q(user1=request.user) | Q(user2=request.user))\
                           .select_related('user1','user2')
    friends = []
    for fr in qs:
        other = fr.user2 if fr.user1 == request.user else fr.user1
        friends.append(other)
    # drop duplicates
    unique = {u.id: u for u in friends}.values()

    return render(request, 'users/friends_list.html', {
        'profile_user': request.user,
        'friends':      list(unique),
    })












