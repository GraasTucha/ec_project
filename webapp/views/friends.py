from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from webapp.models import FriendRequest, Friendship
from django.db.models import Q

@login_required
def search_users(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        users = User.objects.filter(username__icontains=q).exclude(id=request.user.id)[:10]
        for user in users:
            results.append({'id': user.id, 'username': user.username})
    return JsonResponse({'users': results})

@login_required
def send_friend_request(request, user_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    to_user = get_object_or_404(User, id=user_id)
    if to_user == request.user:
        return JsonResponse({'error': "You can't send a friend request to yourself."})
    # Check existing friendship
    if Friendship.objects.filter(Q(user1=request.user, user2=to_user) | Q(user1=to_user, user2=request.user)).exists():
        return JsonResponse({'error': "You are already friends."})
    # Check existing request
    existing_request = FriendRequest.objects.filter(from_user=request.user, to_user=to_user, accepted=False, declined=False).first()
    if existing_request:
        return JsonResponse({'error': "Friend request already sent."})
    FriendRequest.objects.create(from_user=request.user, to_user=to_user)
    return JsonResponse({'success': f"Friend request sent to {to_user.username}."})

@login_required
def notifications(request):
    requests = FriendRequest.objects.filter(to_user=request.user, accepted=False, declined=False)
    return render(request, 'webapp/notifications.html', {'friend_requests': requests})

@login_required
def respond_friend_request(request, request_id, action):
    fr = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    if request.method == 'POST':
        if action == 'accept':
            fr.accepted = True
            fr.save()
            # Create Friendship both ways
            Friendship.objects.create(user1=fr.from_user, user2=fr.to_user)
            # Optionally, create reverse for easier querying (or query with Q instead)
            # Friendship.objects.create(user1=fr.to_user, user2=fr.from_user)
        elif action == 'decline':
            fr.declined = True
            fr.save()
        else:
            return HttpResponseForbidden()
        return redirect('webapp:notifications')
    return HttpResponseForbidden()

@login_required
def profile_friends_list(request, user_id):
    user = get_object_or_404(User, id=user_id)
    friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
    friends = []
    for f in friendships:
        friends.append(f.user2 if f.user1 == user else f.user1)
    return render(request, 'webapp/friends_list.html', {'friends': friends, 'profile_user': user})

@login_required
def chat_page(request, room_name=None):
    # Basic chat page - extend with frontend later
    return render(request, 'webapp/chat.html', {'room_name': room_name or 'general'})

