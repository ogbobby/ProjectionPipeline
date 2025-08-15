import nfl_data_py as nfl
import pandas as pd
import sys
import os
from headers import QBHeader,RBHeader,WRHeader
# Get the absolute path to the directory containing your module
module_dir = os.path.abspath('/home/ogbobby/Documents/NFLPY/') 

# Add the directory to sys.path
sys.path.append(module_dir) 

def GetQBData():
    QBpbp3yrs = nfl.import_weekly_data([2021,2022,2023,2024], columns=QBHeader, downcast=False)
    QBpbp = QBpbp3yrs.query("position == 'QB'")
    passingNGS = nfl.import_ngs_data("passing", [2021,2022,2023,2024])
    qbngs = passingNGS[['season' , 'week', 'player_display_name' , 'avg_time_to_throw' , 'avg_completed_air_yards' , 'avg_intended_air_yards' , 'avg_air_yards_differential' , 'aggressiveness' ,
        'max_completed_air_distance' , 'avg_air_yards_to_sticks' , 'attempts' , 'pass_yards' , 'pass_touchdowns' , 'interceptions' , 'passer_rating' , 
        'completions' , 'completion_percentage' , 'expected_completion_percentage' , 'completion_percentage_above_expectation' , 'avg_air_distance' ,
        'max_air_distance']]
    combinedQB = pd.merge(QBpbp, qbngs, how='outer')
    depthcharts2024 = nfl.import_depth_charts([2024])
    activeOFF = depthcharts2024.query("formation == 'Offense'")
    activePlayerID = activeOFF[['gsis_id']]
    finalQB = combinedQB[combinedQB['player_id'].isin(activePlayerID['gsis_id'].values)]
    finalQB=finalQB.dropna()
    #print(finalQB.head)
    return finalQB

def GetRBData():
    RBpbp3yrs = nfl.import_weekly_data([2021,2022,2023,2024], columns=RBHeader, downcast=False)
    RBpbp = RBpbp3yrs.query("position == 'RB'")
    rushingNGS = nfl.import_ngs_data("rushing", [2021,2022,2023,2024])
    rbngs = rushingNGS[['week', 'player_display_name' , 'efficiency' , 'percent_attempts_gte_eight_defenders' , 'avg_time_to_los' , 'rush_attempts' , 'rush_yards' , 'avg_rush_yards' ,
        'rush_touchdowns']]
    combinedRB = pd.merge(RBpbp, rbngs, on=['player_display_name', 'week'], how='outer')
    depthcharts2024 = nfl.import_depth_charts([2024])
    activeOFF = depthcharts2024.query("formation == 'Offense'")
    activePlayerID = activeOFF[['gsis_id']]
    finalRB = combinedRB[combinedRB['player_id'].isin(activePlayerID['gsis_id'].values)]
    finalRB=finalRB.dropna()
    #print(finalRB.head)
    return finalRB

def GetWRData():
    WRpbp3yrs = nfl.import_weekly_data([2021,2022,2023,2024], columns=WRHeader, downcast=False)
    WRpbp = WRpbp3yrs.query("position == 'WR'")
    receivingNGS = nfl.import_ngs_data("receiving", [2021,2022,2023,2024])
    wrngs = receivingNGS[['player_display_name' , 'avg_cushion' , 'avg_separation' , 'avg_intended_air_yards' , 'percent_share_of_intended_air_yards' , 'receptions' , 'targets' , 'catch_percentage' ,
        'yards' , 'rec_touchdowns' , 'avg_yac' , 'avg_expected_yac' , 'avg_yac_above_expectation']]
    combinedWR = pd.merge(WRpbp, wrngs, how='outer')
    depthcharts2024 = nfl.import_depth_charts([2024])
    activeOFF = depthcharts2024.query("formation == 'Offense'")
    activePlayerID = activeOFF[['gsis_id']]
    finalWR = combinedWR[combinedWR['player_id'].isin(activePlayerID['gsis_id'].values)]
    finalWR=finalWR.dropna()
    #print(finalWR.head)
    return finalWR

def GetTEData():
    WRpbp3yrs = nfl.import_weekly_data([2021,2022,2023,2024], columns=WRHeader, downcast=False)
    TEpbp = WRpbp3yrs.query("position == 'TE'")
    receivingNGS = nfl.import_ngs_data("receiving", [2021,2022,2023,2024])
    wrngs = receivingNGS[['player_display_name' , 'avg_cushion' , 'avg_separation' , 'avg_intended_air_yards' , 'percent_share_of_intended_air_yards' , 'receptions' , 'targets' , 'catch_percentage' ,
        'yards' , 'rec_touchdowns' , 'avg_yac' , 'avg_expected_yac' , 'avg_yac_above_expectation']]
    combinedTE = pd.merge(TEpbp, wrngs, how='outer')
    depthcharts2024 = nfl.import_depth_charts([2024])
    activeOFF = depthcharts2024.query("formation == 'Offense'")
    activePlayerID = activeOFF[['gsis_id']]
    finalTE = combinedTE[combinedTE['player_id'].isin(activePlayerID['gsis_id'].values)]
    finalTE=finalTE.dropna()
    #print(finalTE.head)
    return finalTE

def GetDepthCharts():
    #nfl.import_seasonal_rosters([2025])
    teamDepthCharts = nfl.import_seasonal_rosters([2025])
    return teamDepthCharts
