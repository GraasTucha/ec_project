from django.contrib import admin
from .models import (
    FantasyRankedPlayer,
    DisplayedPlayer,
    UpdateTimestamp,
    FantasyTeam,
    FriendRequest,
    Friendship,
    Notification
)

@admin.register(FantasyRankedPlayer)
class FantasyRankedPlayerAdmin(admin.ModelAdmin):
    list_display = (
        'rank', 'name', 'ppg', 'rpg', 'apg', 'bpg', 'spg',
        'avg', 'removed', 'injury_status', 'injury_duration'
    )
    search_fields = ('name',)
    list_filter = ('removed', 'injury_status')

@admin.register(DisplayedPlayer)
class DisplayedPlayerAdmin(admin.ModelAdmin):
    list_display = ('player', 'display_rank')

@admin.register(UpdateTimestamp)
class UpdateTimestampAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_updated')

@admin.register(FantasyTeam)
class FantasyTeamAdmin(admin.ModelAdmin):
    list_display = ('user',)

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'accepted', 'declined', 'timestamp')
    list_filter = ('accepted', 'declined')

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'verb', 'unread', 'timestamp')
    list_filter = ('unread',)



