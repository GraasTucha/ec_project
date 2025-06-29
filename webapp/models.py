from django.db import models
from django.contrib.auth.models import User

class FantasyRankedPlayer(models.Model):
    name = models.CharField(max_length=100)
    ppg = models.FloatField()
    rpg = models.FloatField()
    apg = models.FloatField()
    bpg = models.FloatField()
    spg = models.FloatField()
    avg = models.FloatField()
    rank = models.PositiveIntegerField(unique=True, null=True, blank=True)
    removed = models.BooleanField(default=False)

    injury_status = models.CharField(max_length=50, blank=True, default="Healthy")
    injury_duration = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return f"{self.rank}: {self.name}"

class DisplayedPlayer(models.Model):
    player = models.OneToOneField(FantasyRankedPlayer, on_delete=models.CASCADE)
    display_rank = models.PositiveIntegerField(unique=True)

class UpdateTimestamp(models.Model):
    name = models.CharField(max_length=100, unique=True)
    last_updated = models.DateTimeField()

# Fantasy team with many-to-many players
class FantasyTeam(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    players = models.ManyToManyField(FantasyRankedPlayer, blank=True)

    def can_add_player(self):
        return self.players.count() < 15

    def __str__(self):
        return f"{self.user.username}'s Fantasy Team"

# Friend system models
class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.username} ➝ {self.to_user.username}"
class Friendship(models.Model):
    user1 = models.ForeignKey(User, related_name='friendship_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='friendship_user2', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Friendship between {self.user1.username} and {self.user2.username}"

# NEW Notification model for friend requests (and future notifications)
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    verb = models.CharField(max_length=255)  # e.g. "sent you a friend request"
    unread = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} {self.verb} to {self.recipient}"

















