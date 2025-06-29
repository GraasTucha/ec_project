from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import FriendRequest
from django.contrib.auth.decorators import login_required
from webapp.models import Friendship
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .models import FantasyRankedPlayer, FantasyTeam, FriendRequest, Friendship, Notification
from nba_api.stats.endpoints import (
    leaguestandings, leaguegamefinder, commonteamroster, playercareerstats
)
from nba_api.stats.static import players, teams
import datetime


# Utility function to get current NBA season string like "2024-25"
def get_display_season():
    today = datetime.date.today()
    year = today.year
    month = today.month
    day = today.day

    cutoff_month = 10
    cutoff_day = 15

    if (month < cutoff_month) or (month == cutoff_month and day < cutoff_day):
        start_year = year - 1
    else:
        start_year = year

    end_year_short = str(start_year + 1)[-2:]
    season_str = f"{start_year}-{end_year_short}"
    return season_str


# View for home page
def home(request):
    return render(request, 'webapp/home.html')


# View for NBA data
def nba_data(request):
    view = request.GET.get('view')
    team_id = request.GET.get('team_id')
    player_id = request.GET.get('player_id')

    current_season = get_display_season()
    context = {'view': view}

    all_teams = sorted(teams.get_teams(), key=lambda x: x['full_name'])
    context['teams'] = all_teams

    if view == 'standings':
        filter_by = request.GET.get('conference', 'all')
        standings_df = leaguestandings.LeagueStandings().get_data_frames()[0]

        if filter_by == 'east':
            standings_df = standings_df[standings_df['Conference'] == 'East']
        elif filter_by == 'west':
            standings_df = standings_df[standings_df['Conference'] == 'West']

        standings_df = standings_df.sort_values(by='WinPCT', ascending=False).reset_index(drop=True)
        standings_df['Rank'] = standings_df.index + 1

        context['standings'] = standings_df[['Rank', 'TeamCity', 'TeamName', 'Conference', 'WINS', 'LOSSES', 'WinPCT']].to_dict(orient='records')
        context['selected_conference'] = filter_by

    elif view == 'game_results':
        if not team_id:
            lakers = next((t for t in all_teams if t['full_name'] == 'Los Angeles Lakers'), None)
            team_id = lakers['id'] if lakers else None
        else:
            team_id = int(team_id)

        if team_id:
            games = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id).get_data_frames()[0]

            start_year = current_season[:4]
            api_season_id = f"2{start_year}"

            filtered_games = games[games['SEASON_ID'] == api_season_id]

            if filtered_games.empty:
                last_season = games['SEASON_ID'].max()
                filtered_games = games[games['SEASON_ID'] == last_season]

            results = filtered_games[['GAME_DATE', 'MATCHUP', 'WL', 'PTS', 'PLUS_MINUS']]
            context['game_results'] = results.to_dict(orient='records')
            context['selected_team_id'] = str(team_id)

    elif view == 'player_stats':
        if team_id:
            team_id = int(team_id)
            roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            team_players = roster[['PLAYER', 'PLAYER_ID']]
            context['players'] = team_players.to_dict(orient='records')
            context['selected_team_id'] = team_id

            if player_id:
                player_id = int(player_id)
                stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_data_frames()[0]

                filtered = stats[stats['SEASON_ID'] == current_season]

                if filtered.empty:
                    last_season = stats['SEASON_ID'].max()
                    filtered = stats[stats['SEASON_ID'] == last_season]

                context['player_stats'] = filtered.to_dict(orient='records')
                context['selected_player_id'] = player_id

    return render(request, 'webapp/nba.html', context)


# View for fantasy draft
def fantasy_draft(request):
    query = request.GET.get('q', '').strip()
    if query:
        ranked_players = FantasyRankedPlayer.objects.filter(
            removed=False,
            name__icontains=query
        ).order_by('rank')
    else:
        ranked_players = FantasyRankedPlayer.objects.filter(
            removed=False
        ).order_by('rank')[:30]

    return render(request, 'webapp/fantasy_draft.html', {
        'ranked_players': ranked_players,
        'search_query': query
    })


# View for removing players
def remove_player(request, player_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                removed_player = FantasyRankedPlayer.objects.get(id=player_id)
                removed_rank = removed_player.rank
                removed_player.removed = True
                removed_player.rank = None
                removed_player.save(update_fields=['removed', 'rank'])

                players_to_update = list(FantasyRankedPlayer.objects.filter(rank__gt=removed_rank).order_by('rank'))
                for p in players_to_update:
                    p.rank -= 1
                FantasyRankedPlayer.objects.bulk_update(players_to_update, ['rank'])
        except FantasyRankedPlayer.DoesNotExist:
            pass
    return redirect('webapp:fantasy_draft')


# View for resetting rankings
def reset_rankings(request):
    if request.method == 'POST':
        with transaction.atomic():
            FantasyRankedPlayer.objects.update(removed=False)
            all_players = list(FantasyRankedPlayer.objects.filter(removed=False).order_by('-avg'))
            FantasyRankedPlayer.objects.all().update(rank=None)

            for i, player in enumerate(all_players, 1):
                player.rank = i
            FantasyRankedPlayer.objects.bulk_update(all_players, ['rank'])

        return redirect('webapp:fantasy_draft')


# View for editing injuries
def edit_injuries(request):
    query = request.GET.get('q', '').strip()

    if query:
        players = FantasyRankedPlayer.objects.filter(
            removed=False,
            name__icontains=query
        ).order_by('rank')
    else:
        players = FantasyRankedPlayer.objects.filter(
            removed=False
        ).order_by('rank')

    if request.method == 'POST':
        for player in players:
            status = request.POST.get(f"status_{player.id}", "Healthy")
            duration = request.POST.get(f"duration_{player.id}", "")
            player.injury_status = status
            player.injury_duration = duration
        FantasyRankedPlayer.objects.bulk_update(players, ['injury_status', 'injury_duration'])

        redirect_url = request.path
        if query:
            redirect_url += f"?q={query}"
        return redirect(redirect_url)

    return render(request, 'webapp/edit_injuries.html', {
        'players': players,
        'search_query': query,
    })


# === Fantasy Team AJAX handlers for profile page ===

@login_required
def search_players_ajax(request):
    q = request.GET.get('q', '').strip()
    players_list = []
    if q:
        matched = FantasyRankedPlayer.objects.filter(name__icontains=q, removed=False)[:10]
        for p in matched:
            players_list.append({
                'id': p.id,
                'name': p.name,
                'ppg': p.ppg,
                'rpg': p.rpg,
                'apg': p.apg,
                'bpg': p.bpg,
                'spg': p.spg,
            })
    return JsonResponse({'players': players_list})


@require_POST
@login_required
def add_player_ajax(request):
    player_id = request.POST.get('player_id')
    if not player_id:
        return JsonResponse({'error': 'No player id provided'}, status=400)
    try:
        player = FantasyRankedPlayer.objects.get(id=player_id, removed=False)
    except FantasyRankedPlayer.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)

    team, created = FantasyTeam.objects.get_or_create(user=request.user)
    if team.players.count() >= 15:
        return JsonResponse({'error': 'Team is full (max 15 players).'}, status=400)

    if team.players.filter(id=player.id).exists():
        return JsonResponse({'error': 'Player already in your team.'}, status=400)

    team.players.add(player)
    return JsonResponse({
        'success': True,
        'player': {
            'id': player.id,
            'name': player.name,
            'ppg': player.ppg,
            'rpg': player.rpg,
            'apg': player.apg,
            'bpg': player.bpg,
            'spg': player.spg,
        }
    })


@require_POST
@login_required
def remove_player_ajax(request):
    player_id = request.POST.get('player_id')
    if not player_id:
        return JsonResponse({'error': 'No player id provided'}, status=400)

    try:
        player = FantasyRankedPlayer.objects.get(id=player_id)
    except FantasyRankedPlayer.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)

    team = FantasyTeam.objects.filter(user=request.user).first()
    if not team:
        return JsonResponse({'error': 'You have no fantasy team.'}, status=400)

    team.players.remove(player)
    return JsonResponse({'success': True})


# === Friend system views ===

@login_required
def search_users(request):
    q = request.GET.get('q', '').strip()  # Get the search query
    users_list = []  # Prepare an empty list to store the search results
    if q:
        # Search users, excluding the logged-in user
        matched = User.objects.filter(username__icontains=q).exclude(id=request.user.id)[:10]
        for u in matched:
            users_list.append({
                'id': u.id,
                'username': u.username,
            })
    return JsonResponse({'users': users_list})


@login_required
@require_POST
def send_friend_request(request, user_id):
    if user_id == request.user.id:
        return JsonResponse({'error': "You cannot friend yourself."}, status=400)

    to_user = get_object_or_404(User, id=user_id)

    # Check if the friend request already exists
    if FriendRequest.objects.filter(from_user=request.user, to_user=to_user, accepted=False, declined=False).exists():
        return JsonResponse({'error': 'Friend request already sent.'}, status=400)

    # Check if they are already friends
    if Friendship.objects.filter(Q(user1=request.user, user2=to_user) | Q(user1=to_user, user2=request.user)).exists():
        return JsonResponse({'error': 'You are already friends.'}, status=400)

    # Create the friend request
    friend_request = FriendRequest.objects.create(from_user=request.user, to_user=to_user)

    # Create a notification for the other user
    Notification.objects.create(
        recipient=to_user,
        sender=request.user,
        verb="sent you a friend request",
        unread=True  # Mark notification as unread
    )

    return JsonResponse({'success': True})





@login_required
def notifications(request):
    # Fetch unread notifications for the logged-in user
    pending_requests = Notification.objects.filter(
        recipient=request.user, unread=True
    ).order_by('-timestamp')  # Sort by the most recent first

    return render(request, 'webapp/notifications.html', {
        'pending_requests': pending_requests
    })


@login_required
@require_POST
def respond_to_request(request, request_id, action):
    fr = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)

    if action == 'accept':
        fr.accepted = True
        fr.declined = False
        fr.save()

        # Create the friendship in both directions
        Friendship.objects.create(user1=fr.from_user, user2=fr.to_user)
        Friendship.objects.create(user1=fr.to_user, user2=fr.from_user)

        # Mark the notification as read
        Notification.objects.filter(
            recipient=request.user,
            sender=fr.from_user,
            verb="sent you a friend request",
            unread=True
        ).update(unread=False)

        return JsonResponse({'success': True})

    elif action == 'decline':
        fr.accepted = False
        fr.declined = True
        fr.save()

        # Mark the notification as read
        Notification.objects.filter(
            recipient=request.user,
            sender=fr.from_user,
            verb="sent you a friend request",
            unread=True
        ).update(unread=False)

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid action'}, status=400)




@login_required
def add_friends(request):
    """
    Display the Add Friends page.
    You can expand this with friend search functionality or lists.
    """
    return render(request, 'webapp/add_friends.html')

@login_required
@require_POST
def mark_notification_as_read(request, notification_id):
    # Get the notification
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)

    # Mark as read
    notification.unread = False
    notification.save()

    return JsonResponse({'success': True})

@login_required
def notifications_requests(request):
    """
    Return all *pending* friend requests (FriendRequest objects)
    as JSON, each carrying its own accept + decline endpoint.
    """
    pending = FriendRequest.objects.filter(
        to_user=request.user,
        accepted=False,
        declined=False
    ).order_by('-timestamp')

    data = []
    for fr in pending:
        data.append({
            'id':          fr.id,
            'sender':      fr.from_user.username,
            'verb':        "sent you a friend request",
            'timestamp':   fr.timestamp.isoformat(),
            'accept_url':  reverse('webapp:respond_to_request', args=[fr.id, 'accept']),
            'decline_url': reverse('webapp:respond_to_request', args=[fr.id, 'decline']),
        })

    return JsonResponse({'requests': data})

@login_required
def profile_friends_list(request):
    """
    Show all users that `request.user` is friends with.
    We store friendships in both directions, so just look for
    Friendship.user1 == request.user and list user2.
    """
    # fetch all friendships where user1 is the current user
    qs = Friendship.objects.filter(user1=request.user).select_related('user2')
    friends = [f.user2 for f in qs]

    return render(request, 'users/friends_list.html', {
        'profile_user': request.user,
        'friends':      friends,
    })








































