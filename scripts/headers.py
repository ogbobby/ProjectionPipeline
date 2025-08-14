# Column headers for different position data imports
# Used by nflpyStats.py to specify which columns to import

QBHeader = [
    'player_id', 'player_display_name', 'position', 'recent_team', 'season', 'week',
    'completions', 'attempts', 'passing_yards', 'passing_tds', 'interceptions',
    'sacks', 'sack_yards', 'passing_air_yards', 'passing_yards_after_catch',
    'passing_first_downs', 'passing_epa', 'passing_2pt_conversions',
    'carries', 'rushing_yards', 'rushing_tds', 'rushing_first_downs',
    'rushing_epa', 'rushing_2pt_conversions', 'fantasy_points', 'fantasy_points_ppr'
]

RBHeader = [
    'player_id', 'player_display_name', 'position', 'recent_team', 'season', 'week',
    'carries', 'rushing_yards', 'rushing_tds', 'rushing_first_downs',
    'rushing_epa', 'rushing_2pt_conversions',
    'targets', 'receptions', 'receiving_yards', 'receiving_tds',
    'receiving_air_yards', 'receiving_yards_after_catch', 'receiving_first_downs',
    'receiving_epa', 'receiving_2pt_conversions', 'target_share', 'air_yards_share',
    'fantasy_points', 'fantasy_points_ppr'
]

WRHeader = [
    'player_id', 'player_display_name', 'position', 'recent_team', 'season', 'week',
    'targets', 'receptions', 'receiving_yards', 'receiving_tds',
    'receiving_air_yards', 'receiving_yards_after_catch', 'receiving_first_downs',
    'receiving_epa', 'receiving_2pt_conversions', 'target_share', 'air_yards_share',
    'wopr', 'racr', 'carries', 'rushing_yards', 'rushing_tds',
    'fantasy_points', 'fantasy_points_ppr'
]