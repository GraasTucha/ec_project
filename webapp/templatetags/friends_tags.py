from django import template
from webapp.models import Friendship
from django.db.models import Q

register = template.Library()

@register.filter
def friends_count(user):
    if not user.is_authenticated:
        return 0
    friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
    return friendships.count()

@register.filter
def pending_friend_requests_count(user):
    if not user.is_authenticated:
        return 0
    return user.received_requests.filter(accepted=False, declined=False).count()

