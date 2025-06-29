from webapp.models import FantasyRankedPlayer
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
import time

def fetch_and_update_fantasy_data(stdout=None):
    all_players = players.get_active_players()
    player_data = []

    for p in all_players:
        try:
            if stdout:
                stdout.write(f"Processing player: {p['full_name']} (ID: {p['id']})")
            time.sleep(0.5)

            stats_df = playercareerstats.PlayerCareerStats(player_id=p['id']).get_data_frames()[0]
            season_stats = stats_df[stats_df['SEASON_ID'].str.contains('2023')]

            if not season_stats.empty:
                row = season_stats.iloc[-1]
                gp = row['GP']
                if gp > 0:
                    ppg = row['PTS'] / gp
                    rpg = row['REB'] / gp
                    apg = row['AST'] / gp
                    bpg = row['BLK'] / gp
                    spg = row['STL'] / gp
                    avg = (ppg + rpg + apg + bpg + spg) / 5
                    player_data.append({
                        'player_id': p['id'],
                        'name': p['full_name'],
                        'ppg': round(ppg, 1),
                        'rpg': round(rpg, 1),
                        'apg': round(apg, 1),
                        'bpg': round(bpg, 1),
                        'spg': round(spg, 1),
                        'avg': round(avg, 2),
                    })
        except Exception as e:
            if stdout:
                stdout.write(f"Error for {p['full_name']}: {e}")

    player_data.sort(key=lambda x: x['avg'], reverse=True)
    for i, pdata in enumerate(player_data[:30], 1):
        FantasyRankedPlayer.objects.update_or_create(
            player_id=pdata['player_id'],
            defaults={
                'name': pdata['name'],
                'ppg': pdata['ppg'],
                'rpg': pdata['rpg'],
                'apg': pdata['apg'],
                'bpg': pdata['bpg'],
                'spg': pdata['spg'],
                'avg': pdata['avg'],
                'rank': i,
            }
        )
        if stdout:
            stdout.write(f"Saved {pdata['name']} with rank {i}")


