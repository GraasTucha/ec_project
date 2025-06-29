# webapp/management/commands/update_fantasy.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from webapp.models import FantasyRankedPlayer, UpdateTimestamp
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
import requests
import time

class Command(BaseCommand):
    help = "Fetch and cache NBA fantasy player data using weighted stat system"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting update_fantasy command...")

        self.stdout.write("Clearing old data...")

        # Add retries and timeout when fetching active players
        all_players = []
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                self.stdout.write(f"Fetching all active NBA players... Attempt {attempt}")

                # Patch requests.Session.request to add timeout for nba_api calls
                original_request = requests.Session.request
                def timeout_request(self, method, url, **kwargs):
                    if 'timeout' not in kwargs:
                        kwargs['timeout'] = 10  # 10 seconds timeout
                    return original_request(self, method, url, **kwargs)
                requests.Session.request = timeout_request

                all_players = players.get_active_players()

                # Restore original method immediately after call
                requests.Session.request = original_request

                if all_players:
                    self.stdout.write(f"Fetched {len(all_players)} active players.")
                    break
            except requests.exceptions.RequestException as e:
                self.stdout.write(f"Request exception on attempt {attempt}: {e}")
                time.sleep(5)
            except Exception as e:
                self.stdout.write(f"Unexpected error on attempt {attempt}: {e}")
                time.sleep(5)
        else:
            self.stdout.write("Failed to fetch active players after retries.")
            self.stdout.write("Using fallback hardcoded player list for testing.")
            all_players = [{'id': 2544, 'full_name': 'LeBron James'}]  # Example fallback

        player_data = []

        for p in all_players:
            try:
                self.stdout.write(f"Processing player: {p['full_name']} (ID: {p['id']})")

                stats_df = playercareerstats.PlayerCareerStats(player_id=p['id']).get_data_frames()[0]
                season_stats = stats_df[stats_df['SEASON_ID'].str.contains('2024-25')]

                if not season_stats.empty:
                    row = season_stats.iloc[-1]
                    gp = row['GP']
                    if gp > 0:
                        # Per-game stats
                        ppg = row['PTS'] / gp
                        rpg = row['REB'] / gp
                        apg = row['AST'] / gp
                        bpg = row['BLK'] / gp
                        spg = row['STL'] / gp
                        fgm = row['FGM'] / gp
                        fga = row['FGA'] / gp
                        ftm = row['FTM'] / gp
                        fta = row['FTA'] / gp
                        tpm = row['FG3M'] / gp
                        tov = row['TOV'] / gp

                        score = (
                            ppg * 1 + tpm * 1 + fgm * 2 + fga * -1 + ftm * 1 + fta * -1 +
                            rpg * 1 + apg * 2 + spg * 4 + bpg * 4 + tov * -2
                        )

                        player_data.append({
                            'name': p['full_name'],
                            'ppg': round(ppg, 1),
                            'rpg': round(rpg, 1),
                            'apg': round(apg, 1),
                            'bpg': round(bpg, 1),
                            'spg': round(spg, 1),
                            'avg': round(score, 2),
                        })

            except Exception as e:
                self.stdout.write(f"Error for {p['full_name']}: {e}")

        player_data.sort(key=lambda x: x['avg'], reverse=True)

        self.stdout.write(f"Saving {len(player_data)} players to database...")
        for i, pdata in enumerate(player_data, 1):
            FantasyRankedPlayer.objects.update_or_create(
                name=pdata['name'],
                defaults={
                    'ppg': pdata['ppg'],
                    'rpg': pdata['rpg'],
                    'apg': pdata['apg'],
                    'bpg': pdata['bpg'],
                    'spg': pdata['spg'],
                    'avg': pdata['avg'],
                    'rank': i,
                    'removed': False,
                }
            )

            if i % 10 == 0:
                self.stdout.write(f"Saved {i} players...")

        UpdateTimestamp.objects.update_or_create(
            name="fantasy_data",
            defaults={"last_updated": timezone.now()}
        )

        self.stdout.write(self.style.SUCCESS("Fantasy players updated."))
        
