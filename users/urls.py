# users/urls.py

from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    # Dashboard / home
    path("", views.user_dashboard, name="user"),

    # Authentication
    path("login/",    views.login_view,  name="login"),
    path("logout/",   views.logout_view, name="logout"),
    path("register/", views.register,    name="register"),

    # 1) Your own profile (no args)
    path("profile/", views.profile_view, name="profile_self"),

    # 2) Any user's profile by their ID
    path("profile/<int:user_id>/", views.profile_view, name="profile"),

    # 3) Your friends list
    path("profile/friends/", views.profile_friends_list, name="profile_friends_list"),

    # AJAX endpoints for fantasy team
    path("profile/search-players/",     views.search_players,            name="search_players"),
    path("profile/add-player/",         views.add_player_to_team,        name="add_player_to_team"),
    path("profile/remove-player/",      views.remove_player_from_team,   name="remove_player_from_team"),
]














