from django.urls import path
from . import views

app_name = 'webapp'

urlpatterns = [
    path('', views.home, name='home'),

    # NBA data views
    path('nba/', views.nba_data, name='nba_data'),

    # Fantasy draft related
    path('fantasy-draft/', views.fantasy_draft, name='fantasy_draft'),
    path('fantasy-draft/remove/<int:player_id>/', views.remove_player, name='remove_player'),
    path('fantasy-draft/reset/', views.reset_rankings, name='reset_rankings'),

    # Edit injuries page
    path('edit-injuries/', views.edit_injuries, name='edit_injuries'),

    # AJAX endpoints for fantasy team management
    path('profile/search-players/', views.search_players_ajax, name='search_players_ajax'),
    path('profile/add-player/', views.add_player_ajax, name='add_player_ajax'),
    path('profile/remove-player/', views.remove_player_ajax, name='remove_player_ajax'),

    # Friend system views
    path('search-users/', views.search_users, name='search_users'),
    path('send-friend-request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),

    # Notifications views
    path('notifications/', views.notifications, name='notifications'),
    path(
        'notifications/respond/<int:request_id>/<str:action>/',
        views.respond_to_request,
        name='respond_to_request'
    ),
    path(
        'notifications/requests/',
        views.notifications_requests,
        name='notifications_requests'
    ),

    # Add friends page
    path('add-friends/', views.add_friends, name='add_friends'),
]



















